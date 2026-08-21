import sqlite3
import os

# Ruta de la base de datos (queda en la raíz del proyecto)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "inventario.db")

def crear_base_datos():
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    # Tabla de usuarios (login)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_usuario TEXT UNIQUE NOT NULL,
            clave_hash TEXT NOT NULL
        )
    """)

    # Tabla de computadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Computador (
            id_inventario TEXT PRIMARY KEY,
            marca_modelo TEXT NOT NULL,
            tipo TEXT CHECK(tipo IN ('escritorio','notebook')) NOT NULL,
            estado TEXT CHECK(estado IN ('bueno','regular','malo')) NOT NULL,
            fecha_registro TEXT NOT NULL
        )
    """)

    # Tabla de bajas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Dar_baja (
            id_baja INTEGER PRIMARY KEY AUTOINCREMENT,
            id_inventario TEXT NOT NULL,
            motivo_baja TEXT NOT NULL,
            fecha_baja TEXT NOT NULL,
            FOREIGN KEY (id_inventario) REFERENCES Computador(id_inventario)
        )
    """)

    # Tabla de solicitudes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Solicitud (
            id_solicitud INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_producto TEXT NOT NULL,
            nro_serie TEXT,
            cantidad INTEGER NOT NULL,
            caracteristicas TEXT,
            estado TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            id_usuario INTEGER NOT NULL,
            fecha_solicitud TEXT NOT NULL,
            FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
        )
    """)

    # Tabla de historial
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Historial (
            id_historial INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            accion TEXT NOT NULL,
            fecha_hora TEXT NOT NULL,
            FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
        )
    """)

    conexion.commit()
    conexion.close()
    print("Base de datos creada correctamente en:", os.path.abspath(DB_PATH))

if __name__ == "__main__":
    print("Ruta esperada:", DB_PATH)
    crear_base_datos()