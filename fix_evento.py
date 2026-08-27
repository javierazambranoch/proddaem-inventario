import psycopg2

conn = psycopg2.connect(
    host='aws-0-us-east-2.pooler.supabase.com',
    port='5432',
    dbname='postgres',
    user='postgres.noshouqodrmqqcegkddk',
    password='Daem2026Nacimiento'
)
cur = conn.cursor()
cur.execute("ALTER TABLE Evento ADD COLUMN IF NOT EXISTS id_usuario_creador INTEGER")
cur.execute("ALTER TABLE Evento ADD COLUMN IF NOT EXISTS visible_para_todos BOOLEAN DEFAULT TRUE")
cur.execute("ALTER TABLE Evento ADD COLUMN IF NOT EXISTS id_establecimiento_destino INTEGER")
conn.commit()

# Migrate existing rows based on old 'tipo' column if it exists
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='evento' AND column_name='tipo'")
if cur.fetchone():
    cur.execute("UPDATE Evento SET visible_para_todos = FALSE WHERE tipo = 'agenda'")
    cur.execute("UPDATE Evento SET visible_para_todos = TRUE WHERE tipo = 'daem'")
    conn.commit()
    print("Datos migrados segun columna tipo")

# Set id_usuario_creador for existing events (admin_daem)
cur.execute("SELECT id_usuario FROM Usuario WHERE LOWER(nombre_usuario) = 'admin_daem'")
row = cur.fetchone()
if row:
    cur.execute("UPDATE Evento SET id_usuario_creador = %s WHERE id_usuario_creador IS NULL", (row[0],))
    conn.commit()
    print("id_usuario_creador asignado a admin_daem:", row[0])

conn.commit()
print("LISTO")
conn.close()
