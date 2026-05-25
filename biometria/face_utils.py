try:
    # pyrefly: ignore [missing-import]
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

import numpy as np
# pyrefly: ignore [missing-import]
import cv2

def get_face_encoding(image_np):
    """
    Recibe una imagen (formato numpy array de cv2) y retorna el encoding del primer rostro encontrado.
    Si no encuentra rostro, retorna None.
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return None
        
    # face_recognition trabaja mejor con imágenes RGB (OpenCV usa BGR por defecto)
    rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
    
    # Encontrar ubicaciones de rostros en la imagen
    face_locations = face_recognition.face_locations(rgb_image)
    
    if not face_locations:
        return None
        
    # Obtener el encoding del primer rostro encontrado
    encodings = face_recognition.face_encodings(rgb_image, face_locations)
    
    if encodings:
        return encodings[0]
    return None

def serialize_encoding(encoding):
    """Convierte el arreglo numpy a bytes para guardarlo en SQLite (BLOB)."""
    return encoding.tobytes()

def deserialize_encoding(encoding_bytes):
    """Convierte los bytes de SQLite de regreso a numpy array."""
    return np.frombuffer(encoding_bytes, dtype=np.float64)
