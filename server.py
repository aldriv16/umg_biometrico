from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
import os
import base64
import numpy as np
# pyrefly: ignore [missing-import]
import cv2
import time
from werkzeug.security import generate_password_hash, check_password_hash

# Importar base de datos y utilidades
from database.db_manager import init_db
import database.queries as queries
from biometria.face_utils import get_face_encoding, serialize_encoding

try:
    # pyrefly: ignore [missing-import]
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
    print("[SYSTEM] face_recognition importado correctamente.")
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("[WARNING] face_recognition no está instalado. Se simulará el reconocimiento facial.")

from utils.pdf_generator import generar_pdf_carnet
from utils.email_sender import enviar_correo_carnet
from utils.tree_builder import build_attendance_tree

app = Flask(__name__)
app.secret_key = 'super_secret_key_umg_biometrico_web'
CORS(app)

# Inicializar Base de Datos
init_db()

# Caché en memoria para el reconocimiento facial rápido
KNOWN_ENCODINGS = []
KNOWN_CARNETS = []
KNOWN_NAMES = []

def refresh_face_cache():
    global KNOWN_ENCODINGS, KNOWN_CARNETS, KNOWN_NAMES
    try:
        personas = queries.get_all_personas()
        KNOWN_ENCODINGS = [p['encoding'] for p in personas]
        KNOWN_CARNETS = [p['carnet'] for p in personas]
        KNOWN_NAMES = [f"{p['nombre']} {p['apellido']}" for p in personas]
        print(f"[CACHÉ] Rostros cargados: {len(KNOWN_ENCODINGS)}")
    except Exception as e:
        print(f"[CACHÉ ERROR] No se pudo cargar rostros: {e}")

# Cargar caché al inicio
refresh_face_cache()

# Registro de cooldowns para evitar logs duplicados continuos en la cámara (10 segundos)
ultimos_registros = {}

# --- RUTAS DE PLANTILLA ---

@app.route('/')
def index():
    # Servimos el archivo index.html desde la carpeta templates
    return send_file(os.path.join(os.path.dirname(__file__), 'templates', 'index.html'))

# --- RUTAS DE API ---

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuario y contraseña son requeridos.'}), 400

    user = queries.get_usuario(username)
    if not user:
        return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos.'}), 401

    if not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos.'}), 401

    # Establecer sesión
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']
    session['carnet'] = user['carnet']

    return jsonify({
        'success': True,
        'username': user['username'],
        'role': user['role'],
        'carnet': user['carnet']
    })

@app.route('/api/session', methods=['GET'])
def api_session():
    if 'username' in session:
        return jsonify({
            'authenticated': True,
            'username': session['username'],
            'role': session['role'],
            'carnet': session.get('carnet')
        })
    return jsonify({'authenticated': False})

@app.route('/api/logout', methods=['GET'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

# --- CHECKLIST DE ESTUDIANTES ---

@app.route('/api/estudiantes/checklist', methods=['GET'])
def get_estudiantes_checklist():
    # Validar permisos (Solo super_admin y docente)
    if 'role' not in session or session['role'] not in ['super_admin', 'docente']:
        return jsonify({'message': 'Acceso no autorizado.'}), 403
    
    checklist = queries.get_all_estudiantes_checklist()
    return jsonify(checklist)

# --- GESTIÓN DE CURSOS Y SALONES ---

@app.route('/api/cursos', methods=['GET', 'POST'])
def handle_cursos():
    if request.method == 'GET':
        return jsonify(queries.get_all_cursos())
        
    # POST requiere super_admin
    if 'role' not in session or session['role'] != 'super_admin':
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    data = request.get_json() or {}
    codigo = data.get('codigo', '').strip()
    nombre = data.get('nombre', '').strip()
    descripcion = data.get('descripcion', '').strip()
    
    if not codigo or not nombre:
        return jsonify({'success': False, 'message': 'Código y nombre son obligatorios.'}), 400
        
    if queries.insert_curso(codigo, nombre, descripcion):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'El código del curso podría estar duplicado.'}), 400

