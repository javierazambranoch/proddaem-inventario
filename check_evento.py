import psycopg2

conn = psycopg2.connect(
    host='aws-0-us-east-2.pooler.supabase.com',
    port='5432',
    dbname='postgres',
    user='postgres.noshouqodrmqqcegkddk',
    password='Daem2026Nacimiento'
)
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='evento' ORDER BY ordinal_position")
for row in cur.fetchall():
    print(row)
conn.close()
