import hashlib
import os
import psycopg2
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "daem_inventario_2026_prod")

ESTABLECIMIENTOS = {
    "Escuela El Saber": 9,
    "Escuela Oscar Guerrero": 3,
    "Escuela Canada": 2,
    "Liceo Municipal": 4,
    "Escuela Toqui Lautaro": 5
}

NOMBRES_DISPLAY = {
    "admin_liceo": "Victor Pinto",
    "admin_saber": "Victor Pinto",
    "admin_daem": "Daniel Medina"
}


def obtener_conexion():
    return psycopg2.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port="5432",
        dbname="postgres",
        user="postgres.noshouqodrmqqcegkddk",
        password="Daem2026Nacimiento"
    )


def registrar_historial(id_usuario, accion):
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Historial (id_usuario, accion, fecha_hora) VALUES (%s, %s, %s)",
            (id_usuario, accion, datetime.now())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("ERROR HISTORIAL:", e)


def login_requerido():
    return "usuario" in session


def crear_tabla_mensajes():
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Mensaje (
                id_mensaje SERIAL PRIMARY KEY,
                id_usuario INTEGER NOT NULL,
                mensaje TEXT NOT NULL,
                id_establecimiento_destino INTEGER,
                fecha_hora TIMESTAMP DEFAULT NOW()
            )
        """)
        try:
            cur.execute("ALTER TABLE Mensaje ADD COLUMN IF NOT EXISTS id_establecimiento_destino INTEGER")
        except Exception:
            pass
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Mensaje_leido (
                id_leido SERIAL PRIMARY KEY,
                id_mensaje INTEGER NOT NULL,
                id_establecimiento INTEGER NOT NULL,
                leido_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (id_mensaje, id_establecimiento)
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print("ERROR CREAR TABLA MENSAJE:", e)


crear_tabla_mensajes()


def crear_tabla_eventos():
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Evento (
                id_evento SERIAL PRIMARY KEY,
                titulo VARCHAR(200) NOT NULL,
                descripcion TEXT DEFAULT '',
                fecha DATE NOT NULL,
                hora TIME DEFAULT '08:00',
                establecimiento VARCHAR(150) NOT NULL,
                tipo VARCHAR(20) NOT NULL DEFAULT 'agenda',
                fecha_creacion TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print("ERROR CREAR TABLA EVENTO:", e)


crear_tabla_eventos()


def crear_columna_baja():
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("ALTER TABLE Computador ADD COLUMN IF NOT EXISTS baja BOOLEAN DEFAULT FALSE")
        conn.commit()
        conn.close()
    except Exception as e:
        print("ERROR CREAR COLUMNA BAJA:", e)


crear_columna_baja()


@app.route("/")
def index():
    if login_requerido():
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nombre = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "").strip()

        if not nombre or not clave:
            flash("Debes ingresar usuario y clave.", "warning")
            return render_template("login.html")

        clave_hash = hashlib.sha256(clave.encode()).hexdigest()

        try:
            conn = obtener_conexion()
            cur = conn.cursor()
            cur.execute(
                "SELECT id_usuario, id_establecimiento, nombre_completo FROM Usuario "
                "WHERE nombre_usuario = %s AND clave_hash = %s",
                (nombre, clave_hash)
            )
            resultado = cur.fetchone()
            conn.close()

            if resultado:
                session["usuario"] = nombre
                session["id_usuario"] = resultado[0]
                session["id_establecimiento"] = resultado[1]
                nombre_display = NOMBRES_DISPLAY.get(nombre, nombre)
                if resultado[2]:
                    nombre_display = resultado[2]
                elif nombre != "admin_daem":
                    try:
                        conn2 = obtener_conexion()
                        cur2 = conn2.cursor()
                        cur2.execute(
                            "SELECT nombre FROM Encargado WHERE id_establecimiento = %s "
                            "ORDER BY id_encargado LIMIT 1",
                            (resultado[1],)
                        )
                        enc = cur2.fetchone()
                        conn2.close()
                        if enc and enc[0]:
                            nombre_display = enc[0]
                    except Exception:
                        pass
                session["nombre_display"] = nombre_display
                registrar_historial(resultado[0], "Inicio de sesión")
                return redirect(url_for("dashboard"))
            else:
                flash("Usuario o clave incorrectos.", "danger")

        except Exception as e:
            flash(f"Error de conexión: {e}", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    nombre_display = session.get("nombre_display", session["usuario"])
    solicitudes_pendientes = 0
    mensajes_nuevos = 0

    try:
        conn = obtener_conexion()
        cur = conn.cursor()

        id_est = session["id_establecimiento"]
        if es_daem:
            cur.execute(
                "SELECT COUNT(DISTINCT id_solicitud) FROM solicitud WHERE estado IN ('pendiente', 'en proceso')"
            )
        else:
            cur.execute(
                "SELECT COUNT(*) FROM solicitud WHERE id_establecimiento = %s AND notif_cambio = TRUE",
                (id_est,)
            )
        solicitudes_pendientes = cur.fetchone()[0]

        if es_daem:
            cur.execute(
                "SELECT COUNT(*) FROM Mensaje m "
                "JOIN Usuario u ON m.id_usuario = u.id_usuario "
                "WHERE u.nombre_usuario <> 'admin_daem' "
                "AND NOT EXISTS (SELECT 1 FROM Mensaje_leido l "
                "                 WHERE l.id_mensaje = m.id_mensaje AND l.id_establecimiento = 1)"
            )
        else:
            cur.execute(
                "SELECT COUNT(*) FROM Mensaje m "
                "JOIN Usuario u ON m.id_usuario = u.id_usuario "
                "WHERE ((u.id_establecimiento = %s AND m.id_establecimiento_destino IS NULL) "
                "       OR (m.id_establecimiento_destino = %s AND u.nombre_usuario = 'admin_daem') "
                "       OR (m.id_establecimiento_destino IS NULL AND u.nombre_usuario = 'admin_daem')) "
                "AND u.nombre_usuario <> 'admin_daem' "
                "AND NOT EXISTS (SELECT 1 FROM Mensaje_leido l "
                "                 WHERE l.id_mensaje = m.id_mensaje AND l.id_establecimiento = %s)",
                (id_est, id_est, id_est)
            )
        mensajes_nuevos = cur.fetchone()[0]

        if es_daem:
            cur.execute(
                "SELECT titulo, descripcion, fecha, hora FROM Evento "
                "WHERE fecha >= CURRENT_DATE AND id_usuario_creador = %s "
                "ORDER BY fecha ASC LIMIT 5",
                (session["id_usuario"],)
            )
        else:
            cur.execute(
                "SELECT titulo, descripcion, fecha, hora FROM Evento "
                "WHERE fecha >= CURRENT_DATE "
                "  AND (visible_para_todos = TRUE OR id_establecimiento_destino = %s) "
                "ORDER BY fecha ASC LIMIT 5",
                (id_est,)
            )
        proximos_eventos = cur.fetchall()

        conn.close()
    except Exception as e:
        print("ERROR NOTIFICACIONES:", e)

    return render_template("dashboard.html",
                           usuario=session["usuario"],
                           nombre_display=nombre_display,
                           es_daem=es_daem,
                           solicitudes_pendientes=solicitudes_pendientes,
                           mensajes_nuevos=mensajes_nuevos,
                           proximos_eventos=proximos_eventos)


@app.route("/inventario", methods=["GET", "POST"])
def inventario():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    id_usuario = session["id_usuario"]
    id_est = session["id_establecimiento"]
    equipos = []
    buscar = request.args.get("buscar", "").strip()
    est_filtro = request.args.get("establecimiento", "0")

    try:
        conn = obtener_conexion()
        cur = conn.cursor()

        if es_daem and buscar:
            if est_filtro == "0":
                cur.execute(
                    "SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada, responsable, lugar_almacenamiento "
                    "FROM Computador WHERE codigo ILIKE %s AND baja = FALSE ORDER BY fecha_registro DESC",
                    (f"%{buscar}%",)
                )
            else:
                cur.execute(
                    "SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada, responsable, lugar_almacenamiento "
                    "FROM Computador WHERE codigo ILIKE %s AND id_establecimiento = %s AND baja = FALSE "
                    "ORDER BY fecha_registro DESC",
                    (f"%{buscar}%", est_filtro)
                )
        elif es_daem:
            if est_filtro == "0":
                cur.execute(
                    "SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada, responsable, lugar_almacenamiento "
                    "FROM Computador WHERE baja = FALSE ORDER BY fecha_registro DESC"
                )
            else:
                cur.execute(
                    "SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada, responsable, lugar_almacenamiento "
                    "FROM Computador WHERE id_establecimiento = %s AND baja = FALSE ORDER BY fecha_registro DESC",
                    (est_filtro,)
                )
        else:
            cur.execute(
                "SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada, responsable, lugar_almacenamiento "
                "FROM Computador WHERE id_establecimiento = %s AND baja = FALSE ORDER BY fecha_registro DESC",
                (id_est,)
            )

        equipos = cur.fetchall()
        conn.close()

    except Exception as e:
        flash(f"Error al cargar inventario: {e}", "danger")

    return render_template("inventario.html",
                           usuario=session["usuario"],
                           es_daem=es_daem,
                           equipos=equipos,
                           buscar=buscar,
                           est_filtro=est_filtro,
                           establecimientos=ESTABLECIMIENTOS)


@app.route("/inventario/guardar", methods=["POST"])
def inv_guardar():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    id_usuario = session["id_usuario"]

    codigo = request.form.get("codigo", "").strip()
    categoria = request.form.get("categoria", "").strip()
    marca = request.form.get("marca", "").strip()
    modelo = request.form.get("modelo", "").strip()
    estado = request.form.get("estado", "").strip()
    ubicacion = request.form.get("ubicacion", "").strip()
    responsable = request.form.get("responsable", "").strip()
    lugar_almacenamiento = request.form.get("lugar_almacenamiento", "").strip()
    condicion = request.form.get("condicion", "").strip()
    est_filtro = request.form.get("est_filtro", str(session["id_establecimiento"]))
    requiere = request.form.get("requiere", "").strip()
    desc_solicitud = request.form.get("desc_solicitud", "").strip()

    if es_daem:
        id_establecimiento = int(est_filtro) if est_filtro != "0" else session["id_establecimiento"]
    else:
        id_establecimiento = session["id_establecimiento"]

    if not codigo or not categoria or not marca or not modelo or not estado or not ubicacion:
        flash("Todos los campos son obligatorios.", "warning")
        return redirect(url_for("inventario", buscar=request.form.get("buscar", ""), establecimiento=est_filtro))

    try:
        conn = obtener_conexion()
        cur = conn.cursor()

        cur.execute(
            """INSERT INTO Computador
            (codigo, categoria, marca, modelo, estado,
             descripcion_condicion, ubicacion_asignada, responsable, lugar_almacenamiento, id_establecimiento, baja)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (codigo, categoria, marca, modelo, estado,
             condicion if condicion else None, ubicacion, responsable if responsable else None,
             lugar_almacenamiento if lugar_almacenamiento else None, id_establecimiento,
             True if estado == "malo" else False)
        )

        solicitud_creada = False
        if estado in ("regular", "malo"):
            prioridad = "media" if estado == "regular" else "alta"
            nombre_prod = f"{requiere.capitalize() if requiere else 'Solicitud'} - {categoria} {marca} {modelo}"
            caracts = f"Código: {codigo} | Marca: {marca} | Modelo: {modelo} | Ubicación: {ubicacion}"
            desc = desc_solicitud if desc_solicitud else f"Solicitud automática desde Inventario.\nEquipo: {codigo}\nEstado: {estado}"
            if estado == "malo":
                desc = f"{desc}\nEste equipo fue dado de baja automáticamente por estar en estado MALO."
            cur.execute(
                """INSERT INTO solicitud
                (nombre_producto, nro_serie, cantidad, caracteristicas,
                 estado, descripcion, prioridad, id_usuario, id_establecimiento, notif_cambio)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (nombre_prod, codigo, 1, caracts, "pendiente", desc, prioridad, id_usuario, id_establecimiento, True)
            )
            solicitud_creada = True

        conn.commit()
        conn.close()

        accion = f"Registro de equipo '{codigo}' ({categoria} {marca} {modelo})"
        if solicitud_creada:
            accion += f" - Solicitud automática"
        registrar_historial(id_usuario, accion)
        flash(f"Equipo '{codigo}' registrado correctamente.", "success")

    except Exception as e:
        if "duplicate key" in str(e).lower():
            flash(f"El código '{codigo}' ya existe.", "danger")
        else:
            flash(f"Error al guardar: {e}", "danger")

    return redirect(url_for("inventario", buscar=request.form.get("buscar", ""), establecimiento=est_filtro))


@app.route("/inventario/eliminar/<codigo>", methods=["POST"])
def inv_eliminar(codigo):
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    est_filtro = request.form.get("est_filtro", "0")

    try:
        conn = obtener_conexion()
        cur = conn.cursor()

        if es_daem and est_filtro != "0":
            cur.execute(
                "DELETE FROM Computador WHERE codigo = %s AND id_establecimiento = %s",
                (codigo, est_filtro)
            )
        elif es_daem:
            cur.execute("DELETE FROM Computador WHERE codigo = %s", (codigo,))
        else:
            cur.execute(
                "DELETE FROM Computador WHERE codigo = %s AND id_establecimiento = %s",
                (codigo, session["id_establecimiento"])
            )

        conn.commit()
        conn.close()

        registrar_historial(session["id_usuario"], f"Eliminación de equipo '{codigo}'")
        flash(f"Equipo '{codigo}' eliminado.", "success")

    except Exception as e:
        flash(f"Error al eliminar: {e}", "danger")

    return redirect(url_for("inventario", buscar=request.form.get("buscar", ""), establecimiento=est_filtro))


@app.route("/dar_baja", methods=["GET"])
def dar_baja():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    id_est = session["id_establecimiento"]
    est_filtro = request.args.get("establecimiento", "0")
    lista = []

    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cols = "codigo, categoria, marca, modelo, estado, ubicacion_asignada, responsable, lugar_almacenamiento, descripcion_condicion"
        if es_daem:
            if est_filtro == "0":
                cur.execute(f"SELECT {cols}, id_establecimiento FROM Computador WHERE baja = TRUE ORDER BY fecha_registro DESC")
            else:
                cur.execute(f"SELECT {cols}, id_establecimiento FROM Computador WHERE baja = TRUE AND id_establecimiento = %s ORDER BY fecha_registro DESC", (est_filtro,))
        else:
            cur.execute(f"SELECT {cols}, id_establecimiento FROM Computador WHERE baja = TRUE AND id_establecimiento = %s ORDER BY fecha_registro DESC", (id_est,))
        lista = cur.fetchall()
        conn.close()
    except Exception as e:
        flash(f"Error al cargar dar de baja: {e}", "danger")

    return render_template("dar_baja.html",
                           usuario=session["usuario"],
                           es_daem=es_daem,
                           bajas=lista,
                           est_filtro=est_filtro,
                           establecimientos=ESTABLECIMIENTOS,
                           est_nombres={v: k for k, v in ESTABLECIMIENTOS.items()})


@app.route("/dar_baja/reincorporar", methods=["POST"])
def dar_baja_reincorporar():
    if not login_requerido():
        return redirect(url_for("login"))

    codigo = request.form.get("codigo", "").strip()
    est_filtro = request.form.get("est_filtro", "0")

    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute(
            "UPDATE Computador SET baja = FALSE, estado = 'bueno' WHERE codigo = %s",
            (codigo,)
        )
        conn.commit()
        conn.close()
        registrar_historial(session["id_usuario"], f"Reincorporación de equipo '{codigo}'")
        flash(f"Equipo '{codigo}' reincorporado al inventario.", "success")
    except Exception as e:
        flash(f"Error al reincorporar: {e}", "danger")

    return redirect(url_for("dar_baja", establecimiento=est_filtro))


@app.route("/solicitudes", methods=["GET", "POST"])
def solicitudes():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    id_usuario = session["id_usuario"]
    id_est = session["id_establecimiento"]
    lista = []
    buscar = request.args.get("buscar", "").strip()
    est_filtro = request.args.get("establecimiento", "0")

    try:
        conn = obtener_conexion()
        cur = conn.cursor()

        if es_daem and buscar:
            if est_filtro == "0":
                cur.execute(
                    "SELECT id_solicitud, nombre_producto, nro_serie, cantidad, prioridad, estado "
                    "FROM solicitud WHERE nombre_producto ILIKE %s ORDER BY fecha_solicitud DESC",
                    (f"%{buscar}%",)
                )
            else:
                cur.execute(
                    "SELECT id_solicitud, nombre_producto, nro_serie, cantidad, prioridad, estado "
                    "FROM solicitud WHERE nombre_producto ILIKE %s AND id_establecimiento = %s "
                    "ORDER BY fecha_solicitud DESC",
                    (f"%{buscar}%", est_filtro)
                )
        elif es_daem:
            if est_filtro == "0":
                cur.execute(
                    "SELECT id_solicitud, nombre_producto, nro_serie, cantidad, prioridad, estado "
                    "FROM solicitud ORDER BY fecha_solicitud DESC"
                )
            else:
                cur.execute(
                    "SELECT id_solicitud, nombre_producto, nro_serie, cantidad, prioridad, estado "
                    "FROM solicitud WHERE id_establecimiento = %s ORDER BY fecha_solicitud DESC",
                    (est_filtro,)
                )
        else:
            cur.execute(
                "SELECT id_solicitud, nombre_producto, nro_serie, cantidad, prioridad, estado "
                "FROM solicitud WHERE id_usuario = %s AND id_establecimiento = %s "
                "ORDER BY fecha_solicitud DESC",
                (id_usuario, id_est)
            )

        lista = cur.fetchall()

        if not es_daem:
            cur.execute(
                "UPDATE solicitud SET notif_cambio = FALSE WHERE id_establecimiento = %s AND notif_cambio = TRUE",
                (id_est,)
            )
            conn.commit()

        conn.close()

    except Exception as e:
        flash(f"Error al cargar solicitudes: {e}", "danger")

    return render_template("solicitudes.html",
                           usuario=session["usuario"],
                           es_daem=es_daem,
                           solicitudes=lista,
                           buscar=buscar,
                           est_filtro=est_filtro,
                           establecimientos=ESTABLECIMIENTOS)


@app.route("/solicitudes/enviar", methods=["POST"])
def sol_enviar():
    if not login_requerido():
        return redirect(url_for("login"))

    id_usuario = session["id_usuario"]
    id_est = session["id_establecimiento"]

    producto = request.form.get("producto", "").strip()
    marca = request.form.get("marca", "").strip()
    modelo = request.form.get("modelo", "").strip()
    cantidad = request.form.get("cantidad", "").strip()
    prioridad = request.form.get("prioridad", "media").strip()
    caracteristicas = request.form.get("caracteristicas", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    if not producto or not marca or not modelo or not cantidad or not descripcion:
        flash("Producto, marca, modelo, cantidad y descripción son obligatorios.", "warning")
        return redirect(url_for("solicitudes"))

    try:
        cantidad_num = int(cantidad)
        if cantidad_num <= 0:
            raise ValueError
    except ValueError:
        flash("La cantidad debe ser un número mayor que 0.", "warning")
        return redirect(url_for("solicitudes"))

    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO solicitud
            (nombre_producto, nro_serie, cantidad, caracteristicas,
             estado, descripcion, prioridad, id_usuario, id_establecimiento, notif_cambio)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (producto, f"{marca} {modelo}", cantidad_num,
             caracteristicas if caracteristicas else None,
             "pendiente", descripcion, prioridad, id_usuario, id_est, True)
        )
        conn.commit()
        conn.close()

        registrar_historial(id_usuario, f"Envío de solicitud: '{producto} {marca} {modelo}' (cantidad: {cantidad_num})")
        flash("Solicitud enviada correctamente.", "success")

    except Exception as e:
        flash(f"Error al enviar: {e}", "danger")

    return redirect(url_for("solicitudes"))


@app.route("/solicitudes/eliminar/<int:id_solicitud>", methods=["POST"])
def sol_eliminar(id_solicitud):
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"

    try:
        conn = obtener_conexion()
        cur = conn.cursor()

        if es_daem:
            cur.execute("DELETE FROM solicitud WHERE id_solicitud = %s", (id_solicitud,))
        else:
            cur.execute(
                "DELETE FROM solicitud WHERE id_solicitud = %s AND id_usuario = %s AND id_establecimiento = %s",
                (id_solicitud, session["id_usuario"], session["id_establecimiento"])
            )

        conn.commit()
        conn.close()

        registrar_historial(session["id_usuario"], f"Eliminación de solicitud N° {id_solicitud}")
        flash(f"Solicitud N° {id_solicitud} eliminada.", "success")

    except Exception as e:
        flash(f"Error al eliminar: {e}", "danger")

    est_filtro = request.form.get("est_filtro", "0")
    return redirect(url_for("solicitudes", establecimiento=est_filtro))


@app.route("/solicitudes/cambiar_estado/<int:id_solicitud>", methods=["POST"])
def sol_cambiar_estado(id_solicitud):
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    nuevo_estado = request.form.get("nuevo_estado", "").strip()
    comentario = request.form.get("comentario_estado", "").strip()
    est_filtro = request.form.get("est_filtro", "0")

    if not nuevo_estado:
        flash("Selecciona un estado.", "warning")
        return redirect(url_for("solicitudes", establecimiento=est_filtro))

    # Rechazada exige motivo obligatorio
    if nuevo_estado == "rechazada" and len(comentario) < 4:
        flash("Al rechazar una solicitud debes escribir el motivo como comentario.", "warning")
        return redirect(url_for("solicitudes", establecimiento=est_filtro))

    try:
        conn = obtener_conexion()
        cur = conn.cursor()

        # Actualizar estado
        cur.execute(
            "UPDATE solicitud SET estado = %s, notif_cambio = TRUE WHERE id_solicitud = %s",
            (nuevo_estado, id_solicitud)
        )

        # Si hay comentario, guardarlo como mensaje personalizado al establecimiento
        if comentario:
            # Obtener el id_usuario del solicitante para enviar el comentario como chat
            cur.execute(
                "SELECT id_usuario, id_establecimiento FROM solicitud WHERE id_solicitud = %s",
                (id_solicitud,)
            )
            sol_data = cur.fetchone()
            if sol_data:
                id_autor = session["id_usuario"]
                texto_msg = f"[Solicitud N°{id_solicitud} → {nuevo_estado.upper()}] {comentario}"
                cur.execute(
                    "INSERT INTO Mensaje (id_usuario, mensaje, id_establecimiento_destino, fecha_hora) "
                    "VALUES (%s, %s, %s, %s)",
                    (id_autor, texto_msg, sol_data[1], datetime.now())
                )

        conn.commit()
        conn.close()

        registrar_historial(
            session["id_usuario"],
            f"Cambio estado solicitud N° {id_solicitud} → {nuevo_estado}"
        )
        flash(f"Solicitud N° {id_solicitud} actualizada a '{nuevo_estado}'.", "success")

    except Exception as e:
        flash(f"Error al cambiar estado: {e}", "danger")

    return redirect(url_for("solicitudes", establecimiento=est_filtro))


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    id_usuario = session["id_usuario"]
    id_est = session["id_establecimiento"]
    usuario = session["usuario"]
    nombre_display = session.get("nombre_display", session["usuario"])
    est_filtro = request.args.get("establecimiento", str(id_est) if not es_daem else "0")

    session["chat_ultimo_visita"] = datetime.now()

    if request.method == "POST":
        mensaje = request.form.get("mensaje", "").strip()
        dest = request.form.get("destino", str(id_est) if not es_daem else "0")
        if mensaje:
            try:
                conn = obtener_conexion()
                cur = conn.cursor()
                dest_val = int(dest) if dest != "0" else None
                cur.execute(
                    "INSERT INTO Mensaje (id_usuario, mensaje, id_establecimiento_destino, fecha_hora) "
                    "VALUES (%s, %s, %s, %s)",
                    (id_usuario, mensaje, dest_val, datetime.now())
                )
                conn.commit()
                conn.close()
            except Exception as e:
                flash(f"Error al enviar mensaje: {e}", "danger")
        if es_daem:
            return redirect(url_for("chat", establecimiento=dest))
        return redirect(url_for("chat"))

    mensajes = []
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        if es_daem:
            if est_filtro != "0":
                cur.execute(
                    "SELECT m.id_mensaje, m.mensaje, m.fecha_hora, u.nombre_usuario, m.id_establecimiento_destino "
                    "FROM Mensaje m JOIN Usuario u ON m.id_usuario = u.id_usuario "
                    "WHERE (m.id_establecimiento_destino = %s AND u.nombre_usuario = 'admin_daem') "
                    "OR (u.id_establecimiento = %s AND m.id_establecimiento_destino IS NULL) "
                    "OR (u.id_establecimiento = %s) "
                    "OR (m.id_establecimiento_destino IS NULL AND u.nombre_usuario = 'admin_daem') "
                    "ORDER BY m.fecha_hora ASC",
                    (est_filtro, est_filtro, est_filtro)
                )
            else:
                cur.execute(
                    "SELECT m.id_mensaje, m.mensaje, m.fecha_hora, u.nombre_usuario, m.id_establecimiento_destino "
                    "FROM Mensaje m JOIN Usuario u ON m.id_usuario = u.id_usuario "
                    "WHERE m.id_establecimiento_destino IS NULL "
                    "ORDER BY m.fecha_hora ASC"
                )
        else:
            cur.execute(
                "SELECT m.id_mensaje, m.mensaje, m.fecha_hora, u.nombre_usuario, m.id_establecimiento_destino "
                "FROM Mensaje m JOIN Usuario u ON m.id_usuario = u.id_usuario "
                "WHERE (u.id_establecimiento = %s AND m.id_establecimiento_destino IS NULL) "
                "OR (m.id_establecimiento_destino = %s AND u.nombre_usuario = 'admin_daem') "
                "OR (m.id_establecimiento_destino IS NULL AND u.nombre_usuario = 'admin_daem') "
                "ORDER BY m.fecha_hora ASC",
                (id_est, id_est)
            )
        filas = cur.fetchall()

        leido_ids = []
        for fila in filas:
            leido_ids.append(fila[0])
        if leido_ids:
            cur.executemany(
                "INSERT INTO Mensaje_leido (id_mensaje, id_establecimiento) VALUES (%s, %s) "
                "ON CONFLICT (id_mensaje, id_establecimiento) DO NOTHING",
                [(mid, id_est if not es_daem else 1) for mid in leido_ids]
            )
            conn.commit()

        if filas:
            cur.execute(
                "SELECT id_mensaje, id_establecimiento FROM Mensaje_leido "
                "WHERE id_mensaje = ANY(%s)",
                (leido_ids,)
            )
            reads = {}
            for rmid, rest in cur.fetchall():
                reads.setdefault(rmid, set()).add(rest)
        else:
            reads = {}

        visto_ids = set()
        for mid, msg, fecha, usr, dest in filas:
            if usr != usuario:
                continue
            if es_daem:
                if dest is None:
                    if reads.get(mid) and any(e != 1 for e in reads[mid]):
                        visto_ids.add(mid)
                elif dest in reads.get(mid, set()):
                    visto_ids.add(mid)
            else:
                if 1 in reads.get(mid, set()):
                    visto_ids.add(mid)

        mensajes = filas
        conn.close()
    except Exception as e:
        flash(f"Error al cargar chat: {e}", "danger")
        mensajes = []
        visto_ids = set()

    return render_template("chat.html",
                           usuario=session["usuario"],
                           nombre_display=nombre_display,
                           es_daem=es_daem,
                           mensajes=mensajes,
                           est_filtro=est_filtro,
                           establecimientos=ESTABLECIMIENTOS,
                           visto_ids=visto_ids)


@app.route("/historial")
def historial():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    id_usuario = session["id_usuario"]
    filtro = request.args.get("filtro", "Todos" if es_daem else "Mis actividades")
    registros = []

    try:
        conn = obtener_conexion()
        cur = conn.cursor()

        if es_daem and filtro == "Todos":
            cur.execute(
                "SELECT h.id_historial, u.nombre_usuario, h.accion, h.fecha_hora "
                "FROM Historial h LEFT JOIN Usuario u ON h.id_usuario = u.id_usuario "
                "ORDER BY h.fecha_hora DESC"
            )
        else:
            cur.execute(
                "SELECT h.id_historial, u.nombre_usuario, h.accion, h.fecha_hora "
                "FROM Historial h LEFT JOIN Usuario u ON h.id_usuario = u.id_usuario "
                "WHERE h.id_usuario = %s ORDER BY h.fecha_hora DESC",
                (id_usuario,)
            )

        registros = cur.fetchall()
        conn.close()

    except Exception as e:
        flash(f"Error al cargar historial: {e}", "danger")

    return render_template("historial.html",
                           usuario=session["usuario"],
                           es_daem=es_daem,
                           registros=registros,
                           filtro=filtro)


@app.route("/encargados", methods=["GET", "POST"])
def encargados():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    if not es_daem:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        accion = request.form.get("accion", "")

        if accion == "agregar":
            id_est = request.form.get("id_establecimiento", "").strip()
            nombre = request.form.get("nombre", "").strip()
            cargo = request.form.get("cargo", "Encargado").strip()
            telefono = request.form.get("telefono", "").strip()
            email = request.form.get("email", "").strip()
            if id_est and nombre:
                try:
                    conn = obtener_conexion()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO Encargado (id_establecimiento, nombre, cargo, telefono, email) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (int(id_est), nombre, cargo, telefono, email)
                    )
                    conn.commit()
                    conn.close()
                    flash("Encargado agregado.", "success")
                except Exception as e:
                    flash(f"Error: {e}", "danger")

        elif accion == "editar":
            id_enc = request.form.get("id_encargado", "").strip()
            nombre = request.form.get("nombre", "").strip()
            cargo = request.form.get("cargo", "").strip()
            telefono = request.form.get("telefono", "").strip()
            email = request.form.get("email", "").strip()
            if id_enc and nombre:
                try:
                    conn = obtener_conexion()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE Encargado SET nombre=%s, cargo=%s, telefono=%s, email=%s "
                        "WHERE id_encargado=%s",
                        (nombre, cargo, telefono, email, int(id_enc))
                    )
                    conn.commit()
                    conn.close()
                    flash("Encargado actualizado.", "success")
                except Exception as e:
                    flash(f"Error: {e}", "danger")

        elif accion == "eliminar":
            id_enc = request.form.get("id_encargado", "").strip()
            try:
                conn = obtener_conexion()
                cur = conn.cursor()
                cur.execute("DELETE FROM Encargado WHERE id_encargado=%s", (int(id_enc),))
                conn.commit()
                conn.close()
                flash("Encargado eliminado.", "success")
            except Exception as e:
                flash(f"Error: {e}", "danger")

        return redirect(url_for("encargados"))

    lista = []
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute(
            "SELECT e.id_encargado, e.id_establecimiento, e.nombre, e.cargo, e.telefono, e.email "
            "FROM Encargado e ORDER BY e.id_establecimiento"
        )
        lista = cur.fetchall()
        conn.close()
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return render_template("encargados.html",
                           usuario=session["usuario"],
                           encargados=lista,
                           establecimientos=ESTABLECIMIENTOS,
                           est_nombres={v: k for k, v in ESTABLECIMIENTOS.items()})


@app.route("/calendario", methods=["GET", "POST"])
def calendario():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        fecha = request.form.get("fecha", "").strip()
        hora = request.form.get("hora", "").strip()
        para_todos = request.form.get("para_todos", "1") == "1"
        destino = request.form.get("destino", "0").strip()

        if titulo and fecha:
            try:
                conn = obtener_conexion()
                cur = conn.cursor()
                if es_daem:
                    dest_val = int(destino) if destino != "0" else None
                else:
                    dest_val = session["id_establecimiento"]
                cur.execute(
                    "INSERT INTO Evento (titulo, descripcion, fecha, hora, id_usuario_creador, visible_para_todos, id_establecimiento_destino) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (titulo, descripcion, fecha, hora if hora else None, session["id_usuario"], para_todos, dest_val)
                )
                conn.commit()
                conn.close()
                flash("Evento creado.", "success")
            except Exception as e:
                flash(f"Error: {e}", "danger")
        return redirect(url_for("calendario"))

    eventos = []
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        if es_daem:
            cur.execute(
                "SELECT e.id_evento, e.titulo, e.descripcion, e.fecha, e.hora, "
                "e.visible_para_todos, e.id_establecimiento_destino, e.id_usuario_creador "
                "FROM Evento e WHERE e.id_usuario_creador = %s ORDER BY e.fecha DESC",
                (session["id_usuario"],)
            )
        else:
            cur.execute(
                "SELECT e.id_evento, e.titulo, e.descripcion, e.fecha, e.hora, "
                "e.visible_para_todos, e.id_establecimiento_destino, e.id_usuario_creador "
                "FROM Evento e "
                "WHERE e.visible_para_todos = TRUE "
                "   OR e.id_establecimiento_destino = %s "
                "ORDER BY e.fecha DESC",
                (session["id_establecimiento"],)
            )
        eventos = cur.fetchall()
        conn.close()
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return render_template("calendario.html",
                           usuario=session["usuario"],
                           es_daem=es_daem,
                           eventos=eventos,
                           establecimientos=ESTABLECIMIENTOS,
                           sesion_id=session["id_usuario"])


@app.route("/calendario/eliminar/<int:id_evento>", methods=["POST"])
def eliminar_evento(id_evento):
    if not login_requerido():
        return redirect(url_for("login"))

    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("DELETE FROM Evento WHERE id_evento = %s AND id_usuario_creador = %s",
                    (id_evento, session["id_usuario"]))
        conn.commit()
        conn.close()
        flash("Evento eliminado.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("calendario"))


@app.route("/calendario/editar/<int:id_evento>", methods=["POST"])
def editar_evento(id_evento):
    if not login_requerido():
        return redirect(url_for("login"))

    titulo = request.form.get("titulo", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    fecha = request.form.get("fecha", "").strip()
    hora = request.form.get("hora", "").strip()
    para_todos = request.form.get("para_todos", "1") == "1"
    destino = request.form.get("destino", "0").strip()

    if titulo and fecha:
        try:
            conn = obtener_conexion()
            cur = conn.cursor()
            dest_val = int(destino) if destino != "0" else None
            cur.execute(
                "UPDATE Evento SET titulo=%s, descripcion=%s, fecha=%s, hora=%s, "
                "visible_para_todos=%s, id_establecimiento_destino=%s "
                "WHERE id_evento=%s AND id_usuario_creador=%s",
                (titulo, descripcion, fecha, hora if hora else None, para_todos, dest_val, id_evento, session["id_usuario"])
            )
            conn.commit()
            conn.close()
            flash("Evento actualizado.", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")

    return redirect(url_for("calendario"))


@app.route("/calendario/toggle/<int:id_evento>", methods=["POST"])
def toggle_evento(id_evento):
    if not login_requerido():
        return redirect(url_for("login"))

    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("SELECT visible_para_todos FROM Evento WHERE id_evento=%s AND id_usuario_creador=%s",
                    (id_evento, session["id_usuario"]))
        row = cur.fetchone()
        if row:
            nuevo = not row[0]
            cur.execute("UPDATE Evento SET visible_para_todos=%s, id_establecimiento_destino=NULL WHERE id_evento=%s",
                        (nuevo, id_evento))
            conn.commit()
            flash("Evento actualizado." if nuevo else "Evento movido a agenda privada.", "success")
        else:
            flash("Evento no encontrado.", "danger")
        conn.close()
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("calendario"))


@app.route("/crear_perfil", methods=["GET", "POST"])
def crear_perfil():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    if not es_daem:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        nombre_est = request.form.get("nombre_establecimiento", "").strip()
        nombre_usuario = request.form.get("nombre_usuario", "").strip()
        clave = request.form.get("clave", "").strip()
        nombre_encargado = request.form.get("nombre_encargado", "").strip()

        if not nombre_est or not nombre_usuario or not clave:
            flash("Nombre del establecimiento, usuario y clave son obligatorios.", "warning")
            return redirect(url_for("crear_perfil"))

        try:
            conn = obtener_conexion()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO Establecimiento (nombre) VALUES (%s) RETURNING id_establecimiento",
                (nombre_est,)
            )
            id_nuevo = cur.fetchone()[0]

            clave_hash = hashlib.sha256(clave.encode()).hexdigest()
            cur.execute(
                "INSERT INTO Usuario (nombre_usuario, clave_hash, id_establecimiento) VALUES (%s, %s, %s)",
                (nombre_usuario, clave_hash, id_nuevo)
            )

            if nombre_encargado:
                cur.execute(
                    "INSERT INTO Encargado (id_establecimiento, nombre, cargo) VALUES (%s, %s, 'Encargado')",
                    (id_nuevo, nombre_encargado)
                )

            conn.commit()
            conn.close()

            ESTABLECIMIENTOS[nombre_est] = id_nuevo
            flash(f"Establecimiento '{nombre_est}' creado. Usuario: {nombre_usuario}", "success")

        except Exception as e:
            flash(f"Error: {e}", "danger")

        return redirect(url_for("crear_perfil"))

    return render_template("crear_perfil.html",
                           usuario=session["usuario"])


@app.route("/mi_perfil", methods=["GET", "POST"])
def mi_perfil():
    if not login_requerido():
        return redirect(url_for("login"))

    es_daem = session["usuario"].lower() == "admin_daem"
    id_est = session["id_establecimiento"]

    if request.method == "POST":
        campo = request.form.get("campo", "").strip()
        valor = request.form.get("valor", "").strip()
        clavenueva = request.form.get("clavenueva", "").strip()
        try:
            conn = obtener_conexion()
            cur = conn.cursor()
            if campo == "nombre_completo":
                cur.execute("UPDATE Usuario SET nombre_completo=%s WHERE id_usuario=%s",
                            (valor if valor else None, session["id_usuario"]))
                if valor:
                    session["nombre_display"] = valor
            elif campo == "celular":
                cur.execute("UPDATE Usuario SET celular=%s WHERE id_usuario=%s",
                            (valor if valor else None, session["id_usuario"]))
            elif campo == "correo":
                cur.execute("UPDATE Usuario SET correo=%s WHERE id_usuario=%s",
                            (valor if valor else None, session["id_usuario"]))
            elif campo == "direccion":
                cur.execute("UPDATE Usuario SET direccion=%s WHERE id_usuario=%s",
                            (valor if valor else None, session["id_usuario"]))
            elif campo == "clave":
                if clavenueva:
                    nuevo_hash = hashlib.sha256(clavenueva.encode()).hexdigest()
                    cur.execute("UPDATE Usuario SET clave_hash=%s, clave_plana=%s WHERE id_usuario=%s",
                                (nuevo_hash, clavenueva, session["id_usuario"]))
            else:
                flash("Campo no valido.", "warning")
                return redirect(url_for("mi_perfil"))
            conn.commit()
            conn.close()
            flash("Dato actualizado.", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        return redirect(url_for("mi_perfil"))

    perfil = {
        "usuario": session["usuario"],
    }
    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute("SELECT nombre FROM Establecimiento WHERE id_establecimiento = %s", (id_est,))
        row = cur.fetchone()
        perfil["establecimiento"] = row[0] if row else "DAEM"
        cur.execute(
            "SELECT nombre_completo, celular, correo, direccion, clave_plana FROM Usuario "
            "WHERE id_usuario = %s",
            (session["id_usuario"],)
        )
        perfil.update(dict(zip(["nombre_completo", "celular", "correo", "direccion", "clave_plana"], cur.fetchone())))
        conn.close()
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return render_template("mi_perfil.html",
                           usuario=session["usuario"],
                           es_daem=es_daem,
                           perfil=perfil)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
