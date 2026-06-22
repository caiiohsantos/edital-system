@echo off
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe admin\painel_admin.py
) else (
    python admin\painel_admin.py
)
