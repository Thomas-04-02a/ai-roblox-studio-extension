@echo off
setlocal
cd /d "%~dp0.."
python bridge\mock_roblox_server.py
