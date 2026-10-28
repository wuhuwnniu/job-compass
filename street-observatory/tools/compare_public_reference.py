"""Compare the first 120s crossing totals against the dataset's approximate body boxes.

This is NOT an accuracy metric: annotation body boxes are approximate, and errors
can cancel when comparing only counts. No claim about precision/recall is made.
"""
import csv
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import app
from analyzer import CrossingCounter

out=ROOT/'test-output'/'oxford-five-minutes'
pid=json.loads((out/'project.json').read_text('utf-8'))['project_id']
with zipfile.ZipFile(ROOT/'data'/'samples'/'oxford-town-centre'/'source.zip') as z:
    rows=list(csv.reader(z.read('TownCentre-groundtruth.top').decode().splitlines()))
counter=CrossingCounter([[.05,.68],[.95,.68]],[0,0,1,1])
events=[]
for row in sorted(rows,key=lambda r:int(r[1])):
    sec=int(row[1])/25
    if sec>=120:break
    if int(row[3])!=1:continue
    point=((float(row[8])+float(row[10]))/2/1920,float(row[11])/1080)
    direction=counter.feed(int(row[0]),point,sec)
    if direction:events.append({'sec':round(sec,2),'direction':direction})
with app.conn() as c:
    actual=[dict(r) for r in c.execute('SELECT sec,direction FROM events WHERE project_id=? AND sec<120 ORDER BY sec',(pid,))]
def aggregate(rows):
    return {'total':len(rows),'a':sum(e['direction']=='A' for e in rows),'b':sum(e['direction']=='B' for e in rows)}
comparison={'window_seconds':120,'automatic':aggregate(actual),'reference':aggregate(events),
            'annotation_last_frame':max(int(r[1]) for r in rows),
            'note':'Reference uses approximate body-box feet from the dataset annotations; this is a diagnostic count comparison, not a measured accuracy score. False positives and misses can cancel.'}
(out/'reference-check.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(comparison),flush=True)
