@echo off
setlocal
REM Windows launcher. Drag images/folders onto this file, or double-click it and paste a path.
REM From a terminal, options work too:  optimize.bat photos -q 75 -w 1600

set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
    python --version >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo Python 3 was not found on this computer.
    echo Install it from https://www.python.org/downloads/
    echo During setup, tick "Add python.exe to PATH". Then run this again.
    echo.
    pause
    exit /b 1
)

%PY% "%~dp0optimize.py" %*
echo.
pause
