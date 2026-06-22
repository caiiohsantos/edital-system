@echo off
setlocal
echo.
echo ============================================================
echo   EDITAL SYSTEM - Setup do Ambiente
echo ============================================================
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)
python --version
echo.
if exist "venv\Scripts\python.exe" (
    echo [OK] venv ja existe
) else (
    echo Criando ambiente virtual...
    python -m venv venv
    echo [OK] venv criado
)
echo.
echo Instalando dependencias...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
python -m pip install PySide6 --quiet
echo [OK] PySide6
python -m pip install requests --quiet
echo [OK] requests
python -m pip install pyinstaller --quiet
echo [OK] PyInstaller
echo.
echo ============================================================
echo   SETUP CONCLUIDO!
echo ============================================================
echo.
echo   run_admin.bat    -^> Painel admin (senha: admin123)
echo   run_cliente.bat  -^> App cliente
echo   build.bat        -^> Compilar e gerar instalador
echo.
pause
