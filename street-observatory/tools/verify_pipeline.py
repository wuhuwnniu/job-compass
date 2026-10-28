"""Exercise the real model through the running API using an explicitly synthetic clip."""
import http.client
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]

def request(method,path,body=None,raw=False,headers=None):
    c=http.client.HTTPConnection('127.0.0.1',8765,timeout=120)
    data=body if raw else json.dumps(body or {}).encode() if method!='GET' else None
    c.request(method,path,data,headers or {'Content-Type':'application/json'})
    r=c.getresponse();content=r.read();status=r.status;c.close()
    if status>=400:raise RuntimeError(content.decode())
    return content if raw and method=='GET' else json.loads(content)

projects=request('GET','/api/projects')
project=next((p for p in projects if p['name']=='验收测试 · 合成短视频'),None)
if project is None:project=request('POST','/api/projects',{'name':'验收测试 · 合成短视频','meta':{'拍摄方式':'固定机位','街道位置':'软件验收用，不代表真实街道'}})
pid=project['id'];base=f'/api/projects/{pid}'
clip=ROOT/'test-output'/'synthetic.mp4'
request('PUT',base+'/video',clip.read_bytes(),True,{'Content-Type':'application/octet-stream','X-Video-Extension':'.mp4'})
request('PATCH',base,{'settings':{'line':[[.03,.78],[.97,.78]],'roi':[0,0,1,1]}})
request('POST',base+'/analyze')
deadline=time.monotonic()+180
while time.monotonic()<deadline:
    p=request('GET',base)
    if p['status']!='running':break
    time.sleep(1)
assert p['status']=='completed',p
s=request('GET',base+'/stats')
assert s['total']>0,s
assert s['a']+s['b']==s['total']
assert s['effective_seconds']==8,s
events=request('GET',base+'/events')
assert len(events['items'])==s['total']
pdf=request('GET',base+'/pdf',raw=True)
assert pdf.startswith(b'%PDF')
(ROOT/'test-output'/'pipeline-report.pdf').write_bytes(pdf)
csv=request('GET',base+'/csv',raw=True)
assert csv.startswith(b'\xef\xbb\xbf')
(ROOT/'test-output'/'pipeline-check.json').write_text(json.dumps({'status':'passed','test':'synthetic moving-image pipeline, not accuracy validation','project_id':pid,'stats':s},ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'status':'passed','duration':8,'crossings':s['total'],'a':s['a'],'b':s['b'],'pdf_bytes':len(pdf)},ensure_ascii=False))
