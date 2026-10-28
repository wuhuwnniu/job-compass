"""Regression checks use disposable DB and explicit test data, never production projects."""
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from analyzer import CrossingCounter

class CountingTest(unittest.TestCase):
    def test_return_crossing_counts_again(self):
        c=CrossingCounter([[.1,.5],[.9,.5]],[0,0,1,1])
        self.assertIsNone(c.feed(7,(.5,.3),0))
        self.assertEqual(c.feed(7,(.5,.7),1),'A')
        self.assertEqual(c.feed(7,(.5,.3),3),'B')
        self.assertEqual(c.feed(7,(.5,.7),5),'A')
    def test_jitter_segment_and_roi(self):
        c=CrossingCounter([[.2,.5],[.8,.5]],[0,0,1,1])
        c.feed(1,(.5,.48),0)
        self.assertIsNone(c.feed(1,(.5,.501),.1))
        self.assertIsNone(c.feed(1,(.5,.499),.2))
        self.assertEqual(c.feed(1,(.5,.52),1),'A')
        self.assertIsNone(c.feed(1,(.5,.48),1.1))
        c.feed(2,(.95,.3),0)
        self.assertIsNone(c.feed(2,(.95,.7),1))
        c=CrossingCounter([[.2,.5],[.8,.5]],[.1,.1,.9,.9])
        self.assertIsNone(c.feed(2,(.95,.7),2))
    def test_gap_cannot_create_crossing(self):
        c=CrossingCounter([[.1,.5],[.9,.5]],[0,0,1,1])
        c.feed(1,(.5,.3),0)
        self.assertIsNone(c.feed(1,(.5,.7),10))

class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.old_data,cls.old_db,cls.old_port=app.DATA,app.DB,app.PORT
        app.DATA=Path(cls.tmp.name);app.DB=app.DATA/'test.db';app.init()
        cls.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        app.PORT=cls.server.server_port
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close()
        app.DATA,app.DB,app.PORT=cls.old_data,cls.old_db,cls.old_port
        cls.tmp.cleanup()
    def request(self,method,path,body=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',app.PORT,timeout=10)
        data=json.dumps(body).encode() if body is not None else None
        c.request(method,path,data,{'Content-Type':'application/json',**(headers or {})})
        r=c.getresponse(); raw=r.read(); status=r.status;c.close()
        try:return status,json.loads(raw)
        except (json.JSONDecodeError,UnicodeDecodeError):return status,raw
    def make_project(self):
        status,p=self.request('POST','/api/projects',{'name':'验收测试街道','meta':{'拍摄方式':'固定机位'}})
        self.assertEqual(status,201);return p['id']
    def test_project_validation_and_origin(self):
        self.assertEqual(self.request('POST','/api/projects',{'name':''})[0],400)
        self.assertEqual(self.request('POST','/api/projects',{'name':'x'}, {'Origin':'https://unknown.example'})[0],400)
        pid=self.make_project()
        self.assertEqual(self.request('PATCH',f'/api/projects/{pid}',{'settings':{'line':[[.4,.4],[.4,.4]]}})[0],400)
        status,p=self.request('PATCH',f'/api/projects/{pid}',{'settings':{'line':[[.1,.5],[.9,.5]]}})
        self.assertEqual(status,200);self.assertEqual(p['settings']['roi'],[0,0,1,1])
        self.assertEqual(self.request('DELETE',f'/api/projects/{pid}')[0],200)
    def test_review_stats_and_csv(self):
        pid=self.make_project();app.update(pid,status='completed',duration=600,progress=100)
        with app.conn() as c:
            c.executemany('INSERT INTO events(project_id,sec,direction,track_id) VALUES(?,?,?,?)',[(pid,10,'A',1),(pid,20,'B',1),(pid,350,'A',2)])
            event=c.execute('SELECT id FROM events WHERE project_id=? ORDER BY id',(pid,)).fetchone()[0]
        status,s=self.request('GET',f'/api/projects/{pid}/stats')
        self.assertEqual(status,200);self.assertEqual(s['total'],3);self.assertEqual(len(s['bins5']),2)
        self.assertEqual(s['per_minute'],.3)
        self.assertEqual(self.request('PATCH',f'/api/projects/{pid}/events',{'id':event,'direction':'B','included':False})[0],200)
        s=app.stats(pid);self.assertEqual(s['total'],2);self.assertEqual(s['reviewed'],1)
        self.assertEqual(self.request('POST',f'/api/projects/{pid}/manual',{'sec':100,'direction':'A'})[0],200)
        self.assertEqual(app.stats(pid)['total'],3)
        status,raw=self.request('GET',f'/api/projects/{pid}/csv');self.assertEqual(status,200);self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
    def test_range_video(self):
        pid=self.make_project();folder=app.DATA/pid;folder.mkdir();f=folder/'video.mp4';f.write_bytes(b'0123456789')
        app.update(pid,video=str(f))
        status,raw=self.request('GET',f'/api/projects/{pid}/video',headers={'Range':'bytes=2-5'})
        self.assertEqual(status,206);self.assertEqual(raw,2345) # JSON parser reads the numeric bytes
        self.assertEqual(self.request('GET',f'/api/projects/{pid}/video',headers={'Range':'bytes=99-'})[0],416)
    def test_ai_config_report_and_revision(self):
        pid=self.make_project();app.update(pid,status='completed',progress=100,duration=100)
        with patch.dict(app.os.environ,{'DEEPSEEK_API_KEY':''}):
            self.assertEqual(self.request('POST',f'/api/projects/{pid}/report',{})[0],400)
        r={'summary':'尚无足够数据。','evidence_keys':['total'],'candidates':[], 'next_steps':['补拍工作日和周末。'],'limitations':['仅一个时段。']}
        with patch('app.call_ai',return_value=(json.dumps(r),{'prompt_tokens':10,'completion_tokens':20})):
            report=app.generate_report(pid)
            self.assertEqual(report['verified_statistics']['total'],0)
            self.assertEqual(app.project(pid)['report_revision'],app.project(pid)['revision'])
        app.update(pid,revision=app.project(pid)['revision']+1)
        self.assertNotEqual(app.project(pid)['report_revision'],app.project(pid)['revision'])
        with patch('app.call_ai',return_value=('{}',{})):
            with self.assertRaises(ValueError):app.generate_report(pid)
    def test_pdf_is_generated(self):
        pid=self.make_project();content=app.pdf_bytes(pid)
        self.assertTrue(content.startswith(b'%PDF'))
    def test_line_change_requires_new_analysis(self):
        pid=self.make_project();app.update(pid,status='completed',duration=100,progress=100)
        status,p=self.request('PATCH',f'/api/projects/{pid}',{'settings':{'line':[[.1,.5],[.9,.5]]}})
        self.assertEqual(status,200);self.assertEqual(p['status'],'ready')
        with self.assertRaises(ValueError):app.generate_report(pid)

if __name__=='__main__':unittest.main(verbosity=2)
