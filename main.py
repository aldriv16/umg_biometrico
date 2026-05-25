import tkinter as tk
# pyrefly: ignore [missing-import]
import customtkinter as ctk
import sys
import os

# Asegurar que el directorio raíz está en el path para las importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import init_db
from ui.form_registro import FormRegistro
from ui.vista_camara import VistaCamara
from ui.vista_arbol import VistaArbol
from ui.vista_restricciones import VistaRestricciones

# Configuración inicial de apariencia
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("UMG Biométrico - Control de Ingreso")
        self.geometry("800x600")
        
        # Inicializar base de datos
        init_db()

        # Layout principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.frame_principal = ctk.CTkFrame(self)
        self.frame_principal.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.lbl_titulo = ctk.CTkLabel(self.frame_principal, text="Registro Biométrico UMG", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo.pack(pady=40)

        # Botones del menú
        self.btn_registro = ctk.CTkButton(self.frame_principal, text="1. Registrar Persona", command=self.abrir_registro)
        self.btn_registro.pack(pady=10, fill="x", padx=100)

        self.btn_ingreso_puerta = ctk.CTkButton(self.frame_principal, text="2. Ingreso Puerta Principal", command=self.abrir_puerta)
        self.btn_ingreso_puerta.pack(pady=10, fill="x", padx=100)

        self.btn_ingreso_salon = ctk.CTkButton(self.frame_principal, text="3. Ingreso Salón de Clases", command=self.abrir_salon)
        self.btn_ingreso_salon.pack(pady=10, fill="x", padx=100)

        self.btn_arbol = ctk.CTkButton(self.frame_principal, text="4. Ver Árbol de Asistencias", command=self.abrir_arbol)
        self.btn_arbol.pack(pady=10, fill="x", padx=100)
        
        self.btn_restricciones = ctk.CTkButton(self.frame_principal, text="5. Módulo de Restricciones", command=self.abrir_restricciones, fg_color="#8B0000", hover_color="#A52A2A")
        self.btn_restricciones.pack(pady=10, fill="x", padx=100)

    def abrir_registro(self):
        FormRegistro(self)

    def abrir_puerta(self):
        VistaCamara(self, "Puerta Principal")

    def abrir_salon(self):
        dialog = ctk.CTkInputDialog(text="Ingrese el nombre del salón (ej. Salón 101):", title="Seleccionar Salón")
        salon = dialog.get_input()
        if salon:
            nombre_salon = f"Salón {salon}" if "sal" not in salon.lower() else salon
            VistaCamara(self, nombre_salon)

    def abrir_arbol(self):
        VistaArbol(self)

    def abrir_restricciones(self):
        VistaRestricciones(self)

if __name__ == "__main__":
    app = App()
    app.mainloop()
