import psycopg2

conn = psycopg2.connect(
    host='aws-0-us-east-2.pooler.supabase.com',
    port='5432',
    dbname='postgres',
    user='postgres.noshouqodrmqqcegkddk',
    password='Daem2026Nacimiento'
)
cur = conn.cursor()
cur.execute("ALTER TABLE Evento ADD COLUMN IF NOT EXISTS hora TEXT DEFAULT ''")
cur.execute("ALTER TABLE Evento ADD COLUMN IF NOT EXISTS id_establecimiento_destino INTEGER")
conn.commit()
print("Columnas agregadas")

cur.execute("SELECT id_evento, hora, id_establecimiento_destino FROM Evento")
for row in cur.fetchall():
    print(row)
conn.close()
