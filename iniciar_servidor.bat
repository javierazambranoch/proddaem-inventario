@echo off
title ProDaem - Servidor Web
echo ============================================
echo   ProDaem - Servidor Web Iniciando...
echo ============================================
echo.
echo Abre en el navegador: http://localhost:5000
echo.
echo Para acceso remoto, instala ngrok y ejecuta:
echo   ngrok http 5000
echo.
echo Presiona Ctrl+C para detener el servidor.
echo.
"C:\Users\HP\Downloads\ProDaem\venv\Scripts\python.exe" "C:\Users\HP\Downloads\ProDaem\web\app.py"
pause
