"""Create an explicitly synthetic moving-image clip for pipeline checks, not accuracy evaluation."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import cv2
import numpy as np
import ultralytics

out=ROOT/'test-output';out.mkdir(exist_ok=True)
image=cv2.imread(str(Path(ultralytics.__file__).parent/'assets'/'bus.jpg'))
image=cv2.resize(image,(450,600))
writer=cv2.VideoWriter(str(out/'synthetic.avi'),cv2.VideoWriter_fourcc(*'MJPG'),10,(450,720))
assert writer.isOpened()
for i in range(80):
    y=int(120*abs(1-i/40))
    frame=np.full((720,450,3),225,dtype=np.uint8)
    frame[y:y+600]=image
    cv2.putText(frame,'SYNTHETIC PIPELINE TEST',(8,24),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,0,0),1,cv2.LINE_AA)
    writer.write(frame)
writer.release()
print(out/'synthetic.avi')
