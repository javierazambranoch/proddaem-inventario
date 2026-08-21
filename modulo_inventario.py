import tkinter as tk
from tkinter import ttk, messagebox

from database.conexion import obtener_conexion


def crear_modulo_inventario(
    area_contenido,
    id_establecimiento,
    id_usuario,
    nombre_usuario=""
):

    es_daem = nombre_usuario.lower() == "admin_daem"

    establecimientos = {
        "Escuela El Saber": 9,
        "Escuela Oscar Guerrero": 3,
        "Liceo Municipal": 4,
        "Escuela Canada": 2
    }

    if es_daem:
        establecimiento_seleccionado = tk.IntVar(value=0)
    else:
        establecimiento_seleccionado = tk.IntVar(value=id_establecimiento)

    print("========================================")
    print("MÓDULO INVENTARIO ABIERTO")
    print("ID ESTABLECIMIENTO:", id_establecimiento)
    print("ID USUARIO:", id_usuario)
    print("ES DAEM:", es_daem)
    print("========================================")


    tk.Label(
        area_contenido,
        text="Inventario DAEM" if es_daem else "Módulo Inventario",
        font=("Arial", 20, "bold"),
        bg="white",
        fg="#2c3e50"
    ).pack(
        pady=(15, 5)
    )


    if es_daem:

        panel_est = tk.Frame(
            area_contenido,
            bg="white"
        )

        panel_est.pack(
            fill="x",
            padx=15,
            pady=5
        )

        tk.Label(
            panel_est,
            text="Establecimiento:",
            bg="white",
            font=("Arial", 11, "bold"),
            fg="#2c3e50"
        ).pack(
            side="left",
            padx=(0, 10)
        )

        combo_est = ttk.Combobox(
            panel_est,
            values=["DAEM (Todos)"] + list(establecimientos.keys()),
            state="readonly",
            width=25
        )

        combo_est.set("DAEM (Todos)")

        combo_est.pack(
            side="left"
        )

        def cambiar_establecimiento(event=None):

            sel = combo_est.get()

            if sel == "DAEM (Todos)":

                establecimiento_seleccionado.set(0)

            elif sel in establecimientos:

                establecimiento_seleccionado.set(
                    establecimientos[sel]
                )

            cargar_tabla()

        combo_est.bind(
            "<<ComboboxSelected>>",
            cambiar_establecimiento
        )


    if es_daem:

        panel_buscar = tk.Frame(
            area_contenido,
            bg="white"
        )

        panel_buscar.pack(
            fill="x",
            padx=15,
            pady=5
        )

        tk.Label(
            panel_buscar,
            text="Buscar por código:",
            bg="white",
            font=("Arial", 10, "bold")
        ).pack(
            side="left",
            padx=(0, 10)
        )

        entry_codigo = tk.Entry(
            panel_buscar,
            width=30,
            font=("Arial", 10)
        )

        entry_codigo.pack(
            side="left"
        )

        def buscar_por_codigo(event=None):

            codigo_buscar = entry_codigo.get().strip()

            if not codigo_buscar:

                cargar_tabla()

                return

            for fila in tabla.get_children():

                tabla.delete(fila)

            conexion = None

            try:

                conexion = obtener_conexion()
                cursor = conexion.cursor()

                est_actual = establecimiento_seleccionado.get()

                if est_actual == 0:

                    cursor.execute(
                        """
                        SELECT
                            codigo,
                            categoria,
                            marca,
                            modelo,
                            estado,
                            ubicacion_asignada
                        FROM Computador
                        WHERE codigo ILIKE %s
                        ORDER BY fecha_registro DESC
                        """,
                        (f"%{codigo_buscar}%",)
                    )

                else:

                    cursor.execute(
                        """
                        SELECT
                            codigo,
                            categoria,
                            marca,
                            modelo,
                            estado,
                            ubicacion_asignada
                        FROM Computador
                        WHERE codigo ILIKE %s
                          AND id_establecimiento = %s
                        ORDER BY fecha_registro DESC
                        """,
                        (f"%{codigo_buscar}%", est_actual)
                    )

                resultados = cursor.fetchall()

                for fila in resultados:

                    tabla.insert(
                        "",
                        "end",
                        values=fila
                    )

                label_total.config(
                    text=f"Resultados: {len(resultados)}"
                )

                if len(resultados) == 0:

                    messagebox.showinfo(
                        "Sin resultados",
                        f"No se encontraron equipos con '{codigo_buscar}'."
                    )

            except Exception as e:

                print("ERROR AL BUSCAR:", e)

                messagebox.showerror(
                    "Error",
                    f"No se pudo buscar:\n\n{e}"
                )

            finally:

                if conexion:

                    conexion.close()

        btn_buscar = tk.Button(
            panel_buscar,
            text="Buscar",
            command=buscar_por_codigo,
            bg="#2980b9",
            fg="white",
            font=("Arial", 9, "bold"),
            padx=12,
            pady=4,
            cursor="hand2"
        )

        btn_buscar.pack(
            side="left",
            padx=(10, 0)
        )

        entry_codigo.bind(
            "<Return>",
            buscar_por_codigo
        )

    else:


        form = tk.Frame(
            area_contenido,
            bg="white",
            padx=15,
            pady=10
        )

        form.pack(
            fill="x",
            padx=10,
            pady=5
        )

        # CÓDIGO
        tk.Label(form, text="Código:", bg="white", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", padx=5, pady=4
        )
        entry_codigo = tk.Entry(form, width=25)
        entry_codigo.grid(row=0, column=1, padx=5, pady=4)

        # CATEGORÍA
        tk.Label(form, text="Categoría:", bg="white", font=("Arial", 10)).grid(
            row=0, column=2, sticky="w", padx=5, pady=4
        )
        entry_categoria = tk.Entry(form, width=20)
        entry_categoria.grid(row=0, column=3, padx=5, pady=4)

        # MARCA
        tk.Label(form, text="Marca:", bg="white", font=("Arial", 10)).grid(
            row=1, column=0, sticky="w", padx=5, pady=4
        )
        entry_marca = tk.Entry(form, width=25)
        entry_marca.grid(row=1, column=1, padx=5, pady=4)

        # MODELO
        tk.Label(form, text="Modelo:", bg="white", font=("Arial", 10)).grid(
            row=1, column=2, sticky="w", padx=5, pady=4
        )
        entry_modelo = tk.Entry(form, width=20)
        entry_modelo.grid(row=1, column=3, padx=5, pady=4)

        # ESTADO
        tk.Label(form, text="Estado:", bg="white", font=("Arial", 10)).grid(
            row=2, column=0, sticky="w", padx=5, pady=4
        )
        combo_estado = ttk.Combobox(
            form, values=["bueno", "regular", "malo"],
            state="readonly", width=22
        )
        combo_estado.grid(row=2, column=1, padx=5, pady=4)

        # UBICACIÓN
        tk.Label(form, text="Ubicación / Responsable:", bg="white", font=("Arial", 10)).grid(
            row=2, column=2, sticky="w", padx=5, pady=4
        )
        entry_ubicacion = tk.Entry(form, width=20)
        entry_ubicacion.grid(row=2, column=3, padx=5, pady=4)

        # CONDICIÓN (oculta inicialmente)
        label_condicion = tk.Label(form, text="Describir condición:", bg="white", font=("Arial", 10))
        entry_condicion = tk.Entry(form, width=60)

        # SOLICITUD AUTOMÁTICA (oculta inicialmente)
        panel_solicitud = tk.LabelFrame(
            form, text=" Solicitud automática ",
            bg="#f8f9fa", fg="#2c3e50",
            font=("Arial", 10, "bold"), padx=10, pady=10
        )

        tk.Label(panel_solicitud, text="Tipo:", bg="#f8f9fa", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        combo_tipo_solicitud = ttk.Combobox(
            panel_solicitud, values=["mantencion", "reposicion"],
            state="readonly", width=15
        )
        combo_tipo_solicitud.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(panel_solicitud, text="Prioridad:", bg="#f8f9fa", font=("Arial", 10)).grid(
            row=0, column=2, sticky="w", padx=5, pady=5
        )
        combo_prioridad = ttk.Combobox(
            panel_solicitud, values=["baja", "media", "alta"],
            state="readonly", width=12
        )
        combo_prioridad.grid(row=0, column=3, sticky="w", padx=5, pady=5)

        tk.Label(panel_solicitud, text="Motivo:", bg="#f8f9fa", font=("Arial", 10)).grid(
            row=1, column=0, sticky="nw", padx=5, pady=5
        )
        texto_solicitud = tk.Text(panel_solicitud, width=55, height=3, wrap="word")
        texto_solicitud.grid(row=1, column=1, columnspan=3, sticky="we", padx=5, pady=5)

        def ocultar_solicitud():
            label_condicion.grid_forget()
            entry_condicion.grid_forget()
            panel_solicitud.grid_forget()

        def mostrar_solicitud():
            label_condicion.grid(row=3, column=0, sticky="w", padx=5, pady=4)
            entry_condicion.grid(row=3, column=1, columnspan=3, sticky="ew", padx=5, pady=4)
            panel_solicitud.grid(row=4, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
            form.update_idletasks()

        def actualizar_campo_condicion(event=None):
            estado = combo_estado.get().strip().lower()
            ocultar_solicitud()
            combo_tipo_solicitud.set("")
            combo_prioridad.set("")
            texto_solicitud.delete("1.0", tk.END)
            entry_condicion.delete(0, tk.END)

            if estado == "regular":
                mostrar_solicitud()
                combo_tipo_solicitud.set("mantencion")
                combo_prioridad.set("media")
                texto_solicitud.insert("1.0", "El equipo presenta daños o problemas que requieren mantención.")
            elif estado == "malo":
                mostrar_solicitud()
                combo_tipo_solicitud.set("reposicion")
                combo_prioridad.set("alta")
                texto_solicitud.insert("1.0", "El equipo se encuentra fuera de servicio y requiere reposición.")

        combo_estado.bind("<<ComboboxSelected>>", actualizar_campo_condicion)

        def limpiar_campos():
            entry_codigo.delete(0, tk.END)
            entry_categoria.delete(0, tk.END)
            entry_marca.delete(0, tk.END)
            entry_modelo.delete(0, tk.END)
            entry_ubicacion.delete(0, tk.END)
            entry_condicion.delete(0, tk.END)
            combo_estado.set("")
            combo_tipo_solicitud.set("")
            combo_prioridad.set("")
            texto_solicitud.delete("1.0", tk.END)
            ocultar_solicitud()
            tabla.selection_remove(tabla.selection())
            entry_codigo.focus()

        def limpiar_formulario():
            seleccion = tabla.selection()
            if not seleccion:
                limpiar_campos()
                return

            item = tabla.item(seleccion[0])
            valores = item.get("values", [])
            if not valores:
                limpiar_campos()
                return

            codigo = valores[0]
            confirmar = messagebox.askyesno(
                "Eliminar equipo",
                f"¿Eliminar el equipo '{codigo}'?\n\nEsta acción eliminará el registro."
            )
            if not confirmar:
                return

            conexion = None
            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor()
                est_actual = establecimiento_seleccionado.get()
                cursor.execute(
                    "DELETE FROM Computador WHERE codigo = %s AND id_establecimiento = %s",
                    (codigo, est_actual)
                )
                if cursor.rowcount == 0:
                    messagebox.showwarning("No encontrado", f"No se encontró '{codigo}' para eliminar.")
                    return
                conexion.commit()
                messagebox.showinfo("Eliminado", f"Equipo '{codigo}' eliminado correctamente.")
                cargar_tabla()
                limpiar_campos()
                try:
                    from database.conexion import registrar_historial
                    registrar_historial(id_usuario, f"Eliminación de equipo '{codigo}'")
                except Exception as eh:
                    print("ERROR HISTORIAL:", eh)
            except Exception as e:
                if conexion:
                    conexion.rollback()
                print("ERROR AL ELIMINAR:", e)
                messagebox.showerror("Error", f"No se pudo eliminar:\n\n{e}")
            finally:
                if conexion:
                    conexion.close()

        def guardar_computador():
            codigo = entry_codigo.get().strip()
            categoria = entry_categoria.get().strip()
            marca = entry_marca.get().strip()
            modelo = entry_modelo.get().strip()
            estado = combo_estado.get().strip()
            ubicacion = entry_ubicacion.get().strip()
            condicion = entry_condicion.get().strip()
            tipo_solicitud = combo_tipo_solicitud.get().strip()
            prioridad = combo_prioridad.get().strip()
            motivo_solicitud = texto_solicitud.get("1.0", tk.END).strip()

            if not codigo:
                messagebox.showwarning("Campo obligatorio", "Debes ingresar el código.")
                entry_codigo.focus(); return
            if not categoria:
                messagebox.showwarning("Campo obligatorio", "Debes ingresar la categoría.")
                entry_categoria.focus(); return
            if not marca:
                messagebox.showwarning("Campo obligatorio", "Debes ingresar la marca.")
                entry_marca.focus(); return
            if not modelo:
                messagebox.showwarning("Campo obligatorio", "Debes ingresar el modelo.")
                entry_modelo.focus(); return
            if not estado:
                messagebox.showwarning("Campo obligatorio", "Debes seleccionar el estado.")
                combo_estado.focus(); return
            if not ubicacion:
                messagebox.showwarning("Campo obligatorio", "Debes ingresar la ubicación.")
                entry_ubicacion.focus(); return

            if estado in ("regular", "malo"):
                if not condicion:
                    messagebox.showwarning("Campo obligatorio", "Debes describir la condición.")
                    entry_condicion.focus(); return
                if not tipo_solicitud:
                    messagebox.showwarning("Campo obligatorio", "Selecciona el tipo de solicitud.")
                    combo_tipo_solicitud.focus(); return
                if not prioridad:
                    messagebox.showwarning("Campo obligatorio", "Selecciona la prioridad.")
                    combo_prioridad.focus(); return
                if not motivo_solicitud:
                    messagebox.showwarning("Campo obligatorio", "Ingresa el motivo.")
                    texto_solicitud.focus(); return

            conexion = None
            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor()
                est_actual = establecimiento_seleccionado.get()

                cursor.execute(
                    """INSERT INTO Computador
                    (codigo, categoria, marca, modelo, estado,
                     descripcion_condicion, ubicacion_asignada, id_establecimiento)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (codigo, categoria, marca, modelo, estado,
                     condicion if condicion else None, ubicacion, est_actual)
                )

                solicitud_creada = False
                if estado in ("regular", "malo"):
                    nombre_producto = f"{tipo_solicitud.capitalize()} - {categoria} {marca} {modelo}"
                    caracteristicas = f"Código: {codigo} | Marca: {marca} | Modelo: {modelo} | Ubicación: {ubicacion}"
                    desc = (f"Solicitud automática desde Inventario.\n\nEquipo: {codigo}\n"
                            f"Categoría: {categoria}\nMarca: {marca}\nModelo: {modelo}\n"
                            f"Estado: {estado}\nCondición: {condicion}\nUbicación: {ubicacion}\n\n"
                            f"Motivo:\n{motivo_solicitud}")
                    cursor.execute(
                        """INSERT INTO solicitud
                        (nombre_producto, nro_serie, cantidad, caracteristicas,
                         estado, descripcion, prioridad, id_usuario, id_establecimiento)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (nombre_producto, codigo, 1, caracteristicas,
                         "pendiente", desc, prioridad, id_usuario, est_actual)
                    )
                    solicitud_creada = True

                conexion.commit()

                if solicitud_creada:
                    messagebox.showinfo("Registrado", f"Equipo '{codigo}' registrado.\nSolicitud automática de {tipo_solicitud} creada.")
                else:
                    messagebox.showinfo("Registrado", f"Equipo '{codigo}' registrado correctamente.")

                limpiar_campos()
                cargar_tabla()

                try:
                    from database.conexion import registrar_historial
                    accion = f"Registro de equipo '{codigo}' ({categoria} {marca} {modelo}, estado: {estado})"
                    if solicitud_creada:
                        accion += f" - Solicitud automática de {tipo_solicitud}"
                    registrar_historial(id_usuario, accion)
                except Exception as eh:
                    print("ERROR HISTORIAL:", eh)

            except Exception as e:
                if conexion:
                    conexion.rollback()
                error = str(e).lower()
                if "duplicate key" in error:
                    messagebox.showerror("Duplicado", f"El código '{codigo}' ya existe.")
                else:
                    messagebox.showerror("Error", f"No se pudo guardar:\n\n{e}")
            finally:
                if conexion:
                    conexion.close()

        # BOTONES
        botones = tk.Frame(form, bg="white")
        botones.grid(row=5, column=0, columnspan=4, pady=10, sticky="w")

        tk.Button(botones, text="Guardar equipo", command=guardar_computador,
                  bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                  padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(botones, text="Limpiar", command=limpiar_formulario,
                  bg="#7f8c8d", fg="white", font=("Arial", 10, "bold"),
                  padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(botones, text="Actualizar", command=lambda: cargar_tabla(),
                  bg="#2980b9", fg="white", font=("Arial", 10, "bold"),
                  padx=15, pady=8).pack(side="left", padx=5)

        ocultar_solicitud()


    columnas = (
        "codigo", "categoria", "marca",
        "modelo", "estado", "ubicacion"
    )

    tabla = ttk.Treeview(
        area_contenido,
        columns=columnas,
        show="headings",
        height=15 if es_daem else 12
    )

    tabla.heading("codigo", text="Código")
    tabla.heading("categoria", text="Categoría")
    tabla.heading("marca", text="Marca")
    tabla.heading("modelo", text="Modelo")
    tabla.heading("estado", text="Estado")
    tabla.heading("ubicacion", text="Ubicación / Responsable")

    tabla.column("codigo", width=110)
    tabla.column("categoria", width=120)
    tabla.column("marca", width=120)
    tabla.column("modelo", width=120)
    tabla.column("estado", width=100)
    tabla.column("ubicacion", width=180)

    tabla.pack(
        fill="both", expand=True,
        padx=15, pady=10
    )


    label_total = tk.Label(
        area_contenido,
        text="Total: 0",
        bg="white", fg="#2c3e50",
        font=("Arial", 10, "bold")
    )

    label_total.pack(
        anchor="w", padx=15, pady=(0, 10)
    )


    def cargar_tabla():

        for fila in tabla.get_children():
            tabla.delete(fila)

        conexion = None

        try:

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            est_actual = establecimiento_seleccionado.get()

            if es_daem and est_actual == 0:

                cursor.execute(
                    """SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada
                    FROM Computador
                    ORDER BY fecha_registro DESC"""
                )

            else:

                cursor.execute(
                    """SELECT codigo, categoria, marca, modelo, estado, ubicacion_asignada
                    FROM Computador
                    WHERE id_establecimiento = %s
                    ORDER BY fecha_registro DESC""",
                    (est_actual,)
                )

            resultados = cursor.fetchall()

            for fila in resultados:

                tabla.insert("", "end", values=fila)

            label_total.config(text=f"Total: {len(resultados)}")

            print("Inventario cargado:", len(resultados), "registros")

        except Exception as e:

            print("ERROR AL CARGAR INVENTARIO:", e)

            messagebox.showerror(
                "Error",
                f"No se pudo cargar el inventario:\n\n{e}"
            )

        finally:

            if conexion:
                conexion.close()


    cargar_tabla()

    if not es_daem:
        entry_codigo.focus()
