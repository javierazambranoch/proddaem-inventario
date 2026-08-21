import tkinter as tk
from tkinter import ttk, messagebox

from database.conexion import obtener_conexion


def crear_modulo_historial(
    area_contenido,
    id_usuario,
    id_establecimiento,
    nombre_usuario
):

    es_daem = nombre_usuario.lower() == "admin_daem"

    print("========================================")
    print("MÓDULO HISTORIAL ABIERTO")
    print("ID USUARIO:", id_usuario)
    print("ID ESTABLECIMIENTO:", id_establecimiento)
    print("USUARIO:", nombre_usuario)
    print("ES DAEM:", es_daem)
    print("========================================")


    contenedor = tk.Frame(
        area_contenido,
        bg="white"
    )

    contenedor.pack(
        fill="both",
        expand=True
    )


    tk.Label(
        contenedor,
        text="Historial",
        font=("Arial", 20, "bold"),
        bg="white",
        fg="#2c3e50"
    ).pack(
        pady=(15, 5)
    )

    tk.Label(
        contenedor,
        text="Registro de actividades realizadas en el sistema",
        font=("Arial", 10),
        bg="white",
        fg="#7f8c8d"
    ).pack(
        pady=(0, 10)
    )


    panel_filtros = tk.LabelFrame(
        contenedor,
        text=" Filtros ",
        bg="white",
        fg="#2c3e50",
        font=("Arial", 10, "bold"),
        padx=10,
        pady=10
    )

    panel_filtros.pack(
        fill="x",
        padx=15,
        pady=5
    )

    tk.Label(
        panel_filtros,
        text="Mostrar:",
        bg="white",
        font=("Arial", 10)
    ).grid(
        row=0,
        column=0,
        padx=5,
        pady=5
    )

    combo_filtro = ttk.Combobox(
        panel_filtros,
        values=[
            "Todos",
            "Mis actividades"
        ] if es_daem else [
            "Mis actividades"
        ],
        state="readonly",
        width=20
    )

    combo_filtro.set(
        "Todos" if es_daem else "Mis actividades"
    )

    combo_filtro.grid(
        row=0,
        column=1,
        padx=5,
        pady=5
    )


    marco_tabla = tk.Frame(
        contenedor,
        bg="white"
    )

    marco_tabla.pack(
        fill="both",
        expand=True,
        padx=15,
        pady=10
    )

    columnas = (
        "id",
        "usuario",
        "accion",
        "fecha"
    )

    tabla = ttk.Treeview(
        marco_tabla,
        columns=columnas,
        show="headings"
    )


    tabla.heading(
        "id",
        text="ID"
    )

    tabla.heading(
        "usuario",
        text="Usuario"
    )

    tabla.heading(
        "accion",
        text="Acción realizada"
    )

    tabla.heading(
        "fecha",
        text="Fecha / Hora"
    )


    tabla.column(
        "id",
        width=70,
        anchor="center"
    )

    tabla.column(
        "usuario",
        width=120,
        anchor="center"
    )

    tabla.column(
        "accion",
        width=450
    )

    tabla.column(
        "fecha",
        width=180,
        anchor="center"
    )


    scrollbar = ttk.Scrollbar(
        marco_tabla,
        orient="vertical",
        command=tabla.yview
    )

    tabla.configure(
        yscrollcommand=scrollbar.set
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    tabla.pack(
        side="left",
        fill="both",
        expand=True
    )


    label_total = tk.Label(
        contenedor,
        text="Total de registros: 0",
        bg="white",
        fg="#2c3e50",
        font=("Arial", 10, "bold")
    )

    label_total.pack(
        anchor="w",
        padx=15,
        pady=(0, 10)
    )


    def cargar_historial():

        # Limpiar tabla

        for fila in tabla.get_children():
            tabla.delete(fila)

        conexion = None

        try:

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            filtro = combo_filtro.get()


            if filtro == "Todos":

                cursor.execute(
                    """
                    SELECT
                        id_historial,
                        id_usuario,
                        accion,
                        fecha_hora
                    FROM historial
                    ORDER BY fecha_hora DESC
                    """
                )


            else:

                cursor.execute(
                    """
                    SELECT
                        id_historial,
                        id_usuario,
                        accion,
                        fecha_hora
                    FROM historial
                    WHERE id_usuario = %s
                    ORDER BY fecha_hora DESC
                    """,
                    (
                        id_usuario,
                    )
                )

            resultados = cursor.fetchall()


            for fila in resultados:

                id_historial = fila[0]
                usuario = fila[1]
                accion = fila[2]
                fecha_hora = fila[3]

                tabla.insert(
                    "",
                    "end",
                    values=(
                        id_historial,
                        usuario,
                        accion,
                        fecha_hora
                    )
                )


            label_total.config(
                text=f"Total de registros: {len(resultados)}"
            )

            print(
                "Historial cargado:",
                len(resultados),
                "registros"
            )

        except Exception as e:

            print(
                "ERROR AL CARGAR HISTORIAL:",
                e
            )

            messagebox.showerror(
                "Error de historial",
                f"No se pudo cargar el historial:\n\n{e}"
            )

        finally:

            if conexion:
                conexion.close()


    def actualizar():

        cargar_historial()

    boton_actualizar = tk.Button(
        panel_filtros,
        text="Actualizar",
        command=actualizar,
        bg="#2980b9",
        fg="white",
        font=("Arial", 10, "bold"),
        padx=15,
        pady=6
    )

    boton_actualizar.grid(
        row=0,
        column=2,
        padx=5,
        pady=5
    )


    def limpiar_filtro():

        combo_filtro.set(
            "Todos" if es_daem else "Mis actividades"
        )

        cargar_historial()

    boton_limpiar = tk.Button(
        panel_filtros,
        text="Limpiar filtro",
        command=limpiar_filtro,
        bg="#7f8c8d",
        fg="white",
        font=("Arial", 10, "bold"),
        padx=15,
        pady=6
    )

    boton_limpiar.grid(
        row=0,
        column=3,
        padx=5,
        pady=5
    )


    def mostrar_detalle(event=None):

        seleccion = tabla.selection()

        if not seleccion:
            return

        item = tabla.item(
            seleccion[0]
        )

        valores = item.get(
            "values",
            []
        )

        if not valores:
            return

        id_historial = valores[0]
        usuario = valores[1]
        accion = valores[2]
        fecha = valores[3]

        mensaje = (
            f"ID historial:\n{id_historial}\n\n"
            f"ID usuario:\n{usuario}\n\n"
            f"Acción realizada:\n{accion}\n\n"
            f"Fecha y hora:\n{fecha}"
        )

        messagebox.showinfo(
            "Detalle del historial",
            mensaje
        )

    tabla.bind(
        "<Double-1>",
        mostrar_detalle
    )


    combo_filtro.bind(
        "<<ComboboxSelected>>",
        lambda event: cargar_historial()
    )


    cargar_historial()