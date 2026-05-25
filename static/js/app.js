// --- VARIABLES GLOBALES DE APLICACIÓN ---
let currentUser = null;
let currentPane = 'dashboard';

// Estado de la Cámara de Monitoreo
let webcamStream = null;
let webcamVideo = null;
let webcamCanvas = null;
let canvasCtx = null;
let isMonitoring = false;
let isAnalyzing = false;
let currentResult = null; // { text, color, timestamp }
let lastAnalysisTime = 0;

// Estado de la Cámara de Registro
let regStream = null;
let regVideo = null;
let regCanvas = null;
let regCapturedBlob = null;

// --- INICIALIZACIÓN ---
document.addEventListener('DOMContentLoaded', () => {
    // Configurar Reloj en Cabecera
    setInterval(updateClock, 1000);
    updateClock();

    // Verificar Sesión Activa
    checkSession();

    // Configurar Eventos de Navegación del Menú
    document.querySelectorAll('.menu-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const target = e.currentTarget.getAttribute('data-target');
            switchPane(target);
        });
    });

    // Evento Login
    document.getElementById('login-form').addEventListener('submit', handleLogin);

    // Evento Logout
    document.getElementById('btn-logout').addEventListener('click', handleLogout);

    // Eventos de Formularios
    document.getElementById('form-crear-curso').addEventListener('submit', handleCrearCurso);
    document.getElementById('form-crear-salon-curso').addEventListener('submit', handleAsignarSalonCurso);
    document.getElementById('form-crear-salon').addEventListener('submit', handleCrearSalon);
    document.getElementById('form-agregar-restriccion').addEventListener('submit', handleAgregarRestriccion);
    document.getElementById('form-registrar-persona').addEventListener('submit', handleRegistrarPersonaSubmit);
    document.getElementById('form-asignar-estudiante-curso').addEventListener('submit', handleAsignarEstudianteCursoSubmit);

    // Evento Botón Crear Salón (Abrir Modal)
    document.getElementById('btn-crear-salon-modal').addEventListener('click', () => {
        openModal('modal-crear-salon');
    });

    // Evento Botón Toggle Cámara Monitoreo
    document.getElementById('btn-toggle-camera').addEventListener('click', toggleCameraMonitoreo);

    // Eventos de Cámara de Registro y Carga de Foto
    document.getElementById('btn-reg-take-photo').addEventListener('click', captureRegPhoto);
    document.getElementById('btn-reg-retry-photo').addEventListener('click', retryRegPhoto);
    
    // Configurar botón para subir foto como alternativa
    document.getElementById('btn-reg-upload-btn').addEventListener('click', () => {
        document.getElementById('reg-upload-file').click();
    });

    document.getElementById('reg-upload-file').addEventListener('change', handleUploadPhotoChange);

    // Evento de Tabs en Perfil del Estudiante
    document.querySelectorAll('.tab-header').forEach(tab => {
        tab.addEventListener('click', (e) => {
            const targetTab = e.target.getAttribute('data-tab');
            document.querySelectorAll('.tab-header').forEach(h => h.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            
            e.target.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    // Configurar Cierre de Modales
    document.querySelectorAll('.btn-close-modal, .modal-footer .btn-secondary').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) closeModal(modal.id);
        });
    });
});

// --- SISTEMA DE NOTIFICACIONES (TOAST) ---
function showToast(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'fa-circle-info';
    if (type === 'success') icon = 'fa-circle-check';
    if (type === 'error') icon = 'fa-circle-exclamation';
    if (type === 'warning') icon = 'fa-triangle-exclamation';

    toast.innerHTML = `
        <i class="fa-solid ${icon} toast-icon"></i>
        <div class="toast-message">${message}</div>
    `;

    container.appendChild(toast);

    // Auto-remover después de 4 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 200);
    }, 4000);
}

// --- ACTUALIZAR HORA EN PANTALLA ---
function updateClock() {
    const clock = document.getElementById('current-time-display');
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' };
    clock.innerHTML = `<i class="fa-solid fa-calendar-day"></i> ${now.toLocaleDateString('es-ES', options)}`;
}

// --- GESTIÓN DE SESIÓN ---
async function checkSession() {
    try {
        const response = await fetch('/api/session');
        const data = await response.json();
        
        if (data.authenticated) {
            currentUser = data;
            setupUIForRole(data.role);
            
            document.getElementById('login-view').classList.add('hidden');
            document.getElementById('app-view').classList.remove('hidden');
            
            // Set User profile sidebar
            document.getElementById('user-display-name').innerText = data.username;
            document.getElementById('user-display-role').innerText = formatRole(data.role);
            
            // Redirigir según rol
            if (data.role === 'estudiante') {
                switchPane('estudiante-perfil');
            } else {
                switchPane('dashboard');
            }
        } else {
            currentUser = null;
            document.getElementById('app-view').classList.add('hidden');
            document.getElementById('login-view').classList.remove('hidden');
            stopCameraMonitoreo();
            stopCameraRegistro();
        }
    } catch (err) {
        showToast('Error de conexión con el servidor.', 'error');
    }
}

function formatRole(role) {
    if (role === 'super_admin') return 'Super Admin';
    if (role === 'docente') return 'Docente';
    if (role === 'estudiante') return 'Estudiante';
    return role;
}

