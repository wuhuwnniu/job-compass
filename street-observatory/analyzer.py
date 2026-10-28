"""Real person detection + per-crossing event counting. No identity deduplication."""
import math
import json
import os
import time
from pathlib import Path

def signed_distance(point,a,b):
    length=math.hypot(b[0]-a[0],b[1]-a[1])
    return ((b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0]))/length

def crosses_segment(p,q,a,b):
    def cross(x,y):return x[0]*y[1]-x[1]*y[0]
    r=(q[0]-p[0],q[1]-p[1]); s=(b[0]-a[0],b[1]-a[1])
    den=cross(r,s)
    if abs(den)<1e-9:return False
    ap=(a[0]-p[0],a[1]-p[1])
    t,u=cross(ap,s)/den,cross(ap,r)/den
    return 0<=t<=1 and 0<=u<=1

class CrossingCounter:
    def __init__(self,line,roi,deadband=0.008,cooldown=1.0):
        self.a,self.b=line; self.roi=roi; self.deadband=deadband; self.cooldown=cooldown; self.tracks={}
    def feed(self,track,point,sec):
        x,y=point; x1,y1,x2,y2=self.roi
        if not (x1<=x<=x2 and y1<=y<=y2):return None
        d=signed_distance(point,self.a,self.b)
        if abs(d)<self.deadband:return None
        side=1 if d>0 else -1
        old=self.tracks.get(track)
        event=None
        if old and old['side']!=side and sec-old['seen']<2.5:
            if crosses_segment(old['point'],point,self.a,self.b) and sec-old['last']>=self.cooldown:
                event='A' if side>0 else 'B'
                old['last']=sec
        self.tracks[track]={'side':side,'point':point,'seen':sec,'last':old['last'] if old else -999}
        return event
    def prune(self,sec):
        self.tracks={k:v for k,v in self.tracks.items() if sec-v['seen']<10}

def analyze(pid,stop):
    from app import conn,project,update,RUNNING,TASK_LOCK,ROOT
    import cv2
    from ultralytics import YOLO
    from attributes import get_attribute_provider
    cap=None
    try:
        p=project(pid)
        with conn() as c:
            path=c.execute('SELECT video FROM projects WHERE id=?',(pid,)).fetchone()[0]
            c.execute('DELETE FROM events WHERE project_id=?',(pid,))
        weights=os.environ.get('YOLO_MODEL','yolo11n.pt')
        model=YOLO(str(ROOT/weights) if (ROOT/weights).exists() else weights)
        cap=cv2.VideoCapture(path)
        fps=cap.get(cv2.CAP_PROP_FPS); total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps<=0 or total<=0:raise ValueError('无法读取视频帧率')
        counter=CrossingCounter(p['settings']['line'],p['settings'].get('roi',[0,0,1,1]))
        attributes=get_attribute_provider()
        pending=[]; frame_index=0; last_commit=time.monotonic(); started=time.monotonic()
        while not stop.is_set():
            ok,frame=cap.read()
            if not ok:break
            h,w=frame.shape[:2]; sec=frame_index/fps
            results=model.track(frame,persist=True,classes=[0],tracker='bytetrack.yaml',conf=0.3,imgsz=640,verbose=False)
            boxes=results[0].boxes
            if boxes is not None and boxes.id is not None:
                for bbox,track in zip(boxes.xyxy.cpu().tolist(),boxes.id.int().cpu().tolist()):
                    # Use feet anchor, appropriate for a line drawn on street ground.
                    point=((bbox[0]+bbox[2])/2/w,bbox[3]/h)
                    direction=counter.feed(track,point,sec)
                    if direction:
                        x1,y1,x2,y2=map(int,bbox)
                        crop=frame[max(0,y1):min(h,y2),max(0,x1):min(w,x2)]
                        attrs=attributes.classify(crop)
                        pending.append((pid,round(sec,3),direction,track,json.dumps(attrs)))
            frame_index+=1
            if time.monotonic()-last_commit>=1.5:
                with conn() as c:
                    c.executemany('INSERT INTO events(project_id,sec,direction,track_id,attrs) VALUES(?,?,?,?,?)',pending)
                pending=[]; counter.prune(sec)
                speed=frame_index/max(0.01,time.monotonic()-started)
                update(pid,progress=min(99.9,frame_index/total*100),message=f'已处理 {sec:.0f} 秒 / {total/fps:.0f} 秒 · {speed:.1f} 帧/秒')
                last_commit=time.monotonic()
        with conn() as c:c.executemany('INSERT INTO events(project_id,sec,direction,track_id,attrs) VALUES(?,?,?,?,?)',pending)
        if stop.is_set():
            update(pid,status='interrupted',progress=frame_index/total*100,message='分析已停止。重新分析会从头计算并替换现有事件。')
        elif frame_index<total*0.99:
            update(pid,status='failed',progress=frame_index/total*100,message='视频提前解码结束，结果不完整，请检查文件。')
        else:
            update(pid,status='completed',progress=100,message='分析完成。建议抽样复核计数，再生成报告。')
    except Exception as e:
        # Avoid exposing credential-bearing URLs if a model download fails.
        message='模型或视频处理失败（'+type(e).__name__+'）。检查依赖、模型权重和视频格式后重试。'
        update(pid,status='failed',message=message)
    finally:
        if cap is not None:cap.release()
        with TASK_LOCK:RUNNING.pop(pid,None)
