@echo off
setlocal
cd /d "%~dp0"
python "%~dp0ssc_plus.py" %*
set "SSC_PLUS_RC=%ERRORLEVEL%"
echo.
if not "%SSC_PLUS_RC%"=="0" echo SSC Plus terminou com codigo %SSC_PLUS_RC%.
pause
exit /b %SSC_PLUS_RC%
