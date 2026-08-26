import psycopg2

conn = psycopg2.connect(
    host='aws-0-us-east-2.pooler.supabase.com',
    port='5432',
    dbname='postgres',
    user='postgres.noshouqodrmqqcegkddk',
    password='Daem2026Nacimiento'
)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS Evento (
        id_evento SERIAL PRIMARY KEY,
        titulo TEXT NOT NULL,
        descripcion TEXT DEFAULT '',
        fecha DATE NOT NULL,
        id_usuario_creador INTEGER,
        fecha_creacion TIMESTAMP DEFAULT NOW()
    )
""")
conn.commit()
print("Tabla Evento creada")
conn.close()
