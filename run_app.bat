@echo off
echo [1/3] Checking dependencies...
pip install -r requirements.txt

echo [2/3] Ensuring Playwright browser is installed...
playwright install chromium

echo [3/3] Starting ChromiPrint...
python main_gui.py

pause
