@echo off
pushd "%~dp0"
set "PY=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not exist "%PY%" set "PY=python"
powershell -NoProfile -WindowStyle Hidden -Command "Start-Process '%PY%' -ArgumentList '-X utf8 canvas_app.py' -WindowStyle Hidden"
popd
exit
