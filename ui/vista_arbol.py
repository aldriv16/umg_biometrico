# pyrefly: ignore [missing-import]
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from database.queries import get_all_registros
from utils.tree_builder import build_attendance_tree

class VistaArbol(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Árbol de Asistencias")
        self.geometry("700x500")

        self.lbl_titulo = ctk.CTkLabel(self, text="Árbol de Asistencia a Instalaciones", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_titulo.pack(pady=10)

        # Frame para el Treeview
        self.frame_tree = ctk.CTkFrame(self)
        self.frame_tree.pack(pady=10, padx=20, fill="both", expand=True)

        # Configurar estilos de TTK para adaptar el Treeview al Dark Mode
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        fieldbackground="#2b2b2b", 
                        bordercolor="#343638", 
                        lightcolor="#343638", 
                        darkcolor="#343638", 
                        font=("Helvetica", 11))
        style.map('Treeview', background=[('selected', '#1f538d')])

        self.tree = ttk.Treeview(self.frame_tree)
        self.tree.pack(fill="both", expand=True)

        self.cargar_datos()

    def cargar_datos(self):
        # 1. Obtener registros de la BD
        registros = get_all_registros()
        
        # 2. Construir la estructura de Árbol en Memoria
        root_node = build_attendance_tree(registros)
        
        # 3. Recorrer el árbol para plasmarlo en la Interfaz Gráfica
        self.populate_tree(root_node, "")

    def populate_tree(self, node, parent_id):
        """Función recursiva para agregar los nodos al ttk.Treeview"""
        # Insertar nodo actual y obtener su ID
        item_id = self.tree.insert(parent_id, "end", text=node.key, open=True)
        
        # Insertar los hijos de forma recursiva
        for child in node.children:
            self.populate_tree(child, item_id)
