from .db_manager import get_connection
# pyrefly: ignore [missing-import]
import numpy as np

def insert_persona(carnet, nombre, apellido, telefono, correo, tipo_persona, carrera, semestre, seccion, face_encoding_bytes):
    """Inserta una nueva persona en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO personas (carnet, nombre, apellido, telefono, correo, tipo_persona, carrera, semestre, seccion, face_encoding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (carnet, nombre, apellido, telefono, correo, tipo_persona, carrera, semestre, seccion, face_encoding_bytes))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error insertando persona: {e}")
        return False
    finally:
        conn.close()

def get_all_personas():
    """Retorna una lista de todas las personas con sus encodings ya deserializados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT carnet, nombre, apellido, face_encoding FROM personas')
    rows = cursor.fetchall()
    conn.close()
    
    personas = []
    for row in rows:
        carnet, nombre, apellido, encoding_bytes = row
        encoding = np.frombuffer(encoding_bytes, dtype=np.float64)
        personas.append({
            'carnet': carnet,
            'nombre': nombre,
            'apellido': apellido,
            'encoding': encoding
        })
    return personas

def registrar_ingreso(carnet, ubicacion):
    """Registra la asistencia/ingreso de una persona."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO registros_ingreso (carnet, ubicacion)
            VALUES (%s, %s)
        ''', (carnet, ubicacion))
        conn.commit()
    except Exception as e:
        print(f"Error registrando ingreso: {e}")
    finally:
        conn.close()

def check_restriccion(carnet):
    """Verifica si un carnet tiene restricción de ingreso. Retorna el motivo si existe."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT motivo FROM restricciones WHERE carnet = %s', (carnet,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def get_all_registros():
    """Obtiene todos los registros de ingreso combinados con los nombres."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.ubicacion, p.nombre, p.apellido, r.fecha_hora 
        FROM registros_ingreso r
        JOIN personas p ON r.carnet = p.carnet
        ORDER BY r.fecha_hora ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_restriccion(carnet, motivo):
    """Añade una persona a la lista de restricciones."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO restricciones (carnet, motivo)
            VALUES (%s, %s)
        ''', (carnet, motivo))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error añadiendo restricción (¿quizás ya existe?): {e}")
        return False
    finally:
        conn.close()

def remove_restriccion(carnet):
    """Elimina una restricción para un carnet específico."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM restricciones WHERE carnet = %s', (carnet,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error quitando restricción: {e}")
        return False
    finally:
        conn.close()
def get_all_restricciones():
    """Obtiene la lista de todas las restricciones combinadas con los nombres."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.carnet, p.nombre, p.apellido, r.motivo 
        FROM restricciones r
        JOIN personas p ON r.carnet = p.carnet
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- NUEVOS QUERIES PARA LA INTERFAZ WEB ---

def insert_usuario(username, password_hash, role, carnet=None):
    """Inserta un nuevo usuario en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO usuarios (username, password_hash, role, carnet)
            VALUES (%s, %s, %s, %s)
        ''', (username, password_hash, role, carnet))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error insertando usuario: {e}")
        return False
    finally:
        conn.close()

def get_usuario(username):
    """Busca un usuario por su nombre de usuario."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password_hash, role, carnet FROM usuarios WHERE username = %s', (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'username': row[1],
            'password_hash': row[2],
            'role': row[3],
            'carnet': row[4]
        }
    return None

def get_all_cursos():
    """Retorna todos los cursos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, codigo, nombre, descripcion FROM cursos ORDER BY nombre ASC')
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'codigo': r[1], 'nombre': r[2], 'descripcion': r[3]} for r in rows]

def insert_curso(codigo, nombre, descripcion):
    """Inserta un nuevo curso."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO cursos (codigo, nombre, descripcion)
            VALUES (%s, %s, %s)
        ''', (codigo, nombre, descripcion))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error insertando curso: {e}")
        return False
    finally:
        conn.close()

def get_all_salones():
    """Retorna todos los salones."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nombre, capacidad FROM salones ORDER BY nombre ASC')
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'nombre': r[1], 'capacidad': r[2]} for r in rows]

