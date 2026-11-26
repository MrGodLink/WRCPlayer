@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: Uso: build.bat [/nopause]   (/nopause = nessuna pausa interattiva, utile per CI)
set "NO_PAUSE="
if /i "%~1"=="/nopause" set "NO_PAUSE=1"

:: ==============================================================================
:: Colori ANSI (Windows 10/11)
:: ==============================================================================
cls
for /F %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "CYAN=%ESC%[96m"
set "BOLD=%ESC%[1m"
set "RESET=%ESC%[0m"

:: ==============================================================================
:: Configurazione progetto
:: ==============================================================================
set "PROJECT_NAME=WRCPlayer"
set "VERSION=1.6.0"
set "ENTRY_SCRIPT=main.py"
set "ICON_PATH=assets\app_icon.ico"
set "REQUIREMENTS=requirements-dev.txt"
set "BASE_REQUIREMENTS=requirements.txt"
set "ASSETS_SCRIPT=scripts\make_assets.py"
set "OUTPUT_DIR=dist"
set "VENV_DIR=venv"

:: Timestamp indipendente dalle impostazioni locali (una sola chiamata PowerShell)
for /f "tokens=*" %%a in ('powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set "TIMESTAMP=%%a"
set "LOG_FILE=build_%TIMESTAMP%.log"

:: ==============================================================================
:: Schermata iniziale (solo caratteri ASCII sicuri per cmd)
:: ==============================================================================
echo.
echo %CYAN%  ################################################################%RESET%
echo %CYAN%  #                                                              #%RESET%
echo %CYAN%  #      ##                                                      #%RESET%
echo %CYAN%  #      ####                                                    #%RESET%
echo %CYAN%  #      ######      W R C P L A Y E R                           #%RESET%
echo %CYAN%  #      ########    Media Player - Build Script                 #%RESET%
echo %CYAN%  #      ######                                                  #%RESET%
echo %CYAN%  #      ####        by MrGodLink                                #%RESET%
echo %CYAN%  #      ##                                                      #%RESET%
echo %CYAN%  #                                                              #%RESET%
echo %CYAN%  ################################################################%RESET%
echo.
echo   %YELLOW%Progetto :%RESET% %PROJECT_NAME% v%VERSION%
echo   %YELLOW%Autore   :%RESET% Raffaele Catapano
echo   %YELLOW%Entry    :%RESET% %ENTRY_SCRIPT%
echo   %YELLOW%Output   :%RESET% %OUTPUT_DIR%\%PROJECT_NAME%.exe
echo   %YELLOW%Log      :%RESET% %LOG_FILE%
echo.
if defined NO_PAUSE goto :Start
echo   Premi un tasto per avviare la build (Ctrl+C per annullare)...
pause >nul
:Start

:: Inizializzazione log
>"%LOG_FILE%" echo [%TIMESTAMP%] Build started
call :LogMessage "INFO" "Starting build process for %PROJECT_NAME% v%VERSION%"

set "CURRENT_STEP=0"
set "TOTAL_STEPS=5"

:: ==============================================================================
:: Step 1: Verifica prerequisiti
:: ==============================================================================
call :PrintStep "Verifica prerequisiti"
call :LogMessage "INFO" "Step 1: Checking prerequisites"

python --version >nul 2>&1
if errorlevel 1 (
    call :PrintError "Python non trovato nel PATH"
    call :LogMessage "ERROR" "Python not found"
    goto :ErrorExit
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
call :PrintSuccess "Trovato: %PYTHON_VERSION%"
call :LogMessage "INFO" "%PYTHON_VERSION%"

:: File richiesti (l'icona viene generata allo Step 3, quindi non si controlla qui)
set "FILES_OK=1"
for %%F in ("%ENTRY_SCRIPT%" "%REQUIREMENTS%" "%BASE_REQUIREMENTS%" "%ASSETS_SCRIPT%") do (
    if not exist "%%~F" (
        call :PrintError "File mancante: %%~F"
        call :LogMessage "ERROR" "Missing %%~F"
        set "FILES_OK=0"
    ) else (
        call :PrintSuccess "Trovato: %%~F"
    )
)
if "%FILES_OK%"=="0" goto :ErrorExit

:: Ambiente virtuale
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    call :PrintInfo "Creazione ambiente virtuale"
    python -m venv "%VENV_DIR%" >>"%LOG_FILE%" 2>&1
    if errorlevel 1 (
        call :PrintError "Impossibile creare l'ambiente virtuale"
        call :LogMessage "ERROR" "venv creation failed"
        goto :ErrorExit
    )
)
call "%VENV_DIR%\Scripts\activate.bat" >nul 2>&1
call :PrintSuccess "Ambiente virtuale attivato"
call :LogMessage "SUCCESS" "Prerequisites check passed"

:: ==============================================================================
:: Step 2: Installazione dipendenze
:: ==============================================================================
call :PrintStep "Installazione dipendenze"
call :LogMessage "INFO" "Step 2: Installing dependencies from %REQUIREMENTS%"

python -m pip install -r "%REQUIREMENTS%" >>"%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :PrintError "Installazione dipendenze fallita (ultime righe del log):"
    call :LogMessage "ERROR" "pip install failed"
    powershell -NoProfile -Command "Get-Content -Tail 15 '%LOG_FILE%'"
    goto :ErrorExit
)
call :PrintSuccess "Dipendenze installate"
call :LogMessage "SUCCESS" "Dependencies installed"

:: ==============================================================================
:: Step 3: Generazione asset
:: ==============================================================================
call :PrintStep "Generazione asset"
call :LogMessage "INFO" "Step 3: Running %ASSETS_SCRIPT%"

python "%ASSETS_SCRIPT%"
if errorlevel 1 (
    call :PrintError "Generazione asset fallita"
    call :LogMessage "ERROR" "make_assets.py failed"
    goto :ErrorExit
)
if not exist "%ICON_PATH%" (
    call :PrintError "Icona non generata: %ICON_PATH%"
    call :LogMessage "ERROR" "Icon missing after asset generation"
    goto :ErrorExit
)
call :PrintSuccess "Asset generati"
call :LogMessage "SUCCESS" "Assets generated"

:: ==============================================================================
:: Step 4: Verifica PyInstaller
:: ==============================================================================
call :PrintStep "Verifica PyInstaller"
call :LogMessage "INFO" "Step 4: Checking PyInstaller availability"

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    call :PrintError "PyInstaller non trovato. Aggiungilo a %REQUIREMENTS%"
    call :LogMessage "ERROR" "PyInstaller not found"
    goto :ErrorExit
)
call :PrintSuccess "PyInstaller pronto"
call :LogMessage "SUCCESS" "PyInstaller verified"

