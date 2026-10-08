@echo off
pushd "%~dp0"
set "PYW=%LOCALAPPDATA%\Programs\Python\Python314\pythonw.exe"
if not exist "%PYW%" set "PYW=pythonw"
set PYTHONUTF8=1
start "" "%PYW%" -X utf8 canvas_app.py
popd
exit