function setupUIForRole(role) {
    // Esconder todos los elementos condicionales de roles
    document.querySelectorAll('.menu-item').forEach(el => el.classList.add('hidden'));
    
    if (role === 'super_admin') {
        document.querySelectorAll('.role-admin').forEach(el => el.classList.remove('hidden'));
        document.querySelectorAll('.menu-item.role-admin').forEach(el => el.classList.remove('hidden'));
    } else if (role === 'docente') {
        document.querySelectorAll('.role-docente').forEach(el => el.classList.remove('hidden'));
        document.querySelectorAll('.menu-item.role-docente').forEach(el => el.classList.remove('hidden'));
        // Quitar controles de editar del docente en las tablas compartidas
        document.querySelectorAll('.role-admin').forEach(el => el.classList.add('hidden'));
    } else if (role === 'estudiante') {
        document.querySelectorAll('.role-student').forEach(el => el.classList.remove('hidden'));
        document.querySelectorAll('.menu-item.role-student').forEach(el => el.classList.remove('hidden'));
    }
}

// --- LOGUEARSE ---
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const btnSubmit = document.getElementById('btn-login-submit');
    btnSubmit.disabled = true;
    btnSubmit.innerText = 'Iniciando sesión...';

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        
        if (data.success) {
            showToast(`Bienvenido al sistema, ${data.username}.`, 'success');
            checkSession();
        } else {
            showToast(data.message || 'Error al iniciar sesión.', 'error');
        }
    } catch (err) {
        showToast('Error de servidor.', 'error');
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerText = 'Iniciar Sesión';
    }
}

// --- CERRAR SESIÓN ---
async function handleLogout() {
    try {
        await fetch('/api/logout');
        showToast('Sesión cerrada correctamente.', 'info');
        checkSession();
    } catch (err) {
        showToast('Error al cerrar sesión.', 'error');
    }
}

// --- CAMBIO DE VISTA (PANELES) ---
function switchPane(targetPane) {
    if (!currentUser) return;
    
    // Apagar cámaras si salimos de su vista respectiva
    if (currentPane === 'camara' && targetPane !== 'camara') {
        stopCameraMonitoreo();
    }

    currentPane = targetPane;
    
    // Actualizar menú activo
    document.querySelectorAll('.menu-item').forEach(item => {
        if (item.getAttribute('data-target') === targetPane) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Mostrar panel activo
    document.querySelectorAll('.pane').forEach(pane => {
        pane.classList.add('hidden');
    });
    
    const activePaneEl = document.getElementById(`pane-${targetPane}`);
    if (activePaneEl) {
        activePaneEl.classList.remove('hidden');
    }

    // Set View Title
    const titleMap = {
        'dashboard': 'Dashboard General',
        'checklist': 'Checklist de Estudiantes',
        'cursos-salones': 'Asignación de Cursos y Salones',
        'camara': 'Monitoreo Facial de Ingreso',
        'arbol': 'Árbol de Asistencias a Instalaciones',
        'restricciones': 'Módulo de Restricciones de Acceso',
        'estudiante-perfil': 'Mi Portal Estudiantil'
    };
    document.getElementById('view-title').innerText = titleMap[targetPane] || 'UMG Biométrico';

    // Cargar datos del panel correspondiente
    loadPaneData(targetPane);
}

function loadPaneData(pane) {
    if (pane === 'dashboard') {
        loadDashboardStats();
    } else if (pane === 'checklist') {
        loadChecklist();
    } else if (pane === 'cursos-salones') {
        loadCursosYSalones();
    } else if (pane === 'camara') {
        // Preparar cámara de monitoreo (se requiere que el usuario la encienda manualmente)
        document.getElementById('camera-overlay-text').classList.remove('hidden');
        document.getElementById('camera-overlay-text').innerText = 'Presione "Iniciar Cámara" para comenzar';
        document.getElementById('btn-toggle-camera').innerHTML = '<i class="fa-solid fa-video"></i> Iniciar Cámara';
        document.getElementById('btn-toggle-camera').className = 'btn btn-primary';
    } else if (pane === 'arbol') {
        loadAttendanceTree();
    } else if (pane === 'restricciones') {
        loadRestricciones();
    } else if (pane === 'estudiante-perfil') {
        loadEstudiantePerfil();
    }
}

// --- MODAL TRIGGERS ---
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('visible');
        if (modalId === 'modal-registro-estudiante') {
            startCameraRegistro();
        }
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('visible');
        if (modalId === 'modal-registro-estudiante') {
            stopCameraRegistro();
        }
    }
}

