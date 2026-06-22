@echo off
setlocal
set "ROOT=%~dp0"
set "PYINST=%ROOT%venv\Scripts\pyinstaller.exe"
echo.
echo ============================================================
echo   EDITAL SYSTEM - Build
echo ============================================================
if not exist "%PYINST%" (
    echo [ERRO] Execute setup_dev.bat primeiro.
    pause & exit /b 1
)
echo [1/3] Limpando...
if exist "%ROOT%dist" rmdir /s /q "%ROOT%dist"
if exist "%ROOT%build" rmdir /s /q "%ROOT%build"
echo [2/3] Compilando cliente...
cd /d "%ROOT%"
"%PYINST%" build_client.spec --clean --noconfirm --log-level WARN
echo [3/3] Compilando admin...
"%PYINST%" build_admin.spec --clean --noconfirm --log-level WARN
echo.
echo ============================================================
echo   BUILD FINALIZADO!
echo   CLIENTE: dist\EditalSystem\EditalSystem.exe
echo   ADMIN:   dist\EditalAdmin\EditalAdmin.exe
echo ============================================================
pause
