import tkinter as tk
from tkinter import messagebox


def crear_ventana_principal(
    ventana,
    id_usuario,
    id_establecimiento,
    nombre_usuario
):
    ventana.title(f"Inventario DAEM - {nombre_usuario}")
    ventana.geometry("800x500")
    ventana.minsize(700, 450)


    panel_lateral = tk.Frame(
        ventana,
        bg="#2c3e50",
        width=180
    )

    panel_lateral.pack(
        side="left",
        fill="y"
    )

    # Evita que el panel cambie de tamaño
    panel_lateral.pack_propagate(False)


    area_contenido = tk.Frame(
        ventana,
        bg="white"
    )

    area_contenido.pack(
        side="right",
        fill="both",
        expand=True
    )


    tk.Label(
        panel_lateral,
        text="INVENTARIO DAEM",
        bg="#2c3e50",
        fg="white",
        font=("Arial", 13, "bold"),
        pady=20
    ).pack(
        fill="x"
    )


    tk.Label(
        panel_lateral,
        text=nombre_usuario,
        bg="#2c3e50",
        fg="#ecf0f1",
        font=("Arial", 10),
        wraplength=160
    ).pack(
        fill="x",
        pady=(0, 20)
    )


    def limpiar_contenido():

        for widget in area_contenido.winfo_children():
            widget.destroy()


    def mostrar_inventario():

        limpiar_contenido()

        try:

            from modulo_inventario import crear_modulo_inventario

            crear_modulo_inventario(
                area_contenido,
                id_establecimiento,
                id_usuario,
                nombre_usuario
            )

        except Exception as e:

            import traceback

            print(
                "\n========== ERROR MODULO INVENTARIO =========="
            )

            traceback.print_exc()

            print(
                "=============================================\n"
            )

            messagebox.showerror(
                "Error en Inventario",
                "No se pudo cargar el módulo Inventario.\n\n"
                f"Detalle del error:\n{e}"
            )


    def mostrar_solicitar():

        limpiar_contenido()

        try:

            from modulo_solicitud import crear_modulo_solicitud

            crear_modulo_solicitud(
                area_contenido,
                id_usuario,
                id_establecimiento,
                nombre_usuario
            )

        except Exception as e:

            import traceback

            print(
                "\n========== ERROR MODULO SOLICITUD =========="
            )

            traceback.print_exc()

            print(
                "============================================\n"
            )

            messagebox.showerror(
                "Error en Solicitudes",
                "No se pudo cargar el módulo Solicitar.\n\n"
                f"Detalle del error:\n{e}"
            )


    def mostrar_historial():

        limpiar_contenido()

        try:

            from modulo_historial import crear_modulo_historial

            crear_modulo_historial(
                area_contenido,
                id_usuario,
                id_establecimiento,
                nombre_usuario
            )

        except Exception as e:

            import traceback

            print(
                "\n========== ERROR MODULO HISTORIAL =========="
            )

            traceback.print_exc()

            print(
                "============================================\n"
            )

            messagebox.showerror(
                "Error en Historial",
                "No se pudo cargar el módulo Historial.\n\n"
                f"Detalle del error:\n{e}"
            )


    def cambiar_perfil():

        respuesta = messagebox.askyesno(
            "Cambiar perfil",
            "¿Deseas cerrar la sesión y volver al inicio de sesión?"
        )

        if respuesta:

            try:

                import main

                main.mostrar_login(ventana)

            except Exception as e:

                messagebox.showerror(
                    "Error",
                    f"No se pudo volver al inicio de sesión:\n\n{e}"
                )


    botones = [
        ("Inventario", mostrar_inventario),
        ("Solicitar", mostrar_solicitar),
        ("Historial", mostrar_historial),
        ("Cambiar perfil", cambiar_perfil)
    ]

    for texto, comando in botones:

        boton = tk.Button(
            panel_lateral,
            text=texto,
            command=comando,
            bg="#34495e",
            fg="white",
            activebackground="#1abc9c",
            activeforeground="white",
            relief="flat",
            borderwidth=0,
            font=("Arial", 11),
            pady=12,
            cursor="hand2"
        )

        boton.pack(
            fill="x",
            padx=10,
            pady=3
        )


    tk.Label(
        panel_lateral,
        text="Sistema de Gestión\nDAEM",
        bg="#2c3e50",
        fg="#bdc3c7",
        font=("Arial", 9),
        pady=20
    ).pack(
        side="bottom",
        fill="x"
    )


    mostrar_inventario()