// --- LOGICA DE DASHBOARD ---
async function loadDashboardStats() {
    try {
        // Cargar registros para tabla de ingresos recientes
        const responseChecklist = await fetch('/api/estudiantes/checklist');
        const checklist = await responseChecklist.json();
        
        // Cargar asistencias tree para contar ingresos
        const responseTree = await fetch('/api/asistencias/tree');
        const tree = await responseTree.json();
        
        // Cargar restricciones
        const responseRestr = await fetch('/api/restricciones');
        const restr = await responseRestr.json();

        // Contar asistencias
        let countIngresos = 0;
        let ultimosIngresos = [];
        
        // Recorrer árbol para recolectar datos
        if (tree && tree.children) {
            tree.children.forEach(node => {
                if (node.name === "Salones de Clase") {
                    node.children.forEach(salon => {
                        salon.children.forEach(item => {
                            countIngresos++;
                            const parts = item.name.split(' / ');
                            ultimosIngresos.push({
                                nombre: parts[0],
                                hora: parts[1],
                                ubicacion: salon.name
                            });
                        });
                    });
                } else {
                    node.children.forEach(item => {
                        countIngresos++;
                        const parts = item.name.split(' / ');
                        ultimosIngresos.push({
                            nombre: parts[0],
                            hora: parts[1],
                            ubicacion: node.name
                        });
                    });
                }
            });
        }

        // Mostrar estadísticas
        document.getElementById('stat-total-personas').innerText = checklist.length;
        document.getElementById('stat-total-ingresos').innerText = countIngresos;
        document.getElementById('stat-total-restricciones').innerText = restr.length;

        // Renderizar tabla
        const tbody = document.querySelector('#table-dashboard-ingresos tbody');
        tbody.innerHTML = '';
        
        if (ultimosIngresos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-secondary">No hay ingresos registrados el día de hoy.</td></tr>';
            return;
        }

        // Ordenar por hora descendente
        ultimosIngresos.sort((a, b) => b.hora.localeCompare(a.hora));

        ultimosIngresos.slice(0, 5).forEach(log => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${log.nombre}</strong></td>
                <td><span class="badge" style="background-color: rgba(59,130,246,0.15); color: var(--primary);">${log.ubicacion}</span></td>
                <td><i class="fa-regular fa-clock text-secondary"></i> ${log.hora}</td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        console.error('Error cargando stats de dashboard:', err);
    }
}

// --- LOGICA DE CHECKLIST ---
let studentsList = [];

async function loadChecklist() {
    try {
        const response = await fetch('/api/estudiantes/checklist');
        studentsList = await response.json();
        
        // Rellenar select del filtro de carreras en el checklist
        const filterCarrera = document.getElementById('checklist-filter-carrera');
        const carreras = [...new Set(studentsList.map(s => s.carrera).filter(Boolean))];
        
        filterCarrera.innerHTML = '<option value="">Todas las carreras</option>';
        carreras.forEach(c => {
            filterCarrera.innerHTML += `<option value="${c}">${c}</option>`;
        });

        renderChecklistTable();
        
        // Agregar eventos para filtros
        document.getElementById('checklist-search').addEventListener('input', renderChecklistTable);
        filterCarrera.addEventListener('change', renderChecklistTable);

    } catch (err) {
        showToast('Error al cargar checklist de estudiantes.', 'error');
    }
}

function renderChecklistTable() {
    const searchVal = document.getElementById('checklist-search').value.toLowerCase();
    const carreraVal = document.getElementById('checklist-filter-carrera').value;
    
    const tbody = document.querySelector('#table-checklist tbody');
    tbody.innerHTML = '';

    const filtered = studentsList.filter(s => {
        const matchesSearch = s.carnet.toLowerCase().includes(searchVal) || 
                              s.nombre.toLowerCase().includes(searchVal) || 
                              s.apellido.toLowerCase().includes(searchVal);
        const matchesCarrera = !carreraVal || s.carrera === carreraVal;
        return matchesSearch && matchesCarrera;
    });

    // Si es admin, agregar botón de registrar al encabezado si no existe
    const headerActions = document.querySelector('#pane-checklist .card-header-actions');
    let btnRegister = document.getElementById('btn-open-register-modal');
    if (currentUser.role === 'super_admin' && !btnRegister) {
        btnRegister = document.createElement('button');
        btnRegister.id = 'btn-open-register-modal';
        btnRegister.className = 'btn btn-success';
        btnRegister.innerHTML = '<i class="fa-solid fa-user-plus"></i> Registrar Persona';
        btnRegister.addEventListener('click', () => openModal('modal-registro-estudiante'));
        headerActions.appendChild(btnRegister);
    }

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-secondary">No se encontraron estudiantes matriculados.</td></tr>';
        return;
    }

    filtered.forEach(s => {
        const tr = document.createElement('tr');
        
        const coursesBadges = s.cursos.map(c => `<span class="badge" style="background-color: rgba(16,185,129,0.15); color: var(--success); margin: 2px;">${c}</span>`).join(' ');
        
        let actionsHtml = '';
        if (currentUser.role === 'super_admin') {
            actionsHtml = `
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="openAsignarCursoModal('${s.carnet}', '${s.nombre} ${s.apellido}')">
                        <i class="fa-solid fa-book"></i> Asignar Cursos
                    </button>
                </td>
            `;
        } else {
            actionsHtml = '<td class="hidden"></td>';
        }

        tr.innerHTML = `
            <td><strong>${s.carnet}</strong></td>
            <td>${s.nombre} ${s.apellido}</td>
            <td><span class="text-secondary">${s.carrera || 'No asignado'}</span><br><small class="text-secondary">${s.semestre || ''} - Sec. ${s.seccion || ''}</small></td>
            <td><a href="mailto:${s.correo}" class="text-secondary" style="text-decoration:none;"><i class="fa-regular fa-envelope"></i> ${s.correo}</a></td>
            <td>${coursesBadges || '<em class="text-secondary">Sin cursos</em>'}</td>
            ${actionsHtml}
        `;
        tbody.appendChild(tr);
    });
}

// --- MODAL ASIGNAR CURSO ---
let activeStudentCarnet = null;

