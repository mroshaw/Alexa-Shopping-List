@echo off

cd /d "%~dp0\.."

set PYTHONPATH=%CD%\src

set FLASK_APP=flaskapp.app:create_app
set FLASK_RUN_HOST=0.0.0.0
set FLASK_RUN_PORT=5000

.venv\Scripts\python.exe -m flask run
