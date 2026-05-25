import customtkinter as ctk
from tkinter import ttk, messagebox

from database.queries import add_restriccion, remove_restriccion, get_all_restricciones

class VistaRestricciones(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Módulo 5 - Gestión de Restricciones")
        self.geometry("750x550")
        
        # Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # Panel Superior: Formulario
        self.frame_form = ctk.CTkFrame(self)
        self.frame_form.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        ctk.CTkLabel(self.frame_form, text="Agregar Restricción", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, pady=10)

        self.ent_carnet = ctk.CTkEntry(self.frame_form, placeholder_text="Carnet a restringir", width=200)
        self.ent_carnet.grid(row=1, column=0, padx=10, pady=5)

        self.ent_motivo = ctk.CTkEntry(self.frame_form, placeholder_text="Motivo de la restricción", width=300)
        self.ent_motivo.grid(row=1, column=1, padx=10, pady=5)

        self.btn_agregar = ctk.CTkButton(self.frame_form, text="Restringir Acceso", command=self.agregar, fg_color="#8B0000", hover_color="#A52A2A")
        self.btn_agregar.grid(row=1, column=2, padx=10, pady=5)

        # Panel Inferior: Lista Actual
        self.frame_lista = ctk.CTkFrame(self)
        self.frame_lista.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")

        ctk.CTkLabel(self.frame_lista, text="Personas con Restricción Activa", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Configurar estilos de TTK para adaptar el Treeview al Dark Mode
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", 
                        bordercolor="#343638", lightcolor="#343638", darkcolor="#343638")
        style.map('Treeview', background=[('selected', '#1f538d')])

        columns = ("Carnet", "Nombre", "Apellido", "Motivo")
        self.tree = ttk.Treeview(self.frame_lista, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150 if col != "Motivo" else 250)
            
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.btn_quitar = ctk.CTkButton(self.frame_lista, text="Quitar Restricción Seleccionada", command=self.quitar, fg_color="green", hover_color="darkgreen")
        self.btn_quitar.pack(pady=10)

        self.cargar_datos()

    def cargar_datos(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        registros = get_all_restricciones()
        for r in registros:
            self.tree.insert("", "end", values=r)

    def agregar(self):
        carnet = self.ent_carnet.get().strip()
        motivo = self.ent_motivo.get().strip()
        
        if not carnet or not motivo:
            messagebox.showerror("Error", "Debe ingresar el carnet y el motivo.")
            return
            
        if add_restriccion(carnet, motivo):
            messagebox.showinfo("Éxito", f"Se ha restringido el acceso al carnet {carnet}.")
            self.ent_carnet.delete(0, 'end')
            self.ent_motivo.delete(0, 'end')
            self.cargar_datos()
        else:
            messagebox.showerror("Error", "No se pudo agregar. Verifique que el carnet exista en el sistema y no esté ya restringido.")

    def quitar(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Debe seleccionar un registro de la lista.")
            return
            
        item = self.tree.item(seleccion[0])
        carnet = item['values'][0]
        
        if remove_restriccion(carnet):
            messagebox.showinfo("Éxito", "Se ha levantado la restricción.")
            self.cargar_datos()
        else:
            messagebox.showerror("Error", "Hubo un problema al quitar la restricción.")
