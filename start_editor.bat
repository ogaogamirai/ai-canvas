@echo off
setlocal
pushd "%~dp0"
set "PYTHONUTF8=1"

rem --- Locate a windowed Python (PYW) and its matching console twin (PYC) ---
set "PYW="
set "PYC="

rem 1) py launcher pair (uses the default installed Python)
where pyw >nul 2>nul && where py >nul 2>nul
if not errorlevel 1 ( set "PYW=pyw" & set "PYC=py" )

rem 2) pythonw / python on PATH
if not defined PYW (
  where pythonw >nul 2>nul && where python >nul 2>nul
  if not errorlevel 1 ( set "PYW=pythonw" & set "PYC=python" )
)

rem 3) LOCALAPPDATA Python314 fallback
if not defined PYW (
  if exist "%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe" (
    set "PYW=%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
    set "PYC=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
  )
)

if not defined PYW (
  echo [AI-Canvas] pythonw/python not found.
  echo             Install Python 3.11+ and run:  pip install pywebview
  pause
  goto :end
)

rem --- Diagnostic mode: start_editor.bat --check (no GUI) ---
if /i "%~1"=="--check" (
  echo [AI-Canvas] windowed launcher : %PYW%
  echo [AI-Canvas] console  launcher : %PYC%
  %PYC% -c "import webview, sys; print('[AI-Canvas] webview OK ->', sys.executable)"
  goto :end
)

rem --- Preflight: pywebview must be importable by the SAME interpreter ---
%PYC% -c "import webview" >nul 2>nul
if errorlevel 1 (
  echo [AI-Canvas] pywebview is not installed for:
  echo             %PYC%
  echo             Run:  %PYC% -m pip install pywebview
  pause
  goto :end
)

start "" %PYW% -X utf8 editor_app.py

:end
popd
endlocal
exit /b 0
