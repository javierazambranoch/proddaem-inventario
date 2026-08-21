import hashlib
import traceback

resultado_texto = []

try:
    from conexion import obtener_conexion
    resultado_texto.append("Import de conexion: OK")

    usuario_prueba = "admin_liceo"
    clave_prueba = "1234"

    hash_calculado = hashlib.sha256(clave_prueba.encode()).hexdigest()
    resultado_texto.append("Hash calculado en Python: " + repr(hash_calculado))

    conexion = obtener_conexion()
    resultado_texto.append("Conexión a Supabase: OK")
    cursor = conexion.cursor()

    cursor.execute("SELECT clave_hash FROM Usuario WHERE nombre_usuario = %s", (usuario_prueba,))
    fila = cursor.fetchone()
    if fila:
        resultado_texto.append("Hash guardado en Supabase: " + repr(fila[0]))
    else:
        resultado_texto.append("NO SE ENCONTRÓ EL USUARIO")

    cursor.execute(
        "SELECT id_usuario, id_establecimiento FROM Usuario WHERE nombre_usuario = %s AND clave_hash = %s",
        (usuario_prueba, hash_calculado)
    )
    resultado = cursor.fetchone()
    resultado_texto.append("Resultado de la consulta completa: " + str(resultado))

    conexion.close()

except Exception as e:
    resultado_texto.append("‼️ ERROR CAPTURADO:")
    resultado_texto.append(traceback.format_exc())

with open("salida.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(resultado_texto))

for linea in resultado_texto:
    print(linea)

print("\n--- FIN DEL SCRIPT ---")