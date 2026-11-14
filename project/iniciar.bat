@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3.13 --version >nul 2>nul
  if not errorlevel 1 (
    if not exist "data\cirurgias.db" py -3.13 application\app.py --init
    py -3.13 application\app.py
    goto :end
  )
)
set "CC_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%CC_PYTHON%" (
  if not exist "data\cirurgias.db" "%CC_PYTHON%" application\app.py --init
  "%CC_PYTHON%" application\app.py
  goto :end
)
python --version >nul 2>nul
if errorlevel 1 (
  echo Instale Python 3.13 e volte a executar iniciar.bat.
  pause
  exit /b 1
)
if not exist "data\cirurgias.db" python application\app.py --init
python application\app.py
:end
endlocal
