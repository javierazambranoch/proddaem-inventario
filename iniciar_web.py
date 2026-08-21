import subprocess
import os
import time
import sys

os.environ["PRODAEM_WEB"] = "1"

base = os.path.dirname(os.path.abspath(__file__))
python = os.path.join(base, "venv", "Scripts", "python.exe")
flask_app = os.path.join(base, "web", "app.py")
cloudflared = os.path.join(base, "cloudflared.exe")

print("=" * 50)
print("  ProDaem - Iniciando servidor web...")
print("=" * 50)

flask_proc = subprocess.Popen(
    [python, flask_app],
    env=os.environ,
    cwd=base
)

print("Esperando que Flask inicie...")
time.sleep(4)

print("Iniciando tunel cloudflared...")
cloud_proc = subprocess.Popen(
    [cloudflared, "tunnel", "--url", "http://localhost:5000"],
    env=os.environ,
    cwd=base,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

url_found = False
start = time.time()
while time.time() - start < 20:
    line = cloud_proc.stdout.readline()
    if not line:
        time.sleep(0.1)
        continue
    print(line.strip())
    if "trycloudflare.com" in line and "https://" in line:
        for word in line.split():
            if word.startswith("https://"):
                print("\n" + "=" * 50)
                print(f"  URL LISTA PARA ENVIAR:")
                print(f"  {word}")
                print("=" * 50)
                url_found = True
                break
    if url_found:
        break

if not url_found:
    print("\nNo se pudo obtener la URL. Verifica que Flask este corriendo.")

print("\nPresiona Ctrl+C para detener todo.")
try:
    flask_proc.wait()
except KeyboardInterrupt:
    flask_proc.terminate()
    cloud_proc.terminate()
    print("\nServidor detenido.")
