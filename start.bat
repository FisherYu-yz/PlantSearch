@echo off
cd /d "%~dp0"

set "PLANT_PYTHON=D:\AN\envs\your_env_name\python.exe"

if not exist "%PLANT_PYTHON%" (
    echo Python interpreter not found:
    echo %PLANT_PYTHON%
    pause
    exit /b 1
)

if not exist "app.py" (
    echo app.py not found in:
    cd
    echo Please extract the entire project first.
    pause
    exit /b 1
)

"%PLANT_PYTHON%" -m streamlit run "%~dp0app.py"
pause