@app.route('/api/salones', methods=['GET', 'POST'])
def handle_salones():
    if request.method == 'GET':
        return jsonify(queries.get_all_salones())
        
    # POST requiere super_admin
    if 'role' not in session or session['role'] != 'super_admin':
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    data = request.get_json() or {}
    nombre = data.get('nombre', '').strip()
    capacidad = data.get('capacidad')
    
    try:
        capacidad = int(capacidad) if capacidad else 0
    except ValueError:
        return jsonify({'success': False, 'message': 'La capacidad debe ser un número.'}), 400
        
    if not nombre:
        return jsonify({'success': False, 'message': 'El nombre del salón es obligatorio.'}), 400
        
    if queries.insert_salon(nombre, capacidad):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'El nombre del salón podría estar duplicado.'}), 400

@app.route('/api/salon_cursos', methods=['GET', 'POST'])
def handle_salon_cursos():
    if request.method == 'GET':
        return jsonify(queries.get_salon_cursos())
        
    # POST requiere super_admin
    if 'role' not in session or session['role'] != 'super_admin':
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    data = request.get_json() or {}
    salon_id = data.get('salon_id')
    curso_id = data.get('curso_id')
    horario = data.get('horario', '').strip()
    
    if not salon_id or not curso_id or not horario:
        return jsonify({'success': False, 'message': 'Salón, curso y horario son obligatorios.'}), 400
        
    try:
        salon_id = int(salon_id)
        curso_id = int(curso_id)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'IDs de salón o curso inválidos.'}), 400
        
    if queries.insert_salon_curso(salon_id, curso_id, horario):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'No se pudo asignar el curso al salón.'}), 400

@app.route('/api/salon_cursos/<int:id>', methods=['DELETE'])
def delete_salon_curso(id):
    if 'role' not in session or session['role'] != 'super_admin':
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    if queries.delete_salon_curso(id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'No se pudo eliminar la asignación.'}), 400

# --- ASIGNACIONES DE ESTUDIANTES ---

@app.route('/api/asignaciones/estudiante/<carnet>', methods=['GET'])
def get_estudiante_asignaciones(carnet):
    # Seguridad básica
    if 'role' not in session:
        return jsonify({'message': 'No autenticado.'}), 401
    if session['role'] == 'estudiante' and session.get('carnet') != carnet:
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    cursos = queries.get_estudiante_cursos(carnet)
    return jsonify(cursos)

@app.route('/api/asignaciones/estudiante', methods=['POST', 'DELETE'])
def handle_estudiante_asignaciones():
    if 'role' not in session or session['role'] != 'super_admin':
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    data = request.get_json() or {}
    carnet = data.get('carnet', '').strip()
    curso_id = data.get('curso_id')
    
    if not carnet or not curso_id:
        return jsonify({'success': False, 'message': 'Carnet y Curso son obligatorios.'}), 400
        
    try:
        curso_id = int(curso_id)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'ID de curso inválido.'}), 400
        
    if request.method == 'POST':
        if queries.insert_estudiante_curso(carnet, curso_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'No se pudo realizar la asignación.'}), 400
    else:
        if queries.remove_estudiante_curso(carnet, curso_id):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'No se pudo remover la asignación.'}), 400

# --- REGISTRO DE PERSONAS Y BIOMETRÍA ---