async function openAsignarCursoModal(carnet, name) {
    activeStudentCarnet = carnet;
    document.getElementById('modal-estudiante-name').innerText = name;
    document.getElementById('modal-estudiante-carnet').innerText = carnet;
    
    // Cargar todos los cursos disponibles en el select
    const responseCursos = await fetch('/api/cursos');
    const cursos = await responseCursos.json();
    
    const select = document.getElementById('select-asignar-curso');
    select.innerHTML = '<option value="">Seleccione un curso...</option>';
    cursos.forEach(c => {
        select.innerHTML += `<option value="${c.id}">${c.codigo} - ${c.nombre}</option>`;
    });

    // Cargar cursos asignados actualmente
    loadStudentAssignedCoursesList();
    openModal('modal-asignar-curso');
}

async function loadStudentAssignedCoursesList() {
    try {
        const response = await fetch(`/api/asignaciones/estudiante/${activeStudentCarnet}`);
        const cursos = await response.json();
        
        const list = document.getElementById('list-estudiante-cursos-asignados');
        list.innerHTML = '';
        
        if (cursos.length === 0) {
            list.innerHTML = '<li class="text-secondary">El estudiante no posee asignaciones de cursos.</li>';
            return;
        }

        cursos.forEach(c => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span><strong>${c.codigo}</strong> - ${c.nombre}</span>
                <button class="btn-icon delete" onclick="handleRemoverEstudianteCurso(${c.id})"><i class="fa-solid fa-trash-can"></i></button>
            `;
            list.appendChild(li);
        });
    } catch (err) {
        showToast('Error cargando asignaciones.', 'error');
    }
}

async function handleAsignarEstudianteCursoSubmit(e) {
    e.preventDefault();
    const cursoId = document.getElementById('select-asignar-curso').value;
    
    if (!cursoId || !activeStudentCarnet) return;
    
    try {
        const response = await fetch('/api/asignaciones/estudiante', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ carnet: activeStudentCarnet, curso_id: parseInt(cursoId) })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Curso asignado correctamente.', 'success');
            loadStudentAssignedCoursesList();
            loadChecklist(); // Recargar checklist de fondo
        } else {
            showToast(data.message || 'Error al asignar curso.', 'error');
        }
    } catch (err) {
        showToast('Error de servidor.', 'error');
    }
}

async function handleRemoverEstudianteCurso(cursoId) {
    if (!activeStudentCarnet || !cursoId) return;
    
    try {
        const response = await fetch('/api/asignaciones/estudiante', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ carnet: activeStudentCarnet, curso_id: parseInt(cursoId) })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Asignación removida con éxito.', 'info');
            loadStudentAssignedCoursesList();
            loadChecklist(); // Recargar checklist de fondo
        } else {
            showToast(data.message || 'No se pudo remover el curso.', 'error');
        }
    } catch (err) {
        showToast('Error de servidor.', 'error');
    }
}

// --- LOGICA DE CURSOS Y SALONES ---
async function loadCursosYSalones() {
    try {
        // Cargar Catálogo Cursos
        const resCursos = await fetch('/api/cursos');
        const cursos = await resCursos.json();
        
        const tblCursos = document.querySelector('#table-catalogo-cursos tbody');
        tblCursos.innerHTML = '';
        if (cursos.length === 0) {
            tblCursos.innerHTML = '<tr><td colspan="2" class="text-center text-secondary">Catálogo vacío.</td></tr>';
        } else {
            cursos.forEach(c => {
                tblCursos.innerHTML += `<tr><td><strong>${c.codigo}</strong></td><td>${c.nombre}</td></tr>`;
            });
        }

        // Cargar dropdowns
        const resSalones = await fetch('/api/salones');
        const salones = await resSalones.json();
        
        const selectSalon = document.getElementById('select-salon-id');
        selectSalon.innerHTML = '<option value="">Seleccione...</option>';
        salones.forEach(s => {
            selectSalon.innerHTML += `<option value="${s.id}">${s.nombre} (Cap: ${s.capacidad})</option>`;
        });

        const selectCurso = document.getElementById('select-curso-id');
        selectCurso.innerHTML = '<option value="">Seleccione...</option>';
        cursos.forEach(c => {
            selectCurso.innerHTML += `<option value="${c.id}">${c.codigo} - ${c.nombre}</option>`;
        });

        // Cargar Asignaciones Salón - Cursos
        loadSalonCursosTable();

    } catch (err) {
        showToast('Error cargando catálogos.', 'error');
    }
}

async function loadSalonCursosTable() {
    try {
        const response = await fetch('/api/salon_cursos');
        const list = await response.json();
        
        const tbody = document.querySelector('#table-salones-asignados tbody');
        tbody.innerHTML = '';
        
        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">No hay asignaciones registradas.</td></tr>';
            return;
        }

        list.forEach(item => {
            tbody.innerHTML += `
                <tr>
                    <td><strong>${item.salon_nombre}</strong></td>
                    <td>${item.curso_nombre}</td>
                    <td><span class="badge" style="background-color:rgba(59,130,246,0.1); color:var(--primary);">${item.horario}</span></td>
                    <td>
                        <button class="btn-icon delete" onclick="handleRemoverSalonCurso(${item.id})"><i class="fa-solid fa-trash-can"></i></button>
                    </td>
                </tr>
            `;
        });
    } catch (err) {
        showToast('Error cargando asignaciones de salón.', 'error');
    }
}

async function handleCrearCurso(e) {
    e.preventDefault();
    const codigo = document.getElementById('curso-codigo').value;
    const nombre = document.getElementById('curso-nombre').value;
    const descripcion = document.getElementById('curso-descripcion').value;

    try {
        const response = await fetch('/api/cursos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo, nombre, descripcion })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Curso creado exitosamente.', 'success');
            document.getElementById('form-crear-curso').reset();
            loadCursosYSalones();
        } else {
            showToast(data.message || 'Error al crear curso.', 'error');
        }
    } catch (err) {
        showToast('Error de conexión.', 'error');
    }
}

async function handleCrearSalon(e) {
    e.preventDefault();
    const nombre = document.getElementById('new-salon-nombre').value;
    const capacidad = document.getElementById('new-salon-capacidad').value;

    try {
        const response = await fetch('/api/salones', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, capacidad })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Salón creado con éxito.', 'success');
            closeModal('modal-crear-salon');
            document.getElementById('form-crear-salon').reset();
            loadCursosYSalones();
        } else {
            showToast(data.message || 'Error al crear salón.', 'error');
        }
    } catch (err) {
        showToast('Error de conexión.', 'error');
    }
}

async function handleAsignarSalonCurso(e) {
    e.preventDefault();
    const salon_id = document.getElementById('select-salon-id').value;
    const curso_id = document.getElementById('select-curso-id').value;
    const horario = document.getElementById('salon-horario').value;

    try {
        const response = await fetch('/api/salon_cursos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ salon_id: parseInt(salon_id), curso_id: parseInt(curso_id), horario })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Curso asignado al salón.', 'success');
            document.getElementById('form-crear-salon-curso').reset();
            loadSalonCursosTable();
        } else {
            showToast(data.message || 'Error al realizar asignación.', 'error');
        }
    } catch (err) {
        showToast('Error de conexión.', 'error');
    }
}

async function handleRemoverSalonCurso(id) {
    try {
        const response = await fetch(`/api/salon_cursos/${id}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (data.success) {
            showToast('Asignación removida del salón.', 'info');
            loadSalonCursosTable();
        } else {
            showToast(data.message || 'No se pudo remover.', 'error');
        }
    } catch (err) {
        showToast('Error de conexión.', 'error');
    }
}

// --- LÓGICA DE MONITOREO FACIAL (WEBCAM) ---
function toggleCameraMonitoreo() {
    if (isMonitoring) {
        stopCameraMonitoreo();
    } else {
        startCameraMonitoreo();
    }
}

function startCameraMonitoreo() {
    webcamVideo = document.getElementById('webcam-video');
    webcamCanvas = document.getElementById('webcam-canvas');
    canvasCtx = webcamCanvas.getContext('2d');
    
    document.getElementById('camera-overlay-text').classList.remove('hidden');
    document.getElementById('camera-overlay-text').innerText = 'Conectando cámara...';

    navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
        .then(stream => {
            webcamStream = stream;
            webcamVideo.srcObject = stream;
            webcamVideo.play();
            isMonitoring = true;
            
            document.getElementById('camera-overlay-text').classList.add('hidden');
            document.querySelector('.camera-scanner-laser').classList.add('active');
            
            document.getElementById('btn-toggle-camera').innerHTML = '<i class="fa-solid fa-video-slash"></i> Detener Monitoreo';
            document.getElementById('btn-toggle-camera').className = 'btn btn-danger';

            // Limpiar logs anteriores
            const logsContainer = document.getElementById('camera-recognition-logs');
            logsContainer.innerHTML = '';

            // Bucle principal de dibujo y envío
            drawAndAnalyzeLoop();
        })
        .catch(err => {
            showToast('No se puede acceder a la cámara web: ' + err.message, 'error');
            document.getElementById('camera-overlay-text').innerText = 'Error: Sin Acceso a Cámara';
        });
}

function stopCameraMonitoreo() {
    isMonitoring = false;
    document.querySelector('.camera-scanner-laser').classList.remove('active');
    
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
    
    if (webcamVideo) {
        webcamVideo.srcObject = null;
    }

    const overlay = document.getElementById('camera-overlay-text');
    if (overlay) {
        overlay.classList.remove('hidden');
        overlay.innerText = 'Cámara Apagada';
    }

    const btn = document.getElementById('btn-toggle-camera');
    if (btn) {
        btn.innerHTML = '<i class="fa-solid fa-video"></i> Iniciar Monitoreo';
        btn.className = 'btn btn-primary';
    }

    currentResult = null;
}

function drawAndAnalyzeLoop() {
    if (!isMonitoring) return;

    canvasCtx.drawImage(webcamVideo, 0, 0, 640, 480);
    drawCameraHUD();

    const now = Date.now();
    if (now - lastAnalysisTime > 1500 && !isAnalyzing) {
        lastAnalysisTime = now;
        analyzeFrame();
    }

    requestAnimationFrame(drawAndAnalyzeLoop);
}

function drawCameraHUD() {
    canvasCtx.strokeStyle = '#3b82f6';
    canvasCtx.lineWidth = 3;
    const len = 30;
    const pad = 100;
    
    // Esquinas de enfoque
    canvasCtx.beginPath();
    canvasCtx.moveTo(pad, pad + len);
    canvasCtx.lineTo(pad, pad);
    canvasCtx.lineTo(pad + len, pad);
    canvasCtx.stroke();
    
    canvasCtx.beginPath();
    canvasCtx.moveTo(640 - pad, pad + len);
    canvasCtx.lineTo(640 - pad, pad);
    canvasCtx.lineTo(640 - pad - len, pad);
    canvasCtx.stroke();
    
    canvasCtx.beginPath();
    canvasCtx.moveTo(pad, 480 - pad - len);
    canvasCtx.lineTo(pad, 480 - pad);
    canvasCtx.lineTo(pad + len, 480 - pad);
    canvasCtx.stroke();
    
    canvasCtx.beginPath();
    canvasCtx.moveTo(640 - pad, 480 - pad - len);
    canvasCtx.lineTo(640 - pad, 480 - pad);
    canvasCtx.lineTo(640 - pad - len, 480 - pad);
    canvasCtx.stroke();

    if (currentResult && (Date.now() - currentResult.timestamp < 2000)) {
        canvasCtx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        canvasCtx.fillRect(100, 390, 440, 50);
        
        canvasCtx.font = 'bold 18px Outfit, sans-serif';
        canvasCtx.fillStyle = currentResult.color;
        canvasCtx.textAlign = 'center';
        canvasCtx.fillText(currentResult.text, 320, 422);

        canvasCtx.strokeStyle = currentResult.color;
        canvasCtx.lineWidth = 2;
        canvasCtx.strokeRect(200, 110, 240, 240);
    } else {
        canvasCtx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        canvasCtx.strokeRect(200, 110, 240, 240);
    }
}

async function analyzeFrame() {
    if (!isMonitoring) return;
    isAnalyzing = true;

    const dataUrl = webcamCanvas.toDataURL('image/jpeg', 0.7);
    const ubicacion = document.getElementById('select-camara-ubicacion').value;

    try {
        const response = await fetch('/api/reconocimiento', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: dataUrl, ubicacion })
        });
        const data = await response.json();
        
        if (data.status === 'allowed') {
            currentResult = {
                text: `ACCESO PERMITIDO: ${data.name}`,
                color: '#10b981',
                timestamp: Date.now()
            };
            addCameraLogItem(data.name, data.carnet, 'Permitido', ubicacion);
        } else if (data.status === 'restricted') {
            currentResult = {
                text: `ACCESO RESTRINGIDO: ${data.name}`,
                color: '#ef4444',
                timestamp: Date.now()
            };
            addCameraLogItem(data.name, data.carnet, 'Restringido', ubicacion, data.motivo);
        }
    } catch (err) {
        console.error('Error en reconocimiento biométrico:', err);
    } finally {
        isAnalyzing = false;
    }
}

