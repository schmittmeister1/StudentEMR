@echo off
setlocal
cd /d %~dp0

if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
)

call .venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt

echo Starting PTA EMR Playground...
python app.py

endlocal
