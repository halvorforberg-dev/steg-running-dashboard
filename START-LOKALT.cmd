@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist .private .venv\Scripts\python.exe setup.py
.venv\Scripts\python.exe server.py
pause
