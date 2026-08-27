import psycopg2
conn = psycopg2.connect(host='aws-0-us-east-2.pooler.supabase.com', port='5432', dbname='postgres', user='postgres.noshouqodrmqqcegkddk', password='Daem2026Nacimiento')
cur = conn.cursor()
cur.execute("ALTER TABLE Computador ADD COLUMN IF NOT EXISTS responsable TEXT")
conn.commit()
print("Columna responsable agregada")
conn.close()
