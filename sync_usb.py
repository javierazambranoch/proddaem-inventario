import sqlite3
import os
import sys
import shutil
from datetime import datetime

DB_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_DB = os.path.join(DB_DIR, "inventario.db")


def sync_usb(usb_path):
    usb_db = os.path.join(usb_path, "inventario.db")

    if not os.path.exists(usb_db):
        print(f"ERROR: No se encontro inventario.db en {usb_path}")
        return False

    print(f"\nSincronizando desde: {usb_path}")

    master = sqlite3.connect(MASTER_DB)
    usb = sqlite3.connect(usb_db)

    mcur = master.cursor()
    ucur = usb.cursor()

    sincronizados = 0
    duplicados = 0

    ucur.execute("SELECT codigo, categoria, marca, modelo, estado, descripcion_condicion, ubicacion_asignada, id_establecimiento FROM Computador")
    for row in ucur.fetchall():
        try:
            mcur.execute(
                "INSERT INTO Computador (codigo, categoria, marca, modelo, estado, descripcion_condicion, ubicacion_asignada, id_establecimiento) VALUES (?,?,?,?,?,?,?,?)",
                row
            )
            sincronizados += 1
        except sqlite3.IntegrityError:
            duplicados += 1

    sol_sync = 0
    sol_dup = 0
    ucur.execute("SELECT nombre_producto, nro_serie, cantidad, caracteristicas, estado, descripcion, prioridad, id_usuario, id_establecimiento FROM solicitud")
    for row in ucur.fetchall():
        try:
            mcur.execute(
                "INSERT INTO solicitud (nombre_producto, nro_serie, cantidad, caracteristicas, estado, descripcion, prioridad, id_usuario, id_establecimiento) VALUES (?,?,?,?,?,?,?,?,?)",
                row
            )
            sol_sync += 1
        except Exception:
            sol_dup += 1

    hist_sync = 0
    ucur.execute("SELECT id_usuario, accion, fecha_hora FROM Historial")
    for row in ucur.fetchall():
        try:
            mcur.execute(
                "INSERT INTO Historial (id_usuario, accion, fecha_hora) VALUES (?,?,?)",
                row
            )
            hist_sync += 1
        except Exception:
            pass

    master.commit()

    print(f"\n--- RESULTADO ---")
    print(f"Equipos: {sincronizados} sincronizados, {duplicados} duplicados")
    print(f"Solicitudes: {sol_sync} sincronizadas, {sol_dup} duplicadas")
    print(f"Historial: {hist_sync} registros sincronizados")

    usb.close()
    master.close()

    return True


def export_to_usb(usb_path):
    os.makedirs(usb_path, exist_ok=True)
    destino = os.path.join(usb_path, "inventario.db")
    shutil.copy2(MASTER_DB, destino)
    print(f"Base de datos exportada a: {destino}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nSINCRONIZADOR DE DATOS - DAEM")
        print("=" * 40)
        print("\nUso:")
        print("  python sync_usb.py sincronizar <ruta_usb>")
        print("  python sync_usb.py exportar <ruta_usb>")
        print("\nEjemplo:")
        print("  python sync_usb.py sincronizar E:\\")
        print("  python sync_usb.py exportar E:\\LiceoMunicipal")
        sys.exit(0)

    accion = sys.argv[1].lower()
    ruta = sys.argv[2] if len(sys.argv) > 2 else "."

    if accion == "sincronizar":
        sync_usb(ruta)
    elif accion == "exportar":
        export_to_usb(ruta)
    else:
        print(f"Acción desconocida: {accion}")
