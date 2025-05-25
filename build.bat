@echo off
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing requirements...
pip install -r requirements.txt

echo Creating icons...
python create_icons.py

echo Building executable...
pyinstaller whisper_gui.spec

echo Build complete! The executable can be found in the dist folder.
pause 