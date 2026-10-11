@echo off
setlocal
pushd "%~dp0"
set "PYTHONUTF8=1"

echo [AI-Canvas] canvas-only mode (index.html). For DSL + canvas cockpit use: start_editor.bat
echo.

set "PYW="
set "PYC="
where pyw >nul 2>nul && where py >nul 2>nul
if not errorlevel 1 ( set "PYW=pyw" & set "PYC=py" )
if not defined PYW (
  where pythonw >nul 2>nul && where python >nul 2>nul
  if not errorlevel 1 ( set "PYW=pythonw" & set "PYC=python" )
)
if not defined PYW (
  if exist "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe" (
    set "PYW=%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
    set "PYC=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
  )
)
if not defined PYW (
  echo [AI-Canvas] pythonw/python not found.
  pause
  goto :end
)

%PYC% -c "import webview" >nul 2>nul
if errorlevel 1 (
  echo [AI-Canvas] pywebview is not installed for: %PYC%
  echo             Run:  %PYC% -m pip install pywebview
  pause
  goto :end
)

start "" %PYW% -X utf8 canvas_app.py

:end
popd
endlocal
exit /b 0