function addCameraLogItem(nombre, carnet, tipo, ubicacion, motivo = '') {
    const container = document.getElementById('camera-recognition-logs');
    const noLogs = container.querySelector('.no-logs');
    if (noLogs) noLogs.remove();

    const item = document.createElement('div');
    let iconClass = 'fa-check';
    let logTypeClass = 'log-allowed';
    let detailText = `Ingreso a ${ubicacion}`;

    if (tipo === 'Restringido') {
        iconClass = 'fa-ban';
        logTypeClass = 'log-restricted';
        detailText = `BLOQUEADO en ${ubicacion} - Motivo: ${motivo}`;
    }

    item.className = `log-item ${logTypeClass}`;
    
    const now = new Date();
    const timeStr = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    item.innerHTML = `
        <div class="log-item-icon"><i class="fa-solid ${iconClass}"></i></div>
        <div class="log-item-details">
            <strong>${nombre}</strong>
            <span>Carnet: ${carnet} | ${detailText}</span>
        </div>
        <div class="log-item-time">${timeStr}</div>
    `;

    container.insertBefore(item, container.firstChild);
    if (container.children.length > 10) {
        container.lastChild.remove();
    }
}

// --- LOGICA DE REGISTRO CON CAMARA ---
function startCameraRegistro() {
    regVideo = document.getElementById('reg-webcam-video');
    regCanvas = document.getElementById('reg-webcam-canvas');
    regCapturedBlob = null;

    document.getElementById('btn-reg-take-photo').classList.remove('hidden');
    document.getElementById('btn-reg-upload-btn').classList.remove('hidden');
    document.getElementById('btn-reg-retry-photo').classList.add('hidden');
    document.getElementById('reg-photo-preview').classList.add('hidden');
    regVideo.classList.remove('hidden');
    document.getElementById('btn-submit-registro').disabled = true;

    navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } })
        .then(stream => {
            regStream = stream;
            regVideo.srcObject = stream;
            regVideo.play();
        })
        .catch(err => {
            showToast('Cámara bloqueada o no disponible. Use el botón "Subir Foto" para registrar.', 'info');
        });
}

