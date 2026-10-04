@echo off
setlocal
cd /d "%~dp0"
set "PYTHON="
set "BOOTSTRAP="
set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys; print(sys.version)" >nul 2>&1
    if errorlevel 1 (
        echo A .venv foi copiada de outro computador e precisa ser recriada.
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=[IO.Path]::GetFullPath('.venv'); $r=[IO.Path]::GetFullPath('.'); if ([IO.Path]::GetDirectoryName($p).TrimEnd('\') -ne $r.TrimEnd('\')) { exit 9 }; Remove-Item -LiteralPath $p -Recurse -Force"
        if errorlevel 1 goto :error
    ) else (
        set "PYTHON=%VENV_PYTHON%"
    )
)

if not defined PYTHON (
    py -3 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1 && set "BOOTSTRAP=py -3"
    if not defined BOOTSTRAP python -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1 && set "BOOTSTRAP=python"
    if not defined BOOTSTRAP (
        where winget >nul 2>&1 || goto :python_missing
        echo Instalando Python 3.12 neste computador...
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements || goto :error
        if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "BOOTSTRAP="%LocalAppData%\Programs\Python\Python312\python.exe""
        if not defined BOOTSTRAP if exist "C:\Program Files\Python312\python.exe" set "BOOTSTRAP="C:\Program Files\Python312\python.exe""
        if not defined BOOTSTRAP py -3.12 --version >nul 2>&1 && set "BOOTSTRAP=py -3.12"
        if not defined BOOTSTRAP goto :restart_required
    )
)

if defined PYTHON goto :install
echo Criando uma .venv propria para este computador...
%BOOTSTRAP% -m venv .venv || goto :error
set "PYTHON=%VENV_PYTHON%"

:install
echo Instalando ou atualizando dependencias...
"%PYTHON%" -m pip install -e . || goto :error
echo Verificando navegador do gerador PDF...
"%PYTHON%" -m playwright install chromium || goto :error
echo Gerando um relatorio para cada paciente da pasta xray...
"%PYTHON%" gerar_relatorio.py || goto :error
pause
exit /b 0

:python_missing
echo Python 3.11 ou superior nao foi encontrado e o winget nao esta disponivel.
echo Instale o Python 3.12 e execute este arquivo novamente.
pause
exit /b 1

:restart_required
echo Python foi instalado, mas o Windows ainda nao atualizou os caminhos.
echo Reinicie o computador e execute este arquivo novamente.
pause
exit /b 1

:error
echo Ocorreu um erro. Veja as mensagens acima.
pause
exit /b 1
