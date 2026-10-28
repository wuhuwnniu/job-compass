param([switch]$SkipInstall)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath=Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create a Python 3.12 virtual environment at .venv first.' }
if (-not $SkipInstall) {
    & $pythonPath -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'yolo11n.pt'))) {
    & $pythonPath -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed.' }
}
& $pythonPath -m PyInstaller --noconfirm --clean packaging/StreetObservatory.spec
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
$env:STREET_DATA_DIR=Join-Path $projectRoot 'test-output\packaged-self-test'
$resultPath=Join-Path $projectRoot 'test-output\packaged-self-test.json'
$appPath=Join-Path $projectRoot 'dist\StreetObservatory\StreetObservatory.exe'
$testProcess=Start-Process -FilePath $appPath -ArgumentList @('--self-test','--result',('"'+$resultPath+'"')) -PassThru -WindowStyle Hidden -Wait
if ($testProcess.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $resultPath)) { throw 'Packaged application self-test failed.' }
$testResult=Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
if (-not $testResult.ok) { throw 'Packaged application self-test did not pass.' }
Remove-Item Env:STREET_DATA_DIR
$releaseDir=Join-Path $projectRoot 'release'
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'packaging\START_HERE.txt') -Destination (Join-Path $projectRoot 'dist\StreetObservatory\START_HERE.txt')
$archivePath=Join-Path $releaseDir 'StreetObservatory-0.2.0-windows-x64.zip'
& $pythonPath -c "import shutil; shutil.make_archive('release/StreetObservatory-0.2.0-windows-x64','zip','dist','StreetObservatory')"
if ($LASTEXITCODE -ne 0) { throw 'Archive creation failed.' }
Get-FileHash -LiteralPath $archivePath -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLower())  StreetObservatory-0.2.0-windows-x64.zip" } | Set-Content -LiteralPath (Join-Path $releaseDir 'SHA256SUMS.txt') -Encoding ascii
Write-Output "Created $archivePath"
