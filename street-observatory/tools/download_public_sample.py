"""Download a public Oxford Town Centre mirror for local evaluation only."""
from pathlib import Path
import json
import time
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'data'/'samples'/'oxford-town-centre'
FOLDER.mkdir(parents=True,exist_ok=True)
SOURCE='https://www.kaggle.com/datasets/almightyj/oxford-town-centre'
DOWNLOAD='https://www.kaggle.com/api/v1/datasets/download/almightyj/oxford-town-centre'
archive=FOLDER/'source.zip'
if not archive.exists():
    temp=FOLDER/'source.zip.part'
    request=urllib.request.Request(DOWNLOAD,headers={'User-Agent':'StreetObservatory/0.1 local evaluation'})
    with urllib.request.urlopen(request,timeout=60) as response,temp.open('wb') as f:
        total=int(response.headers.get('Content-Length','0'));received=0;last=0
        while chunk:=response.read(1024*1024):
            f.write(chunk);received+=len(chunk)
            if time.monotonic()-last>12:
                print(json.dumps({'downloaded_mb':round(received/1024**2,1),'total_mb':round(total/1024**2,1)}),flush=True)
                last=time.monotonic()
    temp.replace(archive)
with zipfile.ZipFile(archive) as z:
    print(json.dumps({'archive_files':z.namelist()},ensure_ascii=False),flush=True)
    videos=[i for i in z.infolist() if Path(i.filename).suffix.lower() in ('.mp4','.avi','.mov','.mkv')]
    if not videos:raise ValueError('No video in public archive')
    entry=max(videos,key=lambda i:i.file_size)
    target=FOLDER/('source'+Path(entry.filename).suffix.lower())
    if not target.exists():
        with z.open(entry) as inp,target.open('wb') as out:
            while chunk:=inp.read(1024*1024):out.write(chunk)
metadata={'source_page':SOURCE,'download_endpoint':DOWNLOAD,'archive_member':entry.filename,
          'retrieved_date':'2026-10-27','description':'Oxford Town Centre fixed-camera pedestrian video, unofficial public mirror.',
          'attribution':'Ben Benfold and Ian Reid. Stable multi-target tracking in real-time surveillance video. CVPR 2011.',
          'license_note':'Mirror lists Other (specified in description), disclaims ownership and refers to original authors. Local technical evaluation only; no redistribution or commercial clearance asserted.'}
(FOLDER/'source.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'saved_video':str(target),'bytes':target.stat().st_size}),flush=True)
