import os
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
# pyrefly: ignore [missing-import]
from PIL import Image

def generar_pdf_carnet(carnet, nombre, apellido, correo, tipo, carrera, semestre, seccion, foto_path=None):
    """Genera un carnet en formato PDF con un código QR, foto, logo y firma."""
    # Asegurar el directorio de salida
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'carnets')
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_path = os.path.join(output_dir, f"carnet_{carnet}.pdf")
    
    # 1. Generar Código QR (Datos enriquecidos)
    qr_data = f"Nombre: {nombre} {apellido}\nCarnet: {carnet}\nRol: {tipo}\nCarrera: {carrera}\nSemestre: {semestre}\nSección: {seccion}\nCorreo: {correo}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    qr_path = os.path.join(output_dir, f"qr_{carnet}.png")
    qr_img.save(qr_path)
    
    # 2. Generar PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Dibujar marco simple
    # Marco más grande
    c.setLineWidth(2)
    c.rect(40, height - 380, 420, 320)
    
    # Insertar Logo UMG
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo_umg.png')
    if os.path.exists(logo_path):
        # Tratar de mantener un aspecto razonable para el logo
        c.drawImage(logo_path, 50, height - 120, width=70, height=50, preserveAspectRatio=True, mask='auto')
    
    # Títulos
    c.setFont("Helvetica-Bold", 16)
    c.drawString(130, height - 85, "UNIVERSIDAD MARIANO GÁLVEZ")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(130, height - 105, "CARNET DE IDENTIFICACIÓN")
    c.setFont("Helvetica", 10)
    c.drawString(130, height - 120, "Sede Boca del Monte")
    
    # Línea separadora
    c.line(40, height - 130, 460, height - 130)

    # Fotografía
    if foto_path and os.path.exists(foto_path):
        c.drawImage(foto_path, 55, height - 260, width=100, height=120)

    # Datos de la persona (Alineados a la derecha de la foto)
    y_pos = height - 150
    text_x = 170
    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_x, y_pos, "Carnet:")
    c.setFont("Helvetica", 10)
    c.drawString(text_x + 50, y_pos, carnet)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_x, y_pos - 20, "Nombre:")
    c.setFont("Helvetica", 10)
    c.drawString(text_x + 50, y_pos - 20, f"{nombre} {apellido}")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_x, y_pos - 40, "Rol:")
    c.setFont("Helvetica", 10)
    c.drawString(text_x + 50, y_pos - 40, tipo)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_x, y_pos - 60, "Carrera:")
    c.setFont("Helvetica", 10)
    c.drawString(text_x + 50, y_pos - 60, carrera)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_x, y_pos - 80, "Sem/Sec:")
    c.setFont("Helvetica", 10)
    c.drawString(text_x + 50, y_pos - 80, f"{semestre} / {seccion}")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_x, y_pos - 100, "Correo:")
    c.setFont("Helvetica", 10)
    c.drawString(text_x + 50, y_pos - 100, correo)
    
    # Insertar QR
    c.drawImage(qr_path, 330, height - 260, width=110, height=110)
    
    # Espacio para Firma
    c.setLineWidth(1)
    c.line(150, height - 330, 350, height - 330)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(250, height - 345, "Firma del Titular")
    
    c.save()
    
    # Limpiar imagen QR temporal
    try:
        os.remove(qr_path)
    except:
        pass
        
    return pdf_path
