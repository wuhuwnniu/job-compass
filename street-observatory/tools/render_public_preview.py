"""Create diagnostic stills for the downloaded sample, with approximate head-region blur.

These stills show detections only; detected targets in one frame are not crossing counts.
"""
import os
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('YOLO_CONFIG_DIR',str(ROOT/'data'/'model-config'))
os.environ.setdefault('YOLO_AUTOINSTALL','false')
import cv2
from ultralytics import YOLO

folder=ROOT/'test-output'/'oxford-five-minutes'
source=ROOT/'data'/'samples'/'oxford-town-centre'/'oxford-5min.mp4'
model=YOLO(str(ROOT/'yolo11n.pt'))
cap=cv2.VideoCapture(str(source))
out=[]
for sec in (10,120,240):
    cap.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
    ok,frame=cap.read()
    if not ok:raise ValueError('Cannot decode diagnostic frame')
    result=model.predict(frame,classes=[0],conf=.3,imgsz=640,verbose=False)[0]
    h,w=frame.shape[:2]
    boxes=result.boxes.xyxy.cpu().tolist()
    # Blur the upper quarter of each detected person before drawing diagnostics.
    # Approximate anonymization of detected people only; no identity analysis.
    for x1,y1,x2,y2 in boxes:
        x1=max(0,int(x1));x2=min(w,int(x2));y1=max(0,int(y1));head_end=min(h,int(y1+(y2-y1)*.25))
        if x2>x1 and head_end>y1:
            crop=frame[y1:head_end,x1:x2]
            small=cv2.resize(crop,(max(1,crop.shape[1]//12),max(1,crop.shape[0]//12)))
            frame[y1:head_end,x1:x2]=cv2.resize(small,(crop.shape[1],crop.shape[0]),interpolation=cv2.INTER_NEAREST)
    for x1,y1,x2,y2 in boxes:
        cv2.rectangle(frame,(int(x1),int(y1)),(int(x2),int(y2)),(110,220,150),1)
        cv2.circle(frame,(int((x1+x2)/2),int(y2)),3,(80,180,255),-1)
    cv2.line(frame,(int(.05*w),int(.68*h)),(int(.95*w),int(.68*h)),(80,220,240),2)
    cv2.putText(frame,'B',(int(.87*w),int(.65*h)),cv2.FONT_HERSHEY_SIMPLEX,.7,(80,220,240),2)
    cv2.putText(frame,'A',(int(.87*w),int(.73*h)),cv2.FONT_HERSHEY_SIMPLEX,.7,(110,220,150),2)
    cv2.rectangle(frame,(0,0),(w,58),(30,45,35),-1)
    cv2.putText(frame,f'Oxford public sample | {sec//60:02}:{sec%60:02} | detected in frame: {len(boxes)}',
                (20,26),cv2.FONT_HERSHEY_SIMPLEX,.65,(240,245,240),1,cv2.LINE_AA)
    cv2.putText(frame,'Yellow: counting line | Orange dots: feet anchors | Not unique visitors',
                (20,48),cv2.FONT_HERSHEY_SIMPLEX,.45,(190,210,190),1,cv2.LINE_AA)
    name=f'detection-{sec}.jpg';cv2.imwrite(str(folder/name),frame)
    out.append({'second':sec,'detections_in_frame':len(boxes),'file':name})
cap.release()
(folder/'diagnostic-frames.json').write_text(json.dumps(out,indent=2),'utf-8')
print(json.dumps(out),flush=True)
