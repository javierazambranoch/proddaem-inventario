import tkinter as tk
from tkinter import ttk, messagebox

from database.conexion import obtener_conexion


def crear_modulo_solicitud(
    area_contenido,
    id_usuario,
    id_establecimiento,
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

    print("MÓDULO SOLICITUD ABIERTO")
    print("ID USUARIO:", id_usuario)
    print("ID ESTABLECIMIENTO:", id_establecimiento)
    print("ES DAEM:", es_daem)


    tk.Label(
        area_contenido,
        text="Solicitudes DAEM" if es_daem else "Nueva solicitud",
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
            text="Ver solicitudes de:",
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

            cargar_solicitudes()

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
            text="Buscar producto:",
            bg="white",
            font=("Arial", 10, "bold")
        ).pack(
            side="left",
            padx=(0, 10)
        )

        entry_buscar = tk.Entry(
            panel_buscar,
            width=30,
            font=("Arial", 10)
        )

        entry_buscar.pack(
            side="left"
        )

        def buscar_producto(event=None):

            texto = entry_buscar.get().strip()

            if not texto:

                cargar_solicitudes()

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
                            id_solicitud,
                            nombre_producto,
                            cantidad,
                            prioridad,
                            estado
                        FROM solicitud
                        WHERE nombre_producto ILIKE %s
                        ORDER BY fecha_solicitud DESC
                        """,
                        (f"%{texto}%",)
                    )

                else:

                    cursor.execute(
                        """
                        SELECT
                            id_solicitud,
                            nombre_producto,
                            cantidad,
                            prioridad,
                            estado
                        FROM solicitud
                        WHERE nombre_producto ILIKE %s
                          AND id_establecimiento = %s
                        ORDER BY fecha_solicitud DESC
                        """,
                        (f"%{texto}%", est_actual)
                    )

                resultados = cursor.fetchall()

                for fila in resultados:

                    tabla.insert(
                        "",
                        "end",
                        values=fila
                    )

                if len(resultados) == 0:

                    messagebox.showinfo(
                        "Sin resultados",
                        f"No se encontraron solicitudes con '{texto}'."
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
            command=buscar_producto,
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

        entry_buscar.bind(
            "<Return>",
            buscar_producto
        )

    else:


        form = tk.Frame(
            area_contenido,
            bg="white",
            padx=15,
            pady=10
        )

        form.pack(
            fill="x"
        )

        # PRODUCTO
        tk.Label(form, text="Producto:", bg="white", font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        entry_producto = tk.Entry(form, width=30)
        entry_producto.grid(row=0, column=1, padx=5, pady=5)

        # CANTIDAD
        tk.Label(form, text="Cantidad:", bg="white", font=("Arial", 10)).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        entry_cantidad = tk.Entry(form, width=10)
        entry_cantidad.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # PRIORIDAD
        tk.Label(form, text="Prioridad:", bg="white", font=("Arial", 10)).grid(
            row=1, column=2, sticky="w", padx=5, pady=5
        )
        combo_prioridad = ttk.Combobox(
            form, values=["baja", "media", "alta"],
            state="readonly", width=22
        )
        combo_prioridad.grid(row=1, column=3, padx=5, pady=5)
        combo_prioridad.set("media")

        # CARACTERÍSTICAS
        tk.Label(form, text="Características:", bg="white", font=("Arial", 10)).grid(
            row=2, column=0, sticky="nw", padx=5, pady=5
        )
        entry_caracteristicas = tk.Entry(form, width=65)
        entry_caracteristicas.grid(row=2, column=1, columnspan=3, sticky="we", padx=5, pady=5)

        # DESCRIPCIÓN
        tk.Label(form, text="Descripción / motivo:", bg="white", font=("Arial", 10)).grid(
            row=3, column=0, sticky="nw", padx=5, pady=5
        )
        texto_descripcion = tk.Text(form, width=65, height=4)
        texto_descripcion.grid(row=3, column=1, columnspan=3, sticky="we", padx=5, pady=5)

        def limpiar_campos():
            entry_producto.delete(0, tk.END)
            entry_cantidad.delete(0, tk.END)
            combo_prioridad.set("media")
            entry_caracteristicas.delete(0, tk.END)
            texto_descripcion.delete("1.0", tk.END)
            tabla.selection_remove(tabla.selection())
            entry_producto.focus()

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

            id_solicitud = valores[0]
            producto = valores[1] if len(valores) > 1 else ""

            confirmar = messagebox.askyesno(
                "Eliminar solicitud",
                f"¿Eliminar solicitud N° {id_solicitud}?\nProducto: {producto}\n\nSe eliminará el registro."
            )
            if not confirmar:
                return

            conexion = None
            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor()
                cursor.execute(
                    "DELETE FROM solicitud WHERE id_solicitud = %s AND id_usuario = %s AND id_establecimiento = %s",
                    (id_solicitud, id_usuario, id_establecimiento)
                )
                if cursor.rowcount == 0:
                    messagebox.showwarning("No encontrado", "No se encontró la solicitud.")
                    return
                conexion.commit()
                messagebox.showinfo("Eliminada", f"Solicitud N° {id_solicitud} eliminada.")
                cargar_solicitudes()
                limpiar_campos()
                try:
                    from database.conexion import registrar_historial
                    registrar_historial(id_usuario, f"Eliminación de solicitud N° {id_solicitud}")
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

        def guardar_solicitud():
            producto = entry_producto.get().strip()
            cantidad = entry_cantidad.get().strip()
            prioridad = combo_prioridad.get().strip()
            caracteristicas = entry_caracteristicas.get().strip()
            descripcion = texto_descripcion.get("1.0", tk.END).strip()

            if not producto:
                messagebox.showwarning("Campo obligatorio", "Ingresa el nombre del producto.")
                entry_producto.focus(); return
            if not cantidad:
                messagebox.showwarning("Campo obligatorio", "Ingresa la cantidad.")
                entry_cantidad.focus(); return
            try:
                cantidad_numero = int(cantidad)
                if cantidad_numero <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Cantidad inválida", "La cantidad debe ser un número entero mayor que 0.")
                entry_cantidad.focus(); return
            if not prioridad:
                messagebox.showwarning("Campo obligatorio", "Selecciona una prioridad.")
                combo_prioridad.focus(); return
            if not descripcion:
                messagebox.showwarning("Campo obligatorio", "Ingresa el motivo.")
                texto_descripcion.focus(); return

            conexion = None
            try:
                conexion = obtener_conexion()
                cursor = conexion.cursor()
                cursor.execute(
                    """INSERT INTO solicitud
                    (nombre_producto, nro_serie, cantidad, caracteristicas,
                     estado, descripcion, prioridad, id_usuario, id_establecimiento)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (producto, None, cantidad_numero,
                     caracteristicas if caracteristicas else None,
                     "pendiente", descripcion, prioridad,
                     id_usuario, id_establecimiento)
                )
                conexion.commit()
                messagebox.showinfo("Enviada", "Solicitud registrada correctamente.\nEstado: Pendiente")
                limpiar_campos()
                cargar_solicitudes()
                try:
                    from database.conexion import registrar_historial
                    registrar_historial(
                        id_usuario,
                        f"Envío de solicitud: '{producto}' (cantidad: {cantidad_numero}, prioridad: {prioridad})"
                    )
                except Exception as eh:
                    print("ERROR HISTORIAL:", eh)
            except Exception as e:
                if conexion:
                    conexion.rollback()
                print("ERROR AL GUARDAR:", e)
                messagebox.showerror("Error", f"No se pudo registrar:\n\n{e}")
            finally:
                if conexion:
                    conexion.close()

        # BOTONES
        botones = tk.Frame(form, bg="white")
        botones.grid(row=4, column=0, columnspan=4, pady=10, sticky="w")

        tk.Button(botones, text="Enviar solicitud", command=guardar_solicitud,
                  bg="#27ae60", fg="white", font=("Arial", 10, "bold"),
                  padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(botones, text="Limpiar", command=limpiar_formulario,
                  bg="#7f8c8d", fg="white", font=("Arial", 10, "bold"),
                  padx=15, pady=8).pack(side="left", padx=5)
        tk.Button(botones, text="Actualizar", command=lambda: cargar_solicitudes(),
                  bg="#2980b9", fg="white", font=("Arial", 10, "bold"),
                  padx=15, pady=8).pack(side="left", padx=5)


    tk.Label(
        area_contenido,
        text="Solicitudes de este establecimiento" if es_daem else "Mis solicitudes",
        font=("Arial", 14, "bold"),
        bg="white",
        fg="#2c3e50"
    ).pack(
        anchor="w",
        padx=15,
        pady=(5, 5)
    )

    columnas = (
        "id", "producto", "cantidad", "prioridad", "estado"
    )

    tabla = ttk.Treeview(
        area_contenido,
        columns=columnas,
        show="headings",
        height=10
    )

    tabla.heading("id", text="Nº")
    tabla.heading("producto", text="Producto")
    tabla.heading("cantidad", text="Cantidad")
    tabla.heading("prioridad", text="Prioridad")
    tabla.heading("estado", text="Estado")

    tabla.column("id", width=50)
    tabla.column("producto", width=200)
    tabla.column("cantidad", width=80)
    tabla.column("prioridad", width=100)
    tabla.column("estado", width=120)

    tabla.pack(
        fill="both", expand=True,
        padx=15, pady=5
    )


    if es_daem:

        panel_estado = tk.Frame(
            area_contenido,
            bg="#f0f0f0",
            padx=10,
            pady=8
        )

        panel_estado.pack(
            fill="x",
            padx=15,
            pady=(0, 5)
        )

        tk.Label(
            panel_estado,
            text="Cambiar estado:",
            bg="#f0f0f0",
            font=("Arial", 10, "bold"),
            fg="#2c3e50"
        ).pack(
            side="left",
            padx=(0, 10)
        )

        combo_nuevo_estado = ttk.Combobox(
            panel_estado,
            values=["pendiente", "en proceso", "completada", "rechazada"],
            state="readonly",
            width=15
        )

        combo_nuevo_estado.set("en proceso")

        combo_nuevo_estado.pack(
            side="left"
        )

        def cambiar_estado():

            seleccion = tabla.selection()

            if not seleccion:

                messagebox.showwarning(
                    "Sin selección",
                    "Selecciona una solicitud de la tabla."
                )

                return

            nuevo_estado = combo_nuevo_estado.get().strip()

            if not nuevo_estado:

                return

            item = tabla.item(seleccion[0])
            valores = item.get("values", [])

            if not valores:

                return

            id_solicitud = valores[0]
            producto = valores[1] if len(valores) > 1 else ""

            confirmar = messagebox.askyesno(
                "Cambiar estado",
                f"Solicitud N° {id_solicitud}\n"
                f"Producto: {producto}\n"
                f"Nuevo estado: {nuevo_estado}\n\n"
                f"¿Confirmar cambio?"
            )

            if not confirmar:

                return

            conexion = None

            try:

                conexion = obtener_conexion()
                cursor = conexion.cursor()

                cursor.execute(
                    "UPDATE solicitud SET estado = %s WHERE id_solicitud = %s",
                    (nuevo_estado, id_solicitud)
                )

                conexion.commit()

                messagebox.showinfo(
                    "Actualizado",
                    f"Solicitud N° {id_solicitud} → {nuevo_estado}"
                )

                cargar_solicitudes()

                try:

                    from database.conexion import registrar_historial

                    registrar_historial(
                        id_usuario,
                        f"Cambio estado solicitud N° {id_solicitud} '{producto}' → {nuevo_estado}"
                    )

                except Exception as eh:

                    print("ERROR HISTORIAL:", eh)

            except Exception as e:

                if conexion:

                    conexion.rollback()

                print("ERROR AL CAMBIAR ESTADO:", e)

                messagebox.showerror(
                    "Error",
                    f"No se pudo cambiar el estado:\n\n{e}"
                )

            finally:

                if conexion:

                    conexion.close()

        btn_estado = tk.Button(
            panel_estado,
            text="Cambiar estado",
            command=cambiar_estado,
            bg="#e67e22",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=6,
            cursor="hand2"
        )

        btn_estado.pack(
            side="left",
            padx=(10, 0)
        )


    def cargar_solicitudes():

        for fila in tabla.get_children():
            tabla.delete(fila)

        conexion = None

        try:

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            est_actual = establecimiento_seleccionado.get()

            if es_daem and est_actual == 0:

                cursor.execute(
                    """SELECT id_solicitud, nombre_producto, cantidad, prioridad, estado
                    FROM solicitud
                    ORDER BY fecha_solicitud DESC"""
                )

            elif es_daem:

                cursor.execute(
                    """SELECT id_solicitud, nombre_producto, cantidad, prioridad, estado
                    FROM solicitud
                    WHERE id_establecimiento = %s
                    ORDER BY fecha_solicitud DESC""",
                    (est_actual,)
                )

            else:

                cursor.execute(
                    """SELECT id_solicitud, nombre_producto, cantidad, prioridad, estado
                    FROM solicitud
                    WHERE id_usuario = %s AND id_establecimiento = %s
                    ORDER BY fecha_solicitud DESC""",
                    (id_usuario, id_establecimiento)
                )

            resultados = cursor.fetchall()

            for fila in resultados:

                tabla.insert("", "end", values=fila)

            print("Solicitudes cargadas:", len(resultados))

        except Exception as e:

            print("ERROR AL CARGAR SOLICITUDES:", e)

            messagebox.showerror(
                "Error",
                f"No se pudieron cargar las solicitudes:\n\n{e}"
            )

        finally:

            if conexion:
                conexion.close()


    cargar_solicitudes()

    if not es_daem:
        entry_producto.focus()
