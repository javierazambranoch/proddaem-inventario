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
    CREATE TABLE IF NOT EXISTS Encargado (
        id_encargado SERIAL PRIMARY KEY,
        id_establecimiento INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        cargo TEXT DEFAULT 'Encargado',
        telefono TEXT DEFAULT '',
        email TEXT DEFAULT ''
    )
""")
conn.commit()
print("Tabla Encargado creada")

cur.execute("SELECT COUNT(*) FROM Encargado")
count = cur.fetchone()[0]
if count == 0:
    encargados = [
        (9, 'Victor Pinto', 'Encargado'),
        (3, '', 'Encargado'),
        (2, '', 'Encargado'),
        (4, '', 'Encargado'),
        (5, '', 'Encargado'),
    ]
    for id_est, nombre, cargo in encargados:
        cur.execute(
            "INSERT INTO Encargado (id_establecimiento, nombre, cargo) VALUES (%s, %s, %s)",
            (id_est, nombre, cargo)
        )
    conn.commit()
    print("Encargados iniciales insertados")
else:
    print("Ya hay", count, "encargados")

conn.close()
