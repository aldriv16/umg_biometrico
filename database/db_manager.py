# pyrefly: ignore [missing-import]
import psycopg2
import os

# Configuración de base de datos PostgreSQL
# IMPORTANTE: Cambia estos valores por tus credenciales reales
DB_CONFIG = {
    'host': 'localhost',
    'user': 'postgres',
    'password': 'Aa50168497', 
    'dbname': 'biometrico'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de personas (Estudiantes, Catedráticos, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personas (
            id SERIAL PRIMARY KEY,
            carnet TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            apellido VARCHAR(255) NOT NULL,
            telefono VARCHAR(50),
            correo VARCHAR(255) NOT NULL,
            tipo_persona TEXT NOT NULL,
            carrera TEXT,
            semestre TEXT,
            seccion TEXT,
            face_encoding BYTEA NOT NULL
        )
    ''')

    # Tabla de registros de ingreso
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros_ingreso (
            id SERIAL PRIMARY KEY,
            carnet TEXT NOT NULL,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ubicacion TEXT NOT NULL,
            FOREIGN KEY(carnet) REFERENCES personas(carnet)
        )
    ''')

    # Tabla de personas con restricción de ingreso
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS restricciones (
            id SERIAL PRIMARY KEY,
            carnet TEXT UNIQUE NOT NULL,
            motivo TEXT,
            FOREIGN KEY(carnet) REFERENCES personas(carnet)
        )
    ''')

    # Tabla de usuarios para login con roles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL, -- 'super_admin', 'docente', 'estudiante'
            carnet VARCHAR(50) UNIQUE,
            FOREIGN KEY(carnet) REFERENCES personas(carnet) ON DELETE SET NULL
        )
    ''')

    # Tabla de cursos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cursos (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(50) UNIQUE NOT NULL,
            nombre VARCHAR(100) NOT NULL,
            descripcion TEXT
        )
    ''')

    # Tabla de salones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salones (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) UNIQUE NOT NULL,
            capacidad INTEGER
        )
    ''')

    # Tabla de cursos asignados a salones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salon_cursos (
            id SERIAL PRIMARY KEY,
            salon_id INTEGER REFERENCES salones(id) ON DELETE CASCADE,
            curso_id INTEGER REFERENCES cursos(id) ON DELETE CASCADE,
            horario VARCHAR(100),
            UNIQUE(salon_id, curso_id)
        )
    ''')

    # Tabla de cursos asignados a estudiantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiante_cursos (
            id SERIAL PRIMARY KEY,
            carnet VARCHAR(50) REFERENCES personas(carnet) ON DELETE CASCADE,
            curso_id INTEGER REFERENCES cursos(id) ON DELETE CASCADE,
            UNIQUE(carnet, curso_id)
        )
    ''')

    conn.commit()

    # Seed data: Super Administrador por defecto
    from werkzeug.security import generate_password_hash
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        pw_hash = generate_password_hash("admin123")
        cursor.execute("INSERT INTO usuarios (username, password_hash, role) VALUES ('admin', %s, 'super_admin')", (pw_hash,))
        print("Usuario super_admin ('admin' / 'admin123') creado por defecto.")

    # Seed data: Cursos por defecto
    cursos_seed = [
        ('SO-101', 'Sistemas Operativos', 'Fundamentos de sistemas operativos y concurrencia'),
        ('DW-202', 'Desarrollo Web', 'Construcción de aplicaciones web interactivas'),
        ('BD-303', 'Base de Datos', 'Diseño y optimización de bases de datos relacionales'),
        ('IA-404', 'Inteligencia Artificial', 'Introducción al aprendizaje automático y visión computacional')
    ]
    for codigo, nombre, desc in cursos_seed:
        cursor.execute("SELECT COUNT(*) FROM cursos WHERE codigo = %s", (codigo,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO cursos (codigo, nombre, descripcion) VALUES (%s, %s, %s)", (codigo, nombre, desc))

    # Seed data: Salones por defecto
    salones_seed = [
        ('Salón 101', 30),
        ('Salón 102', 35),
        ('Salón 201', 40)
    ]
    for nombre, cap in salones_seed:
        cursor.execute("SELECT COUNT(*) FROM salones WHERE nombre = %s", (nombre,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO salones (nombre, capacidad) VALUES (%s, %s)", (nombre, cap))

    # Seed data: Asignaciones de salón y curso
    cursor.execute("SELECT COUNT(*) FROM salon_cursos")
    if cursor.fetchone()[0] == 0:
        # Obtener los IDs insertados
        cursor.execute("SELECT id FROM salones WHERE nombre = 'Salón 101'")
        s101_id = cursor.fetchone()
        cursor.execute("SELECT id FROM salones WHERE nombre = 'Salón 102'")
        s102_id = cursor.fetchone()

        cursor.execute("SELECT id FROM cursos WHERE codigo = 'DW-202'")
        dw_id = cursor.fetchone()
        cursor.execute("SELECT id FROM cursos WHERE codigo = 'BD-303'")
        bd_id = cursor.fetchone()
        cursor.execute("SELECT id FROM cursos WHERE codigo = 'IA-404'")
        ia_id = cursor.fetchone()

        if s101_id and s102_id and dw_id and bd_id and ia_id:
            cursor.execute("INSERT INTO salon_cursos (salon_id, curso_id, horario) VALUES (%s, %s, 'Sábado 07:00-09:00')", (s101_id[0], dw_id[0]))
            cursor.execute("INSERT INTO salon_cursos (salon_id, curso_id, horario) VALUES (%s, %s, 'Sábado 09:00-11:00')", (s101_id[0], bd_id[0]))
            cursor.execute("INSERT INTO salon_cursos (salon_id, curso_id, horario) VALUES (%s, %s, 'Sábado 11:00-13:00')", (s102_id[0], ia_id[0]))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada correctamente.")