@app.route('/api/personas', methods=['POST'])
def registrar_persona():
    if 'role' not in session or session['role'] != 'super_admin':
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    # Obtener campos form-data
    carnet = request.form.get('carnet', '').strip()
    nombre = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    telefono = request.form.get('telefono', '').strip()
    correo = request.form.get('correo', '').strip()
    tipo_persona = request.form.get('tipo_persona', '').strip()
    carrera = request.form.get('carrera', '').strip()
    semestre = request.form.get('semestre', '').strip()
    seccion = request.form.get('seccion', '').strip()
    
    if not carnet or not nombre or not apellido or not correo or not tipo_persona:
        return jsonify({'success': False, 'message': 'Carnet, Nombre, Apellido, Correo y Rol son obligatorios.'}), 400
        
    # Validar si viene la foto
    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'La captura fotográfica biométrica es obligatoria.'}), 400
        
    file = request.files['foto']
    img_bytes = file.read()
    
    # Procesar imagen para detectar rostro
    nparr = np.frombuffer(img_bytes, np.uint8)
    image_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image_np is None:
        return jsonify({'success': False, 'message': 'Archivo de imagen inválido.'}), 400
        
    # Obtener encoding biométrico con fallback si no está instalado
    if FACE_RECOGNITION_AVAILABLE:
        encoding = get_face_encoding(image_np)
        if encoding is None:
            return jsonify({'success': False, 'message': 'No se detectó ningún rostro en la imagen. Intenta de nuevo.'}), 400
        encoding_bytes = serialize_encoding(encoding)
    else:
        # Codificación simulada de 128 flotantes vacíos
        dummy_encoding = np.zeros(128, dtype=np.float64)
        encoding_bytes = serialize_encoding(dummy_encoding)
        
    # Insertar en base de datos de personas
    exito = queries.insert_persona(
        carnet=carnet,
        nombre=nombre,
        apellido=apellido,
        telefono=telefono,
        correo=correo,
        tipo_persona=tipo_persona,
        carrera=carrera,
        semestre=semestre,
        seccion=seccion,
        face_encoding_bytes=encoding_bytes
    )
    
    if not exito:
        return jsonify({'success': False, 'message': 'El número de carnet ya se encuentra registrado.'}), 400
        
    # Crear usuario de login correspondiente
    # Rol 'estudiante' para estudiantes, 'docente' para catedráticos, 'estudiante' por defecto
    role_to_create = 'estudiante'
    username_to_create = carnet
    password_clear = carnet
    
    if tipo_persona.lower() in ['catedrático', 'catedratico', 'docente', 'catedratico/docente']:
        role_to_create = 'docente'
        username_to_create = correo
        password_clear = 'docente123'
    
    pw_hash = generate_password_hash(password_clear)
    queries.insert_usuario(username_to_create, pw_hash, role_to_create, carnet)
    
    # Guardar foto localmente en data/carnets
    foto_dir = os.path.join(os.path.dirname(__file__), 'data', 'carnets')
    os.makedirs(foto_dir, exist_ok=True)
    foto_path = os.path.join(foto_dir, f"foto_{carnet}.jpg")
    cv2.imwrite(foto_path, image_np)
    
    # Generar PDF
    pdf_path = generar_pdf_carnet(
        carnet=carnet,
        nombre=nombre,
        apellido=apellido,
        correo=correo,
        tipo=tipo_persona,
        carrera=carrera,
        semestre=semestre,
        seccion=seccion,
        foto_path=foto_path
    )
    
    # Enviar correo (simulado)
    enviar_correo_carnet(correo, pdf_path)
    
    # Refrescar caché de rostros
    refresh_face_cache()
    
    return jsonify({
        'success': True,
        'message': f"Persona registrada exitosamente. Usuario creado: {username_to_create} / {password_clear}"
    })

# --- RECONOCIMIENTO FACIAL WEB ---

