# Build from the repository root: python -m PyInstaller packaging/StreetObservatory.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files,collect_submodules,copy_metadata
import torchvision

root=Path(SPECPATH).parent
datas=[(str(root/'web'),'web'),(str(root/'yolo11n.pt'),'.'),
       (str(root/'README.md'),'.'),(str(root/'THIRD_PARTY_NOTICES.md'),'.'),(str(root/'LICENSE'),'.')]
datas+=collect_data_files('ultralytics')
for package in ('ultralytics','torch','torchvision','lap','reportlab','pywebview'):
    datas+=copy_metadata(package)
hidden=['analyzer','attributes','credentials','ai_providers','cv2','lap','scipy.optimize','reportlab.pdfbase.cidfonts']
hidden+=collect_submodules('ultralytics.nn')+collect_submodules('ultralytics.trackers')
# Current torchvision loads the *_stable.pyd extensions through torch.ops;
# the stock hook only knows the older _C.pyd module name.
vision_dir=Path(torchvision.__file__).parent
vision_binaries=[(str(p),'torchvision') for p in vision_dir.glob('*.pyd')]
analysis=Analysis([str(root/'desktop.pyw')],pathex=[str(root)],binaries=vision_binaries,datas=datas,
    hiddenimports=hidden,hookspath=[],hooksconfig={},runtime_hooks=[],
    excludes=['tkinter','IPython','jupyter','pytest','PyQt5','PyQt6','PySide2','PySide6','tensorflow','tensorboard'],noarchive=False)
pyz=PYZ(analysis.pure)
exe=EXE(pyz,analysis.scripts,[],exclude_binaries=True,name='StreetObservatory',
    debug=False,bootloader_ignore_signals=False,strip=False,upx=False,console=False,
    version=str(root/'packaging'/'version.txt'))
collect=COLLECT(exe,analysis.binaries,analysis.datas,strip=False,upx=False,name='StreetObservatory')
