@echo off
setlocal

set "APP_VERSION=1.0.0"
set "ROOT=%~dp0"
set "DIST=%ROOT%dist"
set "PY=%ROOT%venv\Scripts\python.exe"
set "PYINST=%ROOT%venv\Scripts\pyinstaller.exe"
set "INNO=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

echo.
echo ============================================================
echo   EDITAL SYSTEM v%APP_VERSION% - Build
echo ============================================================

if not exist "%PY%" (
    echo [ERRO] venv nao encontrado. Execute setup_dev.bat primeiro.
    pause & exit /b 1
)
echo [OK] venv encontrado

echo.
echo [1/4] Limpando builds anteriores...
if exist "%DIST%" rmdir /s /q "%DIST%"
if exist "%ROOT%build" rmdir /s /q "%ROOT%build"
echo [OK] Limpo

echo.
echo [2/4] Criando pasta tutoriais...
if not exist "%ROOT%tutoriais" mkdir "%ROOT%tutoriais"
echo [OK] Pasta tutoriais OK

echo.
echo [3/4] Compilando APP CLIENTE...
cd /d "%ROOT%"
"%PYINST%" build_client.spec --clean --noconfirm --log-level WARN
if %errorlevel% neq 0 (
    echo [ERRO] Falha no build do cliente
    pause & exit /b 1
)
echo [OK] dist\EditalSystem\EditalSystem.exe gerado

echo.
echo [4/4] Compilando PAINEL ADMIN...
"%PYINST%" build_admin.spec --clean --noconfirm --log-level WARN
if %errorlevel% neq 0 (
    echo [ERRO] Falha no build do admin
    pause & exit /b 1
)
echo [OK] dist\EditalAdmin\EditalAdmin.exe gerado

echo.
echo ============================================================
echo   BUILD FINALIZADO COM SUCESSO!
echo ============================================================
echo.
echo   CLIENTE: dist\EditalSystem\EditalSystem.exe
echo   ADMIN:   dist\EditalAdmin\EditalAdmin.exe
echo.
echo   Distribua a pasta dist\EditalSystem\ inteira para os clientes.
echo   NUNCA distribua a pasta EditalAdmin.
echo.

set /p "OPEN=Abrir pasta dist no Explorer? (S/N): "
if /i "%OPEN%"=="S" explorer "%DIST%"
pause
