@echo off
set PRODAEM_WEB=1
echo Iniciando servidor Flask...
start /B "" "C:\Users\HP\Downloads\ProDaem\venv\Scripts\python.exe" "C:\Users\HP\Downloads\ProDaem\web\app.py"
timeout /t 4 /nobreak >nul
echo Iniciando tunel...
"C:\Users\HP\Downloads\ProDaem\cloudflared.exe" tunnel --url http://localhost:5000
