import customtkinter as ctk
import cv2
import face_recognition
from PIL import Image, ImageTk
import tkinter as tk
import time

from database.queries import get_all_personas, registrar_ingreso, check_restriccion

class VistaCamara(ctk.CTkToplevel):
    def __init__(self, master, ubicacion):
        super().__init__(master)
        self.title(f"Control de Ingreso - {ubicacion}")
        self.geometry("800x600")
        self.ubicacion = ubicacion

        self.lbl_titulo = ctk.CTkLabel(self, text=f"Monitoreo: {ubicacion}", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_titulo.pack(pady=10)

        self.lbl_video = tk.Label(self, bg="black")
        self.lbl_video.pack(pady=10, expand=True, fill="both")

        # Cargar datos de la BD a memoria para reconocimiento rápido
        self.personas = get_all_personas()
        self.known_encodings = [p['encoding'] for p in self.personas]
        self.known_carnets = [p['carnet'] for p in self.personas]
        self.known_names = [f"{p['nombre']} {p['apellido']}" for p in self.personas]

        # Evitar registrar a la misma persona muchas veces seguidas (cooldown de 10 segundos)
        self.ultimos_registros = {}

        self.cap = cv2.VideoCapture(0)
        self.process_this_frame = True # Alternar procesamiento de frames para rendimiento

        self.actualizar_camara()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def actualizar_camara(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            
            # Redimensionar para procesamiento más rápido
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = []
            face_names = []
            face_colors = []

            # Procesar 1 de cada 2 frames para rendimiento
            if self.process_this_frame:
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(self.known_encodings, face_encoding, tolerance=0.5)
                    name = "Desconocido"
                    color = (0, 0, 255) # Rojo por defecto
                    carnet = None

                    if True in matches:
                        first_match_index = matches.index(True)
                        carnet = self.known_carnets[first_match_index]
                        name = self.known_names[first_match_index]
                        
                        # Revisar restricciones (Módulo 5)
                        motivo_restriccion = check_restriccion(carnet)
                        if motivo_restriccion:
                            name = f"¡RESTRINGIDO! {name}"
                            color = (255, 0, 0) # Azul/Alerta para restricción (OpenCV usa BGR, así que es azul)
                        else:
                            color = (0, 255, 0) # Verde acceso permitido
                            
                            # Registrar ingreso con cooldown
                            current_time = time.time()
                            if carnet not in self.ultimos_registros or (current_time - self.ultimos_registros[carnet] > 10):
                                registrar_ingreso(carnet, self.ubicacion)
                                self.ultimos_registros[carnet] = current_time
                                print(f"Acceso registrado: {name} en {self.ubicacion}")
                        
                    face_names.append(name)
                    face_colors.append(color)
            
            self.process_this_frame = not self.process_this_frame

            # Como calculamos locaciones en imagen pequeña, debemos re-escalarlas al dibujar
            if not self.process_this_frame and len(face_locations) == 0:
                # Usar variables cacheadas si no procesamos en este frame
                pass 
            
            # Nota: para simplificar la GUI, calculamos en cada frame de dibujo con las locaciones previas.
            # En una app de producción separaríamos los hilos.
            for (top, right, bottom, left), name, color in zip(face_locations, face_names, face_colors):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)

            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.lbl_video.imgtk = imgtk
            self.lbl_video.configure(image=imgtk)

        self.after_id = self.after(10, self.actualizar_camara)

    def on_close(self):
        self.after_cancel(self.after_id)
        if self.cap.isOpened():
            self.cap.release()
        self.destroy()
