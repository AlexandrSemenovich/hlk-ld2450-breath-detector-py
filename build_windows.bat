@echo off
setlocal EnableExtensions
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py -3"
) else (
    set "PY=python"
)

%PY% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo Need Python 3.11+ on PATH.
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    %PY% -m venv .venv
    if errorlevel 1 exit /b 1
)

set "VENV_PY=.venv\Scripts\python.exe"
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"%VENV_PY%" -m pip install -r requirements.txt -r requirements-build.txt
if errorlevel 1 exit /b 1

"%VENV_PY%" -m PyInstaller --noconfirm --clean packaging\ld2450.spec
if errorlevel 1 exit /b 1

echo.
echo Built: dist\LD2450-Monitor\LD2450-Monitor.exe
echo Copy the whole dist\LD2450-Monitor folder to the target PC.
exit /b 0
