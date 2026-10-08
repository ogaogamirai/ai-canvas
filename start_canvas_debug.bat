@echo off
pushd "%~dp0"
set "PY=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not exist "%PY%" set "PY=python"
set PYTHONUTF8=1
"%PY%" -X utf8 canvas_app.py
popd
pause
