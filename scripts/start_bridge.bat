@echo off
setlocal
cd /d "%~dp0.."
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r bridge\requirements.txt
python scripts\start_bridge.py
