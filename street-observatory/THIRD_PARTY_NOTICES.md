# Third-party software and model notices

Street Observatory 0.2.0 uses the following projects. Their own license texts and
notices apply independently of this application's license.

- Ultralytics / YOLO11n weights: AGPL-3.0, with a separate vendor commercial option. https://github.com/ultralytics/ultralytics and https://github.com/ultralytics/assets
- OpenCV: Apache-2.0. https://github.com/opencv/opencv
- PyTorch and torchvision: BSD-style licenses. https://github.com/pytorch/pytorch and https://github.com/pytorch/vision
- pywebview: BSD-3-Clause. https://github.com/r0x0r/pywebview
- Python.NET: MIT. https://github.com/pythonnet/pythonnet
- ReportLab: BSD-style license. https://www.reportlab.com/
- NumPy and SciPy: BSD-3-Clause. https://numpy.org/ and https://scipy.org/
- lap: BSD-2-Clause. https://github.com/gatagat/lap
- PyInstaller: GPL-2.0 with its bootloader distribution exception. https://pyinstaller.org/

Installed distributions may include additional transitive dependencies and notices.
The build includes their available distribution metadata and license files; see
`requirements-lock.txt` for the tested environment. CPU model weights are included
for offline counting. No DeepSeek API key or test footage is included.

DeepSeek is an optional external API service. Users provide their own keys and
are billed by DeepSeek under their own service terms. Microsoft Edge WebView2
Runtime is a system prerequisite and is not redistributed in this package.

Public Oxford test footage is excluded from source and binary release archives.
