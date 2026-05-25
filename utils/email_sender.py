import smtplib
from email.message import EmailMessage
import os

# NOTA: Para un sistema real se deben usar variables de entorno o un config.
# Las credenciales abajo son de ejemplo.
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
# EMAIL_USER = "tu_correo@gmail.com"
# EMAIL_PASS = "tu_contraseña_de_aplicacion"

def enviar_correo_carnet(destinatario, pdf_path):
    """
    Envía el PDF del carnet por correo electrónico.
    En un entorno real, descomentar y configurar las credenciales.
    """
    # MOCK PARA EL PROYECTO (Si no se configuran credenciales reales):
    print(f"[SIMULACIÓN] Correo enviado a {destinatario} con archivo {os.path.basename(pdf_path)}")
    return True
    
    # CODIGO REAL (Descomentar para usar con credenciales válidas)
    """
    msg = EmailMessage()
    msg['Subject'] = 'Tu Carnet Biométrico UMG'
    msg['From'] = EMAIL_USER
    msg['To'] = destinatario
    msg.set_content('Adjunto encontrarás tu carnet de identificación UMG con código QR.')

    try:
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
            pdf_name = os.path.basename(pdf_path)
            
        msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=pdf_name)

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            
        print("Correo enviado exitosamente.")
        return True
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False
    """