@app.route('/api/reconocimiento', methods=['POST'])
def api_reconocimiento():
    # Validar permisos
    if 'role' not in session or session['role'] not in ['super_admin', 'docente']:
        return jsonify({'success': False, 'message': 'No autorizado.'}), 403
        
    data = request.get_json() or {}
    image_data = data.get('image')
    ubicacion = data.get('ubicacion', 'Puerta Principal').strip()
    
    if not image_data:
        return jsonify({'success': False, 'message': 'Falta la imagen biométrica.'}), 400
        
    # Decodificar imagen base64
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        decoded = base64.b64decode(image_data)
        nparr = np.frombuffer(decoded, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error al decodificar imagen: {str(e)}'}), 400
        
    if frame is None:
        return jsonify({'success': False, 'message': 'No se pudo leer la imagen.'}), 400
        
    # Si no está instalado face_recognition, simulamos una detección con el primer estudiante registrado
    if not FACE_RECOGNITION_AVAILABLE:
        if len(KNOWN_CARNETS) > 0:
            carnet = KNOWN_CARNETS[0]
            nombre = KNOWN_NAMES[0]
            
            # Verificar restricción
            motivo_restriccion = queries.check_restriccion(carnet)
            if motivo_restriccion:
                return jsonify({
                    'success': False,
                    'status': 'restricted',
                    'name': nombre,
                    'carnet': carnet,
                    'motivo': motivo_restriccion,
                    'message': f'¡Restringido! Motivo: {motivo_restriccion}'
                })
                
            # Registrar asistencia con cooldown
            current_time = time.time()
            cooldown_key = f"{carnet}_{ubicacion}"
            if cooldown_key not in ultimos_registros or (current_time - ultimos_registros[cooldown_key] > 10):
                queries.registrar_ingreso(carnet, ubicacion)
                ultimos_registros[cooldown_key] = current_time
                print(f"[RECONOCIMIENTO MOCK] Ingreso registrado: {nombre} en {ubicacion}")
                
            return jsonify({
                'success': True,
                'status': 'allowed',
                'name': nombre,
                'carnet': carnet,
                'message': 'Acceso Autorizado (Simulado - Sin face_recognition)'
            })
        else:
            return jsonify({'success': False, 'status': 'unknown', 'message': 'Persona no identificada (Simulado - Sin alumnos registrados).'})

    # Procesar detección real con face_recognition
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    
    if not face_locations:
        return jsonify({'success': False, 'status': 'no_face', 'message': 'No se detecta rostro.'})
        
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    # Tomamos el primer rostro detectado
    face_encoding = face_encodings[0]
    
    # Buscar coincidencia
    if len(KNOWN_ENCODINGS) == 0:
        return jsonify({'success': False, 'status': 'unknown', 'message': 'No hay rostros registrados en el sistema.'})
        
    matches = face_recognition.compare_faces(KNOWN_ENCODINGS, face_encoding, tolerance=0.5)
    
    if True in matches:
        match_index = matches.index(True)
        carnet = KNOWN_CARNETS[match_index]
        nombre = KNOWN_NAMES[match_index]
        
        # Verificar restricción
        motivo_restriccion = queries.check_restriccion(carnet)
        if motivo_restriccion:
            return jsonify({
                'success': False,
                'status': 'restricted',
                'name': nombre,
                'carnet': carnet,
                'motivo': motivo_restriccion,
                'message': f'¡Restringido! Motivo: {motivo_restriccion}'
            })
            
        # Registrar asistencia con cooldown
        current_time = time.time()
        cooldown_key = f"{carnet}_{ubicacion}"
        if cooldown_key not in ultimos_registros or (current_time - ultimos_registros[cooldown_key] > 10):
            queries.registrar_ingreso(carnet, ubicacion)
            ultimos_registros[cooldown_key] = current_time
            print(f"[RECONOCIMIENTO] Ingreso registrado: {nombre} en {ubicacion}")
            
        return jsonify({
            'success': True,
            'status': 'allowed',
            'name': nombre,
            'carnet': carnet,
            'message': 'Acceso Autorizado'
        })
        
    return jsonify({'success': False, 'status': 'unknown', 'message': 'Persona no identificada.'})

# --- RESTRICCIONES ---

@app.route('/api/restricciones', methods=['GET', 'POST'])
def handle_restricciones():
    if 'role' not in session or session['role'] != 'super_admin':
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    if request.method == 'GET':
        return jsonify(queries.get_all_restricciones())
        
    data = request.get_json() or {}
    carnet = data.get('carnet', '').strip()
    motivo = data.get('motivo', '').strip()
    
    if not carnet or not motivo:
        return jsonify({'success': False, 'message': 'Carnet y motivo son obligatorios.'}), 400
        
    if queries.add_restriccion(carnet, motivo):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'No se pudo agregar la restricción. ¿Existe el carnet?'}), 400