def insert_salon(nombre, capacidad):
    """Inserta un nuevo salón."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO salones (nombre, capacidad)
            VALUES (%s, %s)
        ''', (nombre, capacidad))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error insertando salon: {e}")
        return False
    finally:
        conn.close()

def get_salon_cursos():
    """Retorna todos los cursos asignados a salones con detalles."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sc.id, s.id, s.nombre, c.id, c.nombre, sc.horario
        FROM salon_cursos sc
        JOIN salones s ON sc.salon_id = s.id
        JOIN cursos c ON sc.curso_id = c.id
        ORDER BY s.nombre ASC, sc.horario ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [{
        'id': r[0],
        'salon_id': r[1],
        'salon_nombre': r[2],
        'curso_id': r[3],
        'curso_nombre': r[4],
        'horario': r[5]
    } for r in rows]

def insert_salon_curso(salon_id, curso_id, horario):
    """Asigna un curso a un salón."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO salon_cursos (salon_id, curso_id, horario)
            VALUES (%s, %s, %s)
            ON CONFLICT (salon_id, curso_id) DO UPDATE SET horario = EXCLUDED.horario
        ''', (salon_id, curso_id, horario))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error insertando salon_curso: {e}")
        return False
    finally:
        conn.close()

def delete_salon_curso(salon_curso_id):
    """Elimina la asignación de un curso a un salón."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM salon_cursos WHERE id = %s', (salon_curso_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error eliminando salon_curso: {e}")
        return False
    finally:
        conn.close()

def get_estudiante_cursos(carnet):
    """Retorna los cursos asignados a un estudiante."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.codigo, c.nombre, c.descripcion
        FROM estudiante_cursos ec
        JOIN cursos c ON ec.curso_id = c.id
        WHERE ec.carnet = %s
        ORDER BY c.nombre ASC
    ''', (carnet,))
    rows = cursor.fetchall()
    conn.close()
    return [{'id': r[0], 'codigo': r[1], 'nombre': r[2], 'descripcion': r[3]} for r in rows]

def insert_estudiante_curso(carnet, curso_id):
    """Asigna un curso a un estudiante."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO estudiante_cursos (carnet, curso_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        ''', (carnet, curso_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error asignando curso a estudiante: {e}")
        return False
    finally:
        conn.close()

def remove_estudiante_curso(carnet, curso_id):
    """Elimina la asignación de un curso a un estudiante."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM estudiante_cursos WHERE carnet = %s AND curso_id = %s', (carnet, curso_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error eliminando curso de estudiante: {e}")
        return False
    finally:
        conn.close()

def get_all_estudiantes_checklist():
    """Obtiene la lista de todos los estudiantes inscritos con sus cursos asignados."""
    conn = get_connection()
    cursor = conn.cursor()
    # Obtener todas las personas que son Estudiantes
    cursor.execute('''
        SELECT p.carnet, p.nombre, p.apellido, p.carrera, p.semestre, p.seccion, p.correo, p.telefono
        FROM personas p
        WHERE LOWER(p.tipo_persona) = 'estudiante'
        ORDER BY p.apellido ASC, p.nombre ASC
    ''')
    personas = cursor.fetchall()
    
    checklist = []
    for p in personas:
        carnet, nombre, apellido, carrera, semestre, seccion, correo, telefono = p
        
        # Obtener los cursos de este estudiante
        cursor.execute('''
            SELECT c.nombre
            FROM estudiante_cursos ec
            JOIN cursos c ON ec.curso_id = c.id
            WHERE ec.carnet = %s
        ''', (carnet,))
        cursos = [row[0] for row in cursor.fetchall()]
        
        checklist.append({
            'carnet': carnet,
            'nombre': nombre,
            'apellido': apellido,
            'carrera': carrera,
            'semestre': semestre,
            'seccion': seccion,
            'correo': correo,
            'telefono': telefono,
            'cursos': cursos
        })
        
    conn.close()
    return checklist
