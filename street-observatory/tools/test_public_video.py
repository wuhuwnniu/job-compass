"""Import a continuous 5-minute public sample and exercise the real app API."""
import argparse
import http.client
import json
from pathlib import Path
import subprocess
import time
import cv2
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'data'/'samples'/'oxford-town-centre'
OUT=ROOT/'test-output'/'oxford-five-minutes'
OUT.mkdir(parents=True,exist_ok=True)
CLIP=FOLDER/'oxford-5min.mp4'
NAME='公开样片 · 牛津步行街 · 5分钟'

def inspect(path):
    cap=cv2.VideoCapture(str(path))
    info={'width':int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),'height':int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
          'fps':cap.get(cv2.CAP_PROP_FPS),'frames':int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}
    info['seconds']=info['frames']/info['fps'] if info['fps'] else 0
    cap.release();return info

def prepare():
    source=next(p for p in FOLDER.glob('source.*') if p.suffix.lower() in ('.mp4','.avi','.mov','.mkv'))
    before=inspect(source)
    print(json.dumps({'source_info':before}),flush=True)
    if before['seconds']<299.9:raise ValueError('Public source is shorter than 5 minutes; no looping allowed')
    if not CLIP.exists():
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-y',
                        '-i',str(source),'-t','300','-vf','scale=1280:-2','-c:v','libx264',
                        '-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(CLIP)],check=True)
    info=inspect(CLIP)
    if abs(info['seconds']-300)>.1:raise ValueError('The prepared sample must be a continuous 300-second clip')
    cap=cv2.VideoCapture(str(CLIP))
    for sec in (0,60,150):
        cap.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
        ok,frame=cap.read()
        if ok:cv2.imwrite(str(OUT/f'frame-{sec}.jpg'),frame)
    cap.release()
    manifest=json.loads((FOLDER/'source.json').read_text('utf-8'))
    manifest.update({'source_info':before,'clip_info':info,'clip_start_seconds':0,'clip_end_seconds':300,
                     'transform':'First continuous 300 seconds; resize to 1280px width; normal speed, original frame rate; audio omitted.'})
    (OUT/'source.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'clip':str(CLIP),'clip_info':info}),flush=True)

def request(method,path,body=None,binary=False):
    c=http.client.HTTPConnection('127.0.0.1',8765,timeout=120)
    payload=json.dumps(body or {},ensure_ascii=False).encode() if method not in ('GET','DELETE') else None
    c.request(method,path,payload,{'Content-Type':'application/json'})
    r=c.getresponse();content=r.read();status=r.status;c.close()
    if status>=400:raise RuntimeError(content.decode())
    return content if binary else json.loads(content)

def run():
    info=inspect(CLIP)
    if abs(info['seconds']-300)>.1:raise ValueError('Run prepare first')
    projects=request('GET','/api/projects')
    p=next((p for p in projects if p['name']==NAME),None)
    if p is None:
        p=request('POST','/api/projects',{'name':NAME,'meta':{
            '街道位置':'英国牛津 Town Centre（公开参考素材）','拍摄方式':'固定机位',
            '素材来源':'https://www.kaggle.com/datasets/almightyj/oxford-town-centre',
            '用途':'真实视频处理效果测试，不代表用户候选街道；无属性模型或AI生成结果。',
            '测试片段':'原素材 00:00—05:00，连续片段，正常速度'}})
    pid=p['id'];base=f'/api/projects/{pid}'
    if not p.get('video_url'):
        c=http.client.HTTPConnection('127.0.0.1',8765,timeout=120)
        with CLIP.open('rb') as f:
            c.request('PUT',base+'/video',f,{'Content-Type':'application/octet-stream','Content-Length':str(CLIP.stat().st_size),'X-Video-Extension':'.mp4'})
            r=c.getresponse();body=r.read()
            if r.status!=200:raise RuntimeError(body.decode())
        c.close()
        request('PATCH',base,{'settings':{'line':[[.05,.68],[.95,.68]],'roi':[0,0,1,1]}})
    if p['status']!='completed' and p['status']!='running':request('POST',base+'/analyze')
    (OUT/'project.json').write_text(json.dumps({'project_id':pid,'url':'http://127.0.0.1:8765','name':NAME},ensure_ascii=False,indent=2),'utf-8')
    started=time.monotonic();last=-20
    while True:
        p=request('GET',base)
        if time.monotonic()-last>=15:
            print(json.dumps({'status':p['status'],'percent':round(p['progress'],1),'message':p['message']},ensure_ascii=False),flush=True)
            last=time.monotonic()
        if p['status']!='running':break
        time.sleep(2)
    if p['status']!='completed':raise RuntimeError(p['message'])
    s=request('GET',base+'/stats')
    (OUT/'stats.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),'utf-8')
    (OUT/'events.csv').write_bytes(request('GET',base+'/csv',binary=True))
    summary={'project_id':pid,'duration_seconds':p['duration'],'total':s['total'],'a':s['a'],'b':s['b'],
             'per_minute':s['per_minute'],'processing_wall_seconds':round(time.monotonic()-started,1),
             'note':'Automatic crossing counts, not unique people. No manual ground-truth accuracy claim. Attributes and live AI not tested.'}
    (OUT/'result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);args=parser.parse_args()
    prepare() if args.action=='prepare' else run()
