# pyrefly: ignore [missing-import]
import customtkinter as ctk
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox
import uuid

# Importar lógica
from biometria.face_utils import get_face_encoding, serialize_encoding
from database.queries import insert_persona
from utils.pdf_generator import generar_pdf_carnet
from utils.email_sender import enviar_correo_carnet

class FormRegistro(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Proceso 1 - Registro de Persona")
        self.geometry("900x700")
        
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO: Formulario ---
        self.frame_form = ctk.CTkFrame(self)
        self.frame_form.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(self.frame_form, text="Datos Biográficos", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)

        # Campos
        self.ent_carnet = ctk.CTkEntry(self.frame_form, placeholder_text="Número de Carnet (*Obligatorio)")
        self.ent_carnet.pack(pady=5, padx=20, fill="x")

        self.ent_nombre = ctk.CTkEntry(self.frame_form, placeholder_text="Nombre (*Obligatorio)")
        self.ent_nombre.pack(pady=5, padx=20, fill="x")

        self.ent_apellido = ctk.CTkEntry(self.frame_form, placeholder_text="Apellido (*Obligatorio)")
        self.ent_apellido.pack(pady=5, padx=20, fill="x")

        self.ent_telefono = ctk.CTkEntry(self.frame_form, placeholder_text="Número de teléfono")
        self.ent_telefono.pack(pady=5, padx=20, fill="x")

        self.ent_correo = ctk.CTkEntry(self.frame_form, placeholder_text="Correo electrónico UMG (*Obligatorio)")
        self.ent_correo.pack(pady=5, padx=20, fill="x")

        self.cmb_tipo = ctk.CTkComboBox(self.frame_form, values=["Estudiante", "Catedrático", "Administrativo", "Operativo"])
        self.cmb_tipo.set("Estudiante")
        self.cmb_tipo.pack(pady=5, padx=20, fill="x")

        self.ent_carrera = ctk.CTkEntry(self.frame_form, placeholder_text="Carrera")
        self.ent_carrera.pack(pady=5, padx=20, fill="x")

        self.ent_semestre = ctk.CTkEntry(self.frame_form, placeholder_text="Semestre")
        self.ent_semestre.pack(pady=5, padx=20, fill="x")

        self.ent_seccion = ctk.CTkEntry(self.frame_form, placeholder_text="Sección")
        self.ent_seccion.pack(pady=5, padx=20, fill="x")

        # --- PANEL DERECHO: Cámara ---
        self.frame_camara = ctk.CTkFrame(self)
        self.frame_camara.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(self.frame_camara, text="Captura Biométrica", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)

        self.lbl_video = tk.Label(self.frame_camara, bg="black")
        self.lbl_video.pack(pady=10, expand=True, fill="both")

        self.btn_capturar = ctk.CTkButton(self.frame_camara, text="Capturar y Registrar", command=self.registrar, fg_color="green", hover_color="darkgreen")
        self.btn_capturar.pack(pady=20)

        # --- INICIAR CÁMARA ---
        self.cap = cv2.VideoCapture(0)
        self.current_frame = None
        self.actualizar_camara()

        # Al cerrar ventana
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def actualizar_camara(self):
        ret, frame = self.cap.read()
        if ret:
            # Espejar imagen
            frame = cv2.flip(frame, 1)
            self.current_frame = frame.copy()
            
            # Convertir formato de BGR (OpenCV) a RGB y luego a ImageTK
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.lbl_video.imgtk = imgtk
            self.lbl_video.configure(image=imgtk)
        
        # Repetir tras 10ms
        self.after_id = self.after(10, self.actualizar_camara)

    def registrar(self):
        # 1. Validar campos
        carnet_num = self.ent_carnet.get().strip()
        nombre = self.ent_nombre.get().strip()
        apellido = self.ent_apellido.get().strip()
        correo = self.ent_correo.get().strip()
        
        if not carnet_num or not nombre or not apellido or not correo:
            messagebox.showerror("Error", "Carnet, Nombre, Apellido y Correo son obligatorios.")
            return

        # 2. Capturar biometría
        if self.current_frame is None:
            messagebox.showerror("Error", "No se detecta la cámara.")
            return
            
        encoding = get_face_encoding(self.current_frame)
        if encoding is None:
            messagebox.showerror("Error", "No se detectó ningún rostro en la imagen. Intenta de nuevo.")
            return
            
        encoding_bytes = serialize_encoding(encoding)

        # 3. Guardar en BD
        exito = insert_persona(
            carnet=carnet_num,
            nombre=nombre,
            apellido=apellido,
            telefono=self.ent_telefono.get().strip(),
            correo=correo,
            tipo_persona=self.cmb_tipo.get(),
            carrera=self.ent_carrera.get().strip(),
            semestre=self.ent_semestre.get().strip(),
            seccion=self.ent_seccion.get().strip(),
            face_encoding_bytes=encoding_bytes
        )

        if not exito:
            messagebox.showerror("Error BD", "No se pudo guardar en la base de datos.")
            return

        # Guardar foto temporalmente
        import os
        foto_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'carnets')
        os.makedirs(foto_dir, exist_ok=True)
        foto_path = os.path.join(foto_dir, f"foto_{carnet_num}.jpg")
        cv2.imwrite(foto_path, self.current_frame)

        # 4. Generar PDF
        pdf_path = generar_pdf_carnet(
            carnet=carnet_num,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            tipo=self.cmb_tipo.get(),
            carrera=self.ent_carrera.get().strip(),
            semestre=self.ent_semestre.get().strip(),
            seccion=self.ent_seccion.get().strip(),
            foto_path=foto_path
        )

        # 5. Enviar Correo
        enviar_correo_carnet(correo, pdf_path)

        messagebox.showinfo("Éxito", f"Registro completado.\nCarnet: {carnet_num}\nSe ha simulado el envío del PDF.")
        self.on_close()

    def on_close(self):
        self.after_cancel(self.after_id)
        if self.cap.isOpened():
            self.cap.release()
        self.destroy()
