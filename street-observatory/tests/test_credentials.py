"""Use two independent browser cookies and synthetic keys; never call real DeepSeek."""
import http.client
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from credentials import CURRENT_PROFILE,crypt

@unittest.skipUnless(os.name=='nt','Windows DPAPI tests')
class CredentialTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.old_data,cls.old_db,cls.old_port=app.DATA,app.DB,app.PORT
        app.DATA=Path(cls.temp.name);app.DB=app.DATA/'test.db';app.init()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);app.PORT=cls.server.server_port
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close()
        app.DATA,app.DB,app.PORT=cls.old_data,cls.old_db,cls.old_port
        cls.temp.cleanup()
    def setUp(self):self.cookies={}
    def request(self,profile,method,path,body=None,origin=None):
        c=http.client.HTTPConnection('127.0.0.1',app.PORT,timeout=10)
        headers={'Content-Type':'application/json'}
        if profile in self.cookies:headers['Cookie']=self.cookies[profile]
        if origin:headers['Origin']=origin
        c.request(method,path,json.dumps(body).encode() if body is not None else None,headers)
        r=c.getresponse();cookie=r.getheader('Set-Cookie')
        if cookie:
            self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=Strict',cookie)
            self.cookies[profile]=cookie.split(';')[0]
        data=r.read();status=r.status;c.close()
        return status,json.loads(data)
    def test_encryption_and_profile_isolation(self):
        key_a='sk-test-profile-a-not-a-real-key-1111';key_b='sk-test-profile-b-not-a-real-key-2222'
        status,a=self.request('a','PUT','/api/ai/settings',{'api_key':key_a,'model':'deepseek-flash'})
        self.assertEqual(status,200);self.assertTrue(a['configured']);self.assertNotIn(key_a,json.dumps(a))
        self.assertFalse(self.request('b','GET','/api/ai/settings')[1]['configured'])
        status,b=self.request('b','PUT','/api/ai/settings',{'api_key':key_b,'model':'deepseek-v4-pro'})
        self.assertEqual(status,200);self.assertEqual(b['key_hint'],'••••2222')
        self.assertEqual(self.request('a','GET','/api/ai/settings')[1]['model'],'deepseek-flash')
        with app.conn() as c:
            rows=c.execute('SELECT encrypted_key,owner_hash FROM ai_credentials').fetchall()
        self.assertTrue(rows)
        for row in rows:
            blob=bytes(row['encrypted_key'])
            self.assertNotIn(key_a.encode(),blob);self.assertNotIn(key_b.encode(),blob)
            self.assertTrue(crypt(blob,row['owner_hash'],True).decode().startswith('sk-test-'))
        self.assertFalse(self.request('a','DELETE','/api/ai/settings')[1]['configured'])
        self.assertTrue(self.request('b','GET','/api/ai/settings')[1]['configured'])
    def test_env_key_not_shared_with_browser(self):
        with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'sk-test-env-not-a-real-key-3333'}):
            self.assertFalse(self.request('fresh','GET','/api/health')[1]['ai']['configured'])
    def test_invalid_and_cross_origin_are_rejected(self):
        self.assertEqual(self.request('a','PUT','/api/ai/settings',{'api_key':'bad','model':'deepseek-flash'})[0],400)
        self.assertEqual(self.request('a','PUT','/api/ai/settings',{'api_key':'sk-test-not-real-0000'},origin='https://other.example')[0],400)
    def test_model_update_keeps_saved_key(self):
        self.request('a','PUT','/api/ai/settings',{'api_key':'sk-test-local-not-real-4444','model':'deepseek-flash'})
        status,result=self.request('a','PUT','/api/ai/settings',{'api_key':'','model':'deepseek-v4-pro'})
        self.assertEqual(status,200);self.assertEqual(result['key_hint'],'••••4444')
        self.assertEqual(result['model'],'deepseek-v4-pro')
    def test_connection_uses_current_profile(self):
        self.request('a','PUT','/api/ai/settings',{'api_key':'sk-test-only-a-not-real-5555','model':'deepseek-flash'})
        self.request('b','PUT','/api/ai/settings',{'api_key':'sk-test-only-b-not-real-6666','model':'deepseek-flash'})
        captured=[]
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return json.dumps({'choices':[{'message':{'content':'连接成功'}}],'usage':{'prompt_tokens':1,'completion_tokens':1}}).encode()
        def fake_open(request,**kwargs):captured.append(request.get_header('Authorization'));return Response()
        with patch('ai_providers.urlopen',side_effect=fake_open):
            self.assertEqual(self.request('a','POST','/api/ai/test',{})[0],200)
            self.assertEqual(self.request('b','POST','/api/ai/test',{})[0],200)
        self.assertEqual(captured,['Bearer sk-test-only-a-not-real-5555','Bearer sk-test-only-b-not-real-6666'])

if __name__=='__main__':unittest.main(verbosity=2)
