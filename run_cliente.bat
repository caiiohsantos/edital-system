@echo off
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe client\app.py
) else (
    echo [AVISO] venv nao encontrado. Rodando com Python do sistema...
    python client\app.py
)
