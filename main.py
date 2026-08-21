import tkinter as tk
from tkinter import messagebox
import hashlib
from database.conexion import obtener_conexion, registrar_historial


usuario_actual = None
establecimiento_actual = None


def verificar_login(nombre_usuario, clave):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    clave_hash = hashlib.sha256(clave.encode()).hexdigest()

    cursor.execute(
        """
        SELECT id_usuario, id_establecimiento
        FROM Usuario
        WHERE nombre_usuario = %s
        AND clave_hash = %s
        """,
        (nombre_usuario, clave_hash)
    )

    resultado = cursor.fetchone()

    conexion.close()

    return resultado if resultado else None


def limpiar_ventana(ventana):
    for widget in ventana.winfo_children():
        widget.destroy()


def intentar_login(ventana, entry_usuario, entry_clave):

    global usuario_actual
    global establecimiento_actual

    nombre = entry_usuario.get().strip()
    clave = entry_clave.get().strip()

    if not nombre or not clave:
        messagebox.showwarning(
            "Campos obligatorios",
            "Debes ingresar usuario y clave."
        )
        return

    resultado = verificar_login(nombre, clave)

    if resultado:

        usuario_actual, establecimiento_actual = resultado

        registrar_historial(
            usuario_actual,
            "Inicio de sesión"
        )

        from ventana_principal import crear_ventana_principal

        limpiar_ventana(ventana)

        crear_ventana_principal(
            ventana,
            usuario_actual,
            establecimiento_actual,
            nombre
        )

    else:

        messagebox.showerror(
            "Error",
            "Usuario o clave incorrectos."
        )

        entry_clave.delete(0, tk.END)
        entry_clave.focus()


def mostrar_login(ventana):

    limpiar_ventana(ventana)

    ventana.title("Inventario DAEM - Login")

    # Pantalla completa
    ventana.state("zoomed")

    # Color de fondo
    ventana.configure(bg="#ecf0f1")


    ventana.grid_rowconfigure(0, weight=1)
    ventana.grid_columnconfigure(0, weight=1)


    contenedor = tk.Frame(
        ventana,
        bg="white",
        padx=60,
        pady=50
    )

    contenedor.grid(
        row=0,
        column=0,
        padx=20,
        pady=20
    )


    tk.Label(
        contenedor,
        text="INVENTARIO DAEM",
        font=("Arial", 32, "bold"),
        bg="white",
        fg="#2c3e50"
    ).pack(
        pady=(0, 10)
    )


    tk.Label(
        contenedor,
        text="Sistema de Gestión de Inventario",
        font=("Arial", 16),
        bg="white",
        fg="#7f8c8d"
    ).pack(
        pady=(0, 35)
    )


    tk.Label(
        contenedor,
        text="Usuario",
        font=("Arial", 14, "bold"),
        bg="white",
        fg="#34495e"
    ).pack(
        anchor="w"
    )

    entry_usuario = tk.Entry(
        contenedor,
        font=("Arial", 16),
        width=32,
        relief="solid",
        bd=1
    )

    entry_usuario.pack(
        pady=(8, 20),
        ipady=8
    )


    tk.Label(
        contenedor,
        text="Clave",
        font=("Arial", 14, "bold"),
        bg="white",
        fg="#34495e"
    ).pack(
        anchor="w"
    )

    entry_clave = tk.Entry(
        contenedor,
        font=("Arial", 16),
        width=32,
        show="*",
        relief="solid",
        bd=1
    )

    entry_clave.pack(
        pady=(8, 30),
        ipady=8
    )


    boton_ingresar = tk.Button(
        contenedor,
        text="INGRESAR",
        command=lambda: intentar_login(
            ventana,
            entry_usuario,
            entry_clave
        ),
        font=("Arial", 14, "bold"),
        bg="#2980b9",
        fg="white",
        activebackground="#3498db",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        width=25,
        height=2
    )

    boton_ingresar.pack(
        pady=(0, 10)
    )


    tk.Label(
        contenedor,
        text="Acceso al sistema de gestión DAEM",
        font=("Arial", 10),
        bg="white",
        fg="#95a5a6"
    ).pack(
        pady=(15, 0)
    )


    ventana.bind(
        "<Return>",
        lambda event: intentar_login(
            ventana,
            entry_usuario,
            entry_clave
        )
    )


    entry_usuario.focus()


if __name__ == "__main__":

    raiz = tk.Tk()

    mostrar_login(raiz)

    raiz.mainloop()