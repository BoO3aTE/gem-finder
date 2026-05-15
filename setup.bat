@echo off
echo Installing gem-finder dependencies...
py -3 -m pip install -r requirements.txt
echo.
echo Done! Now run: py -3 scanner.py
pause
