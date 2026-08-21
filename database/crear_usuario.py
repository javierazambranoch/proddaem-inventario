import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "inventario.db")

def crear_usuario(nombre_usuario, clave):
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    clave_hash = hashlib.sha256(clave.encode()).hexdigest()

    try:
        cursor.execute(
            "INSERT INTO Usuario (nombre_usuario, clave_hash) VALUES (?, ?)",
            (nombre_usuario, clave_hash)
        )
        conexion.commit()
        print(f"Usuario '{nombre_usuario}' creado correctamente.")
    except sqlite3.IntegrityError:
        print(f"El usuario '{nombre_usuario}' ya existe.")
    finally:
        conexion.close()

if __name__ == "__main__":
    crear_usuario("juan", "1234")