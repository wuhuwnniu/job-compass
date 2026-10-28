"""Windows desktop entry point. All mutable data lives outside the installed app."""
import argparse
import ctypes
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import sys
import threading

VERSION='0.2.0'

def main():
    multiprocessing.freeze_support()
    parser=argparse.ArgumentParser()
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--result')
    args=parser.parse_args()
    user_data=Path(os.environ.get('STREET_DATA_DIR',str(Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'StreetObservatory')))
    user_data.mkdir(parents=True,exist_ok=True)
    os.environ['STREET_DATA_DIR']=str(user_data)
    os.environ.setdefault('YOLO_CONFIG_DIR',str(user_data/'model-config'))
    os.environ.setdefault('MPLCONFIGDIR',str(user_data/'matplotlib'))
    log=(user_data/'desktop.log').open('a',encoding='utf-8',buffering=1)
    if sys.stdout is None:sys.stdout=log
    if sys.stderr is None:sys.stderr=log
    import app
    if args.self_test:
        app.init()
        import cv2
        import numpy as np
        from ultralytics import YOLO
        model=YOLO(str(app.ROOT/'yolo11n.pt'))
        model.predict(np.zeros((320,320,3),dtype=np.uint8),verbose=False)
        import reportlab.pdfgen.canvas
        import webview
        result={'ok':True,'version':VERSION,'frozen':bool(getattr(sys,'frozen',False)),
                'detector_loaded':True,'opencv':cv2.__version__,'desktop_imported':True,
                'html_exists':(app.ROOT/'web'/'index.html').is_file()}
        if args.result:Path(args.result).write_text(json.dumps(result,indent=2),'utf-8')
        return
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p]
    kernel.CreateMutexW.restype=ctypes.c_void_p
    mutex_name='Local\\StreetObservatory-'+hashlib.sha256(str(user_data).encode()).hexdigest()[:20]
    mutex=kernel.CreateMutexW(None,False,mutex_name)
    if ctypes.get_last_error()==183:
        ctypes.windll.user32.MessageBoxW(None,'街道观察已经运行，请切换到已有窗口。','街道观察',0x40)
        if mutex:kernel.CloseHandle(ctypes.c_void_p(mutex))
        return
    app.init()
    server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
    app.PORT=server.server_port
    threading.Thread(target=server.serve_forever,daemon=True).start()
    import webview
    try:
        webview.create_window('街道观察 · Street Observatory',f'http://127.0.0.1:{app.PORT}/',
                              width=1280,height=850,min_size=(800,600),background_color='#f7f8f5',text_select=True)
        webview.start(gui='edgechromium',private_mode=False,storage_path=str(user_data/'webview'))
    finally:
        for event in list(app.RUNNING.values()):event.set()
        server.shutdown();server.server_close()
        if mutex:kernel.CloseHandle(ctypes.c_void_p(mutex))

if __name__=='__main__':
    try:main()
    except Exception:
        import traceback
        traceback.print_exc()
        if '--self-test' not in sys.argv:
            ctypes.windll.user32.MessageBoxW(None,'启动失败，请查看本用户 StreetObservatory 文件夹中的 desktop.log。若缺少 WebView2，请安装 Microsoft Edge WebView2 Runtime。','街道观察',0x10)
        sys.exit(1)
