@echo off
cd /d "%~dp0%"
set FLASK_APP=app.py
set FLASK_ENV=development
C:\Python313\python.exe -m flask run
pause
