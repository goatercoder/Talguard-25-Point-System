@echo off
echo Starting Talguard Investment Screener...
python -m streamlit run "%~dp0app.py" --server.headless false
pause
