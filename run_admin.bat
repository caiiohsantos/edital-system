@echo off
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe admin\painel_admin.py
) else (
    echo [AVISO] venv nao encontrado. Rodando com Python do sistema...
    python admin\painel_admin.py
)