:: ==============================================================================
:: Step 5: Build con PyInstaller
:: ==============================================================================
call :PrintStep "Compilazione eseguibile con PyInstaller"
call :LogMessage "INFO" "Step 5: Running PyInstaller"

python -m PyInstaller --noconfirm --clean --onefile --windowed --name "%PROJECT_NAME%" --icon "%ICON_PATH%" --hidden-import qt_engine --hidden-import mock_engine --hidden-import wmp_engine --hidden-import win32com.client --hidden-import pywintypes --hidden-import pythoncom "%ENTRY_SCRIPT%"
if errorlevel 1 (
    call :PrintError "Compilazione PyInstaller fallita (vedi output sopra)"
    call :LogMessage "ERROR" "PyInstaller build failed"
    goto :ErrorExit
)

set "EXE_PATH=%OUTPUT_DIR%\%PROJECT_NAME%.exe"
if not exist "%EXE_PATH%" (
    call :PrintError "Eseguibile non trovato: %EXE_PATH%"
    call :LogMessage "ERROR" "Output exe not found"
    goto :ErrorExit
)

:: Dimensione del file exe, in MB con 1 decimale
set /a "TOTAL_KB=0"
for %%F in ("%EXE_PATH%") do set /a "TOTAL_KB=%%~zF/1024"
set /a "MB10=TOTAL_KB*10/1024"
set /a "MB_INT=MB10/10"
set /a "MB_DEC=MB10%%10"
set "SIZE_MB_STR=%MB_INT%.%MB_DEC%"

call :PrintSuccess "Build completata con successo!"
call :LogMessage "SUCCESS" "Build completed"
call :LogMessage "INFO" "Output: %EXE_PATH%"
call :LogMessage "INFO" "File size: %SIZE_MB_STR% MB"
goto :SuccessExit

:: ==============================================================================
:: Gestori di uscita
:: ==============================================================================
:SuccessExit
call :LogMessage "SUCCESS" "Build process completed successfully"
echo.
echo ================================================================================
echo %GREEN%%BOLD%                         BUILD COMPLETED SUCCESSFULLY%RESET%
echo ================================================================================
echo   %CYAN%Project:%RESET%    %PROJECT_NAME% v%VERSION%
echo   %CYAN%Output:%RESET%     %EXE_PATH%
echo   %CYAN%Size:%RESET%       %SIZE_MB_STR% MB (file)
echo   %CYAN%Log file:%RESET%   %LOG_FILE%
echo ================================================================================
echo.
if not defined NO_PAUSE (
    echo Premi un tasto per uscire...
    pause >nul
)
exit /b 0

:ErrorExit
call :LogMessage "ERROR" "Build process failed"
echo.
echo ================================================================================
echo %RED%%BOLD%                              BUILD FAILED%RESET%
echo ================================================================================
echo   Controlla il file di log per i dettagli: %LOG_FILE%
echo ================================================================================
echo.
if not defined NO_PAUSE (
    echo Premi un tasto per uscire...
    pause >nul
)
exit /b 1

:: ==============================================================================
:: Sottoprogrammi
:: ==============================================================================
:PrintStep
set /a CURRENT_STEP+=1
echo.
echo %YELLOW%%BOLD%[Step %CURRENT_STEP%/%TOTAL_STEPS%] %~1%RESET%
echo --------------------------------------------------------------------------------
goto :eof

:PrintInfo
echo %CYAN%[INFO] %~1%RESET%
goto :eof

:PrintSuccess
echo %GREEN%[OK] %~1%RESET%
goto :eof

:PrintError
echo %RED%[ERROR] %~1%RESET%
goto :eof

:LogMessage
set "NOW=%TIME: =0%"
>>"%LOG_FILE%" echo [%NOW:~0,8%] [%~1] %~2
goto :eof
