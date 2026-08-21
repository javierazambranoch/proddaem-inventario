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
    "Liceo Municipal": 4,
    "Escuela Canada": 2
}

NOMBRES_DISPLAY = {
    "admin_liceo": "Victor Pinto",
    "admin_saber": "Victor Pinto"
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
                "SELECT id_usuario, id_establecimiento FROM Usuario "
                "WHERE nombre_usuario = %s AND clave_hash = %s",
                (nombre, clave_hash)
            )
            resultado = cur.fetchone()
            conn.close()

            if resultado:
                session["usuario"] = nombre
                session["id_usuario"] = resultado[0]
                session["id_establecimiento"] = resultado[1]
                session["nombre_display"] = NOMBRES_DISPLAY.get(nombre, nombre)
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
    notificaciones = []
    solicitudes_pendientes = 0

    try:
        conn = obtener_conexion()
        cur = conn.cursor()

        if not es_daem:
            id_est = session["id_establecimiento"]

            cur.execute(
                "SELECT COUNT(*) FROM solicitud WHERE id_establecimiento = %s AND estado = 'pendiente'",
                (id_est,)
            )
            solicitudes_pendientes = cur.fetchone()[0]

            cur.execute(
                "SELECT h.accion, h.fecha_hora, u.nombre_usuario "
                "FROM Historial h JOIN Usuario u ON h.id_usuario = u.id_usuario "
                "WHERE u.id_establecimiento = %s "
                "ORDER BY h.fecha_hora DESC LIMIT 10",
                (id_est,)
            )
            notificaciones = cur.fetchall()

        conn.close()
    except Exception as e:
        print("ERROR NOTIFICACIONES:", e)

    return render_template("dashboard.html",
                           usuario=session["usuario"],
                           nombre_display=nombre_display,
                           es_daem=es_daem,
                           notificaciones=notificaciones,
                           solicitudes_pendientes=solicitudes_pendientes)


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
                    "SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada "
                    "FROM Computador WHERE codigo ILIKE %s ORDER BY fecha_registro DESC",
                    (f"%{buscar}%",)
                )
            else:
                cur.execute(
                    "SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada "
                    "FROM Computador WHERE codigo ILIKE %s AND id_establecimiento = %s "
                    "ORDER BY fecha_registro DESC",
                    (f"%{buscar}%", est_filtro)
                )
        elif es_daem:
            if est_filtro == "0":
                cur.execute(
                    "SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada "
                    "FROM Computador ORDER BY fecha_registro DESC"
                )
            else:
                cur.execute(
                    "SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada "
                    "FROM Computador WHERE id_establecimiento = %s ORDER BY fecha_registro DESC",
                    (est_filtro,)
                )
        else:
            cur.execute(
                "SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada "
                "FROM Computador WHERE id_establecimiento = %s ORDER BY fecha_registro DESC",
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
    condicion = request.form.get("condicion", "").strip()
    est_filtro = request.form.get("est_filtro", str(session["id_establecimiento"]))

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
             descripcion_condicion, ubicacion_asignada, id_establecimiento)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (codigo, categoria, marca, modelo, estado,
             condicion if condicion else None, ubicacion, id_establecimiento)
        )

        solicitud_creada = False
        if estado in ("regular", "malo"):
            tipo = "mantencion" if estado == "regular" else "reposicion"
            prioridad = "media" if estado == "regular" else "alta"
            nombre_prod = f"{tipo.capitalize()} - {categoria} {marca} {modelo}"
            caracts = f"Código: {codigo} | Marca: {marca} | Modelo: {modelo} | Ubicación: {ubicacion}"
            desc = f"Solicitud automática desde Inventario.\nEquipo: {codigo}\nEstado: {estado}\nCondición: {condicion}"
            cur.execute(
                """INSERT INTO solicitud
                (nombre_producto, nro_serie, cantidad, caracteristicas,
                 estado, descripcion, prioridad, id_usuario, id_establecimiento)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (nombre_prod, codigo, 1, caracts, "pendiente", desc, prioridad, id_usuario, id_establecimiento)
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

    categoria = request.form.get("categoria", "").strip()
    producto = request.form.get("producto", "").strip()
    cantidad = request.form.get("cantidad", "").strip()
    prioridad = request.form.get("prioridad", "media").strip()
    caracteristicas = request.form.get("caracteristicas", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    if not producto or not cantidad or not descripcion or not categoria:
        flash("Producto, categoría, cantidad y descripción son obligatorios.", "warning")
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
             estado, descripcion, prioridad, id_usuario, id_establecimiento)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (producto, categoria, cantidad_num,
             caracteristicas if caracteristicas else None,
             "pendiente", descripcion, prioridad, id_usuario, id_est)
        )
        conn.commit()
        conn.close()

        registrar_historial(id_usuario, f"Envío de solicitud: '{producto}' (cantidad: {cantidad_num})")
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

    nuevo_estado = request.form.get("nuevo_estado", "").strip()
    est_filtro = request.form.get("est_filtro", "0")

    if not nuevo_estado:
        flash("Selecciona un estado.", "warning")
        return redirect(url_for("solicitudes", establecimiento=est_filtro))

    try:
        conn = obtener_conexion()
        cur = conn.cursor()
        cur.execute(
            "UPDATE solicitud SET estado = %s WHERE id_solicitud = %s",
            (nuevo_estado, id_solicitud)
        )
        conn.commit()
        conn.close()

        registrar_historial(
            session["id_usuario"],
            f"Cambio estado solicitud N° {id_solicitud} -> {nuevo_estado}"
        )
        flash(f"Solicitud N° {id_solicitud} -> {nuevo_estado}", "success")

    except Exception as e:
        flash(f"Error al cambiar estado: {e}", "danger")

    return redirect(url_for("solicitudes", establecimiento=est_filtro))


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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