function stopCameraRegistro() {
    if (regStream) {
        regStream.getTracks().forEach(track => track.stop());
        regStream = null;
    }
    if (regVideo) regVideo.srcObject = null;
}

function captureRegPhoto() {
    if (!regStream) return;

    const ctx = regCanvas.getContext('2d');
    ctx.drawImage(regVideo, 0, 0, 320, 240);
    
    regCanvas.toBlob(blob => {
        regCapturedBlob = blob;
        
        const dataUrl = regCanvas.toDataURL('image/jpeg');
        document.getElementById('img-photo-preview').src = dataUrl;
        
        regVideo.classList.add('hidden');
        document.getElementById('reg-photo-preview').classList.remove('hidden');
        
        document.getElementById('btn-reg-take-photo').classList.add('hidden');
        document.getElementById('btn-reg-upload-btn').classList.add('hidden');
        document.getElementById('btn-reg-retry-photo').classList.remove('hidden');
        
        document.getElementById('btn-submit-registro').disabled = false;
    }, 'image/jpeg', 0.85);
}

function handleUploadPhotoChange(e) {
    const file = e.target.files[0];
    if (file) {
        regCapturedBlob = file;
        const reader = new FileReader();
        reader.onload = (event) => {
            document.getElementById('img-photo-preview').src = event.target.result;
            
            // Dibujar imagen cargada en el canvas para que sirva al backend
            const img = new Image();
            img.onload = () => {
                const ctx = regCanvas.getContext('2d');
                ctx.drawImage(img, 0, 0, 320, 240);
            };
            img.src = event.target.result;

            regVideo.classList.add('hidden');
            document.getElementById('reg-photo-preview').classList.remove('hidden');
            
            document.getElementById('btn-reg-take-photo').classList.add('hidden');
            document.getElementById('btn-reg-upload-btn').classList.add('hidden');
            document.getElementById('btn-reg-retry-photo').classList.remove('hidden');
            
            document.getElementById('btn-submit-registro').disabled = false;
            showToast('Imagen cargada correctamente.', 'success');
        };
        reader.readAsDataURL(file);
    }
}

