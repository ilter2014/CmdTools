@echo off
REM ============================================================
REM CmdTools v0.3 — Windows Otomatik Kurulum
REM ============================================================
REM Çift tıklayarak çalıştırın.
REM Python 3.8+ gerekli.
REM ============================================================

setlocal enabledelayedexpansion

set "KURULUM_DIR=C:\CmdTools"
set "REPO_URL=https://github.com/ilter2014/CmdTools/archive/refs/heads/main.zip"
set "GECICI=%TEMP%\cmdtools_install.zip"
set "GECICI_DIR=%TEMP%\cmdtools_extract"

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║     CmdTools v0.3 Windows Kurulumu      ║
echo   ║     github.com/ilter2014/CmdTools        ║
echo   ╚══════════════════════════════════════════╝
echo.

REM ─── 1. PYTHON KONTROLU ───
echo   1/5  Python kontrol ediliyor...
where python >nul 2>&1
if errorlevel 1 (
    echo   ✗ Python bulunamadi!
    echo     Kurulum icin Python 3.8+ gereklidir.
    echo     https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   ✓ Python %PYVER% bulundu
echo.

REM ─── 2. INTERNET KONTROLU ───
echo   2/5  Internet baglantisi kontrol ediliyor...
curl -s --max-time 5 https://github.com >nul 2>&1
if errorlevel 1 (
    echo   ✗ Internet baglantisi yok!
    pause
    exit /b 1
)
echo   ✓ Internet baglantisi OK
echo.

REM ─── 3. MEVCUT KONTROL ───
echo   3/5  Mevcut kurulum kontrol ediliyor...
if exist "%KURULUM_DIR%" (
    echo   → Mevcut kurulum bulundu, guncelleniyor...
    rmdir /s /q "%KURULUM_DIR%" 2>nul
)

REM ─── 4. INDIRME ───
echo   4/5  Indiriliyor...
curl -L -o "%GECICI%" "%REPO_URL%" --progress-bar
if errorlevel 1 (
    echo   ✗ Indirme basarisiz!
    pause
    exit /b 1
)
echo   ✓ Indirme tamamlandi
echo.

REM ─── 5. CIKARMA VE KURULUM ───
echo   5/5  Kuruluyor...
if exist "%GECICI_DIR%" rmdir /s /q "%GECICI_DIR%"
mkdir "%GECICI_DIR%" 2>nul
powershell -command "Expand-Archive -Path '%GECICI%' -DestinationPath '%GECICI_DIR%' -Force"

REM CmdTools-main klasörünü bul ve tasi
for /d %%D in ("%GECICI_DIR%\CmdTools-*") do (
    move "%%D" "%KURULUM_DIR%" >nul 2>&1
)

REM Gecik dosyalari temizle
del "%GECICI%" 2>nul
rmdir /s /q "%GECICI_DIR%" 2>nul

if not exist "%KURULUM_DIR%" (
    echo   ✗ Kurulum basarisiz!
    pause
    exit /b 1
)
echo   ✓ %KURULUM_DIR% konumuna kuruldu
echo.

REM ─── PATH KAYDI ───
echo   PATH guncelleniyor...
setx PATH "%PATH%;%KURULUM_DIR%" >nul 2>&1
echo   ✓ PATH'e eklendi
echo.

REM ─── KUTUPHANE KURULUMU ───
echo   Kütüphaneler kuruluyor...
python "%KURULUM_DIR%\updaterouter.py" --cmdname cmdtools install 2>nul
echo.

REM ─── SONUC ───
echo   ╔══════════════════════════════════════════╗
echo   ║         KURULUM BASARILI!               ║
echo   ╠══════════════════════════════════════════╣
echo   ║  Konum: C:\CmdTools                     ║
echo   ║                                          ║
echo   ║  Yeni CMD acarak baslayabilirsiniz:      ║
echo   ║    sysinfo                              ║
echo   ║    calc 25*8+10                         ║
echo   ║    cmdtools help                        ║
echo   ╚══════════════════════════════════════════╝
echo.
pause
