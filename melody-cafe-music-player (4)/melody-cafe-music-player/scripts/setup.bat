@echo off
echo Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate
python -m pip install -r requirements.txt
echo.
echo Done. Start the app with run.bat
pause