@app.route('/api/restricciones/<carnet>', methods=['DELETE'])
def delete_restriccion(carnet):
    if 'role' not in session or session['role'] != 'super_admin':
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    if queries.remove_restriccion(carnet):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'No se pudo eliminar la restricción.'}), 400

# --- HISTORIAL Y ÁRBOL DE ASISTENCIAS ---

@app.route('/api/asistencias/tree', methods=['GET'])
def get_asistencias_tree():
    # Seguridad (Solo super_admin y docente)
    if 'role' not in session or session['role'] not in ['super_admin', 'docente']:
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    registros = queries.get_all_registros()
    root_node = build_attendance_tree(registros)
    
    def serialize_tree(node):
        return {
            'name': node.key,
            'children': [serialize_tree(child) for child in node.children]
        }
        
    return jsonify(serialize_tree(root_node))

@app.route('/api/asistencias/personal/<carnet>', methods=['GET'])
def get_personal_asistencias(carnet):
    # Validar permisos
    if 'role' not in session:
        return jsonify({'message': 'No autenticado.'}), 401
    if session['role'] == 'estudiante' and session.get('carnet') != carnet:
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    # Obtener historial filtrado por carnet
    conn = queries.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ubicacion, fecha_hora 
        FROM registros_ingreso 
        WHERE carnet = %s 
        ORDER BY fecha_hora DESC
    ''', (carnet,))
    rows = cursor.fetchall()
    conn.close()
    
    historial = []
    for r in rows:
        ubicacion, fecha_hora = r
        historial.append({
            'ubicacion': ubicacion,
            'fecha_hora': fecha_hora.strftime("%Y-%m-%d %H:%M:%S") if fecha_hora else ''
        })
    return jsonify(historial)

# --- PERFIL ESTUDIANTE ---

@app.route('/api/estudiante/perfil/<carnet>', methods=['GET'])
def get_estudiante_perfil(carnet):
    if 'role' not in session:
        return jsonify({'message': 'No autenticado.'}), 401
    if session['role'] == 'estudiante' and session.get('carnet') != carnet:
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    conn = queries.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT carnet, nombre, apellido, telefono, correo, tipo_persona, carrera, semestre, seccion
        FROM personas
        WHERE carnet = %s
    ''', (carnet,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'message': 'Estudiante no encontrado.'}), 404
        
    return jsonify({
        'carnet': row[0],
        'nombre': row[1],
        'apellido': row[2],
        'telefono': row[3],
        'correo': row[4],
        'tipo': row[5],
        'carrera': row[6],
        'semestre': row[7],
        'seccion': row[8]
    })

# --- DESCARGA DE CARNET PDF ---

@app.route('/api/carnet/pdf/<carnet>', methods=['GET'])
def get_carnet_pdf(carnet):
    if 'role' not in session:
        return jsonify({'message': 'No autenticado.'}), 401
    if session['role'] == 'estudiante' and session.get('carnet') != carnet:
        return jsonify({'message': 'Acceso no autorizado.'}), 403
        
    pdf_path = os.path.join(os.path.dirname(__file__), 'data', 'carnets', f"carnet_{carnet}.pdf")
    
    # Si por alguna razón el archivo no existe físicamente pero el estudiante está registrado en la BD, lo regeneramos
    if not os.path.exists(pdf_path):
        conn = queries.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT carnet, nombre, apellido, correo, tipo_persona, carrera, semestre, seccion
            FROM personas WHERE carnet = %s
        ''', (carnet,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            foto_path = os.path.join(os.path.dirname(__file__), 'data', 'carnets', f"foto_{carnet}.jpg")
            generar_pdf_carnet(
                carnet=row[0],
                nombre=row[1],
                apellido=row[2],
                correo=row[3],
                tipo=row[4],
                carrera=row[5],
                semestre=row[6],
                seccion=row[7],
                foto_path=foto_path if os.path.exists(foto_path) else None
            )
            
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=f"carnet_{carnet}.pdf")
    
    return jsonify({'message': 'Carnet PDF no disponible.'}), 404

if __name__ == '__main__':
    # Registrar servidor
    app.run(host='0.0.0.0', port=5000, debug=True)