function retryRegPhoto() {
    regCapturedBlob = null;
    document.getElementById('reg-upload-file').value = '';
    document.getElementById('reg-photo-preview').classList.add('hidden');
    regVideo.classList.remove('hidden');
    
    document.getElementById('btn-reg-take-photo').classList.remove('hidden');
    document.getElementById('btn-reg-upload-btn').classList.remove('hidden');
    document.getElementById('btn-reg-retry-photo').classList.add('hidden');
    document.getElementById('btn-submit-registro').disabled = true;
    
    // Volver a iniciar cámara si es posible
    if (regStream) {
        stopCameraRegistro();
    }
    startCameraRegistro();
}

async function handleRegistrarPersonaSubmit(e) {
    e.preventDefault();

    if (!regCapturedBlob) {
        showToast('Debe realizar la captura o subir una fotografía biométrica.', 'warning');
        return;
    }

    const btnSubmit = document.getElementById('btn-submit-registro');
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Registrando...';

    const formData = new FormData();
    formData.append('carnet', document.getElementById('reg-carnet').value);
    formData.append('nombre', document.getElementById('reg-nombre').value);
    formData.append('apellido', document.getElementById('reg-apellido').value);
    formData.append('correo', document.getElementById('reg-correo').value);
    formData.append('telefono', document.getElementById('reg-telefono').value);
    formData.append('tipo_persona', document.getElementById('reg-tipo').value);
    formData.append('carrera', document.getElementById('reg-carrera').value);
    formData.append('semestre', document.getElementById('reg-semestre').value);
    formData.append('seccion', document.getElementById('reg-seccion').value);
    formData.append('foto', regCapturedBlob, 'foto.jpg');

    try {
        const response = await fetch('/api/personas', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            closeModal('modal-registro-estudiante');
            document.getElementById('form-registrar-persona').reset();
            loadChecklist(); 
        } else {
            showToast(data.message || 'Error al guardar el registro.', 'error');
        }
    } catch (err) {
        showToast('Error de servidor al registrar.', 'error');
    } finally {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = '<i class="fa-solid fa-save"></i> Registrar Estudiante';
    }
}

// --- LOGICA DEL ÁRBOL DE ASISTENCIAS ---
async function loadAttendanceTree() {
    try {
        const response = await fetch('/api/asistencias/tree');
        const treeData = await response.json();
        
        const container = document.getElementById('attendance-tree-container');
        container.innerHTML = '';
        container.appendChild(buildHtmlTree(treeData));
    } catch (err) {
        showToast('Error cargando el árbol de asistencias.', 'error');
    }
}

function buildHtmlTree(node) {
    const nodeEl = document.createElement('div');
    nodeEl.className = 'tree-node-wrapper';
    const isLeaf = node.children.length === 0;
    
    if (isLeaf) {
        const leaf = document.createElement('div');
        leaf.className = 'tree-leaf-node';
        leaf.innerHTML = `<i class="fa-solid fa-user-check"></i> ${node.name}`;
        return leaf;
    }

    const header = document.createElement('div');
    header.className = 'tree-node-header';
    
    let iconClass = 'fa-folder-open';
    if (node.name === "UMG - Sede Boca del Monte") iconClass = 'fa-university';
    else if (node.name === "Puerta Principal") iconClass = 'fa-door-closed';
    else if (node.name === "Salones de Clase") iconClass = 'fa-school';

    header.innerHTML = `
        <i class="fa-solid fa-chevron-down tree-node-toggle"></i>
        <i class="fa-solid ${iconClass} tree-node-icon"></i>
        <span><strong>${node.name}</strong></span>
    `;

    const childrenContainer = document.createElement('div');
    childrenContainer.className = 'tree-node-children';

    node.children.forEach(child => {
        childrenContainer.appendChild(buildHtmlTree(child));
    });

    header.addEventListener('click', () => {
        const toggle = header.querySelector('.tree-node-toggle');
        toggle.classList.toggle('collapsed');
        childrenContainer.classList.toggle('collapsed');
    });

    nodeEl.appendChild(header);
    nodeEl.appendChild(childrenContainer);
    return nodeEl;
}

