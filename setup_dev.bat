@echo off
setlocal

echo.
echo ============================================================
echo   EDITAL SYSTEM - Setup do Ambiente de Desenvolvimento
echo ============================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Acesse https://python.org/downloads
    pause
    exit /b 1
)

python --version
echo.

if exist "venv\Scripts\python.exe" (
    echo [OK] venv ja existe, pulando...
) else (
    echo Criando ambiente virtual...
    python -m venv venv
    if %errorlevel% neq 0 ( echo [ERRO] Falha ao criar venv & pause & exit /b 1 )
    echo [OK] venv criado
)

echo.
echo Instalando dependencias...
echo.

call venv\Scripts\activate.bat

python -m pip install --upgrade pip --quiet

python -m pip install PySide6 --quiet
if %errorlevel% neq 0 ( echo [ERRO] Falha PySide6 & pause & exit /b 1 )
echo [OK] PySide6

python -m pip install requests --quiet
echo [OK] requests

python -m pip install pyinstaller --quiet
if %errorlevel% neq 0 ( echo [ERRO] Falha PyInstaller & pause & exit /b 1 )
echo [OK] PyInstaller

echo.
echo Verificando Microsoft Edge para tutorial nativo...
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    echo [OK] Microsoft Edge encontrado - Tutorial abrira em janela nativa!
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    echo [OK] Microsoft Edge encontrado - Tutorial abrira em janela nativa!
) else (
    echo [INFO] Edge nao encontrado - tutorial abrira no navegador padrao
)

echo.
echo ============================================================
echo   SETUP CONCLUIDO!
echo ============================================================
echo.
echo   run_admin.bat    -^> Painel admin (senha: admin123)
echo   run_cliente.bat  -^> App cliente
echo   build.bat        -^> Compilar e gerar instalador
echo.
echo ============================================================
pause
