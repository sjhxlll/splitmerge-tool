@echo off
setlocal

where python >nul 2>nul
if errorlevel 1 (
  echo Python is not found in PATH.
  echo Install Python 3.10+ first.
  exit /b 1
)

python -m pip install --upgrade pip
python -m pip install pyinstaller

pyinstaller --noconfirm --clean --onefile --windowed --name splitmerge-desktop splitmerge_desktop.py

if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

echo Build success.
echo EXE path: dist\splitmerge-desktop.exe
endlocal