// --- LOGICA DE RESTRICCIONES ---
async function loadRestricciones() {
    try {
        const response = await fetch('/api/restricciones');
        const list = await response.json();
        
        const tbody = document.querySelector('#table-restricciones tbody');
        tbody.innerHTML = '';

        if (list.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">No hay restricciones activas.</td></tr>';
            return;
        }

        list.forEach(r => {
            tbody.innerHTML += `
                <tr>
                    <td><strong>${r[0]}</strong></td>
                    <td>${r[1]} ${r[2]}</td>
                    <td><span class="badge" style="background-color:rgba(239,68,68,0.1); color:var(--danger);">${r[3]}</span></td>
                    <td>
                        <button class="btn btn-secondary btn-sm" onclick="handleQuitarRestriccion('${r[0]}')">
                            Levantar Bloqueo
                        </button>
                    </td>
                </tr>
            `;
        });
    } catch (err) {
        showToast('Error cargando restricciones.', 'error');
    }
}

async function handleAgregarRestriccion(e) {
    e.preventDefault();
    const carnet = document.getElementById('restriccion-carnet').value;
    const motivo = document.getElementById('restriccion-motivo').value;

    try {
        const response = await fetch('/api/restricciones', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ carnet, motivo })
        });
        const data = await response.json();
        if (data.success) {
            showToast('Bloqueo de ingreso agregado con éxito.', 'success');
            document.getElementById('form-agregar-restriccion').reset();
            loadRestricciones();
        } else {
            showToast(data.message || 'No se pudo agregar la restricción.', 'error');
        }
    } catch (err) {
        showToast('Error de servidor.', 'error');
    }
}

async function handleQuitarRestriccion(carnet) {
    try {
        const response = await fetch(`/api/restricciones/${carnet}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (data.success) {
            showToast('Restricción levantada exitosamente.', 'info');
            loadRestricciones();
        } else {
            showToast(data.message || 'Error al remover la restricción.', 'error');
        }
    } catch (err) {
        showToast('Error de servidor.', 'error');
    }
}

// --- LOGICA DE ESTUDIANTE (PORTAL MI PERFIL) ---
async function loadEstudiantePerfil() {
    if (!currentUser || !currentUser.carnet) return;
    const carnet = currentUser.carnet;

    try {
        const resPerfil = await fetch(`/api/estudiante/perfil/${carnet}`);
        const perfil = await resPerfil.json();
        
        document.getElementById('student-profile-name').innerText = `${perfil.nombre} ${perfil.apellido}`;
        document.getElementById('student-profile-carnet').innerText = perfil.carnet;
        document.getElementById('student-profile-carrera').innerText = perfil.carrera || 'No asignada';
        document.getElementById('student-profile-sem-sec').innerText = `${perfil.semestre || '-'} / Sección ${perfil.seccion || '-'}`;
        document.getElementById('student-profile-correo').innerText = perfil.correo;
        document.getElementById('student-profile-telefono').innerText = perfil.telefono || 'No registrado';

        const resCursos = await fetch(`/api/asignaciones/estudiante/${carnet}`);
        const cursos = await resCursos.json();
        
        const resSalonCursos = await fetch('/api/salon_cursos');
        const salonCursos = await resSalonCursos.json();

        const tblCursos = document.querySelector('#table-estudiante-cursos tbody');
        tblCursos.innerHTML = '';
        
        if (cursos.length === 0) {
            tblCursos.innerHTML = '<tr><td colspan="4" class="text-center text-secondary">No tienes cursos asignados actualmente.</td></tr>';
        } else {
            cursos.forEach(c => {
                const match = salonCursos.find(sc => sc.curso_id === c.id);
                const salon = match ? match.salon_nombre : 'No asignado';
                const horario = match ? match.horario : 'Sin horario';
                
                tblCursos.innerHTML += `
                    <tr>
                        <td><strong>${c.codigo}</strong></td>
                        <td>${c.nombre}</td>
                        <td><span class="badge" style="background-color:rgba(59,130,246,0.1); color:var(--primary);">${salon}</span></td>
                        <td>${horario}</td>
                    </tr>
                `;
            });
        }

        const resAsist = await fetch(`/api/asistencias/personal/${carnet}`);
        const asistencias = await resAsist.json();

        const tblAsist = document.querySelector('#table-estudiante-asistencias tbody');
        tblAsist.innerHTML = '';

        if (asistencias.length === 0) {
            tblAsist.innerHTML = '<tr><td colspan="2" class="text-center text-secondary">No registras asistencias el día de hoy.</td></tr>';
        } else {
            asistencias.forEach(a => {
                tblAsist.innerHTML += `
                    <tr>
                        <td><span class="badge" style="background-color:rgba(16,185,129,0.1); color:var(--success);">${a.ubicacion}</span></td>
                        <td><i class="fa-regular fa-clock text-secondary"></i> ${a.fecha_hora}</td>
                    </tr>
                `;
            });
        }

        const btnPdf = document.getElementById('btn-download-pdf-carnet');
        btnPdf.onclick = () => {
            window.open(`/api/carnet/pdf/${carnet}`, '_blank');
        };

    } catch (err) {
        showToast('Error al cargar perfil estudiantil.', 'error');
    }
}
