import os
import sqlite3
import re
from datetime import datetime

MODO_WEB = os.environ.get("PRODAEM_WEB", "0") == "1"

DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, "inventario.db")


class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor
        self._rowcount = 0

    def execute(self, query, params=None):
        converted = re.sub(r'%s', '?', query)
        if params:
            self._cursor.execute(converted, params)
        else:
            self._cursor.execute(converted)
        self._rowcount = self._cursor.rowcount

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchone(self):
        return self._cursor.fetchone()

    @property
    def rowcount(self):
        return self._rowcount

    @rowcount.setter
    def rowcount(self, val):
        self._rowcount = val


class SQLiteConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return SQLiteCursorWrapper(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def crear_tablas_sqlite():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            id_establecimiento INTEGER NOT NULL,
            nombre_usuario TEXT UNIQUE NOT NULL,
            clave_hash TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Computador (
            id_inventario INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            categoria TEXT NOT NULL,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            estado TEXT NOT NULL,
            descripcion_condicion TEXT,
            ubicacion_asignada TEXT,
            id_establecimiento INTEGER NOT NULL,
            fecha_registro TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS solicitud (
            id_solicitud INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_producto TEXT NOT NULL,
            nro_serie TEXT,
            cantidad INTEGER NOT NULL,
            caracteristicas TEXT,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            descripcion TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            id_usuario INTEGER NOT NULL,
            id_establecimiento INTEGER NOT NULL,
            fecha_solicitud TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Historial (
            id_historial INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            accion TEXT NOT NULL,
            fecha_hora TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)
    usuarios = [
        (1, "admin_daem"), (9, "admin_saber"), (3, "admin_oscar"),
        (4, "admin_liceo"), (2, "admin_canada")
    ]
    hash_clave = "03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4"
    for id_est, nombre in usuarios:
        cur.execute(
            "INSERT OR IGNORE INTO Usuario (id_establecimiento, nombre_usuario, clave_hash) VALUES (?,?,?)",
            (id_est, nombre, hash_clave)
        )
    conn.commit()
    conn.close()


def _obtener_supabase():
    import psycopg2
    return psycopg2.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port="5432",
        dbname="postgres",
        user="postgres.noshouqodrmqqcegkddk",
        password="Daem2026Nacimiento"
    )


def _obtener_sqlite():
    crear_tablas_sqlite()
    return SQLiteConnectionWrapper(sqlite3.connect(DB_PATH))


def obtener_conexion():
    if MODO_WEB:
        return _obtener_supabase()
    else:
        try:
            return _obtener_supabase()
        except Exception:
            return _obtener_sqlite()


def registrar_historial(id_usuario, accion):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO Historial (id_usuario, accion, fecha_hora) VALUES (%s, %s, %s)",
            (id_usuario, accion, fecha_hora)
        )
        conexion.commit()
        conexion.close()
    except Exception as e:
        print("ERROR HISTORIAL:", e)


if __name__ == "__main__":
    modo = "WEB (Supabase)" if MODO_WEB else "OFFLINE (SQLite)"
    print(f"Modo: {modo}")
    try:
        conexion = obtener_conexion()
        cur = conexion.cursor()
        cur.execute("SELECT COUNT(*) FROM Usuario")
        print("Usuarios:", cur.fetchone()[0])
        conexion.close()
    except Exception as e:
        print("Error:", e)
