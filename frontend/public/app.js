// =========================================================
// CONFIGURACIÓN API (MICROSERVICIOS SERVERLESS)
// =========================================================
const API_EVENTOS_URL = "https://k9ai3zejv8.execute-api.us-east-1.amazonaws.com/dev";
const API_COMPRAS_URL = "https://2g26jo250g.execute-api.us-east-1.amazonaws.com/dev";

let todosLosEventos = [];

// Función auxiliar para prevenir inyecciones HTML / XSS
function escapeHTML(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// =========================================================
// INICIALIZACIÓN
// =========================================================
document.addEventListener('DOMContentLoaded', () => {
    actualizarNavbarUsuario();
    
    if (document.getElementById('eventosGrid')) {
        cargarEventos();
    }

    if (document.getElementById('tablaHistorial')) {
        cargarHistorialCompras();
    }

    const formAuth = document.getElementById('formAuth');
    if (formAuth) {
        formAuth.addEventListener('submit', handleAuthSubmit);
    }
});

// =========================================================
// GESTIÓN DE EVENTOS
// =========================================================
async function cargarEventos() {
    const grid = document.getElementById('eventosGrid');
    const countBadge = document.getElementById('eventoCount');

    if (!grid) return;

    grid.innerHTML = `
        <div class="col-span-full py-16 text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mb-3"></div>
            <p class="text-slate-500 font-medium text-sm">Cargando eventos desde la API...</p>
        </div>
    `;

    try {
        const res = await fetch(`${API_EVENTOS}/eventos`);

        if (!res.ok) {
            throw new Error(`Error en API Gateway (${res.status})`);
        }

        const data = await res.json();
        
        if (Array.isArray(data)) {
            todosLosEventos = data;
        } else if (data.eventos && Array.isArray(data.eventos)) {
            todosLosEventos = data.eventos;
        } else if (data.items && Array.isArray(data.items)) {
            todosLosEventos = data.items;
        } else if (data.body) {
            const parsedBody = typeof data.body === 'string' ? JSON.parse(data.body) : data.body;
            todosLosEventos = Array.isArray(parsedBody) ? parsedBody : (parsedBody.eventos || parsedBody.items || []);
        } else {
            todosLosEventos = [];
        }

        renderEventos(todosLosEventos);
    } catch (error) {
        console.error("Error al cargar eventos:", error);
        grid.innerHTML = `
            <div class="col-span-full py-12 text-center text-red-500 bg-red-50 rounded-2xl border border-red-100 p-6">
                <p class="font-semibold text-base mb-1">Ocurrió un problema al cargar los eventos</p>
                <p class="text-xs text-red-400">Verifica la consola o recarga la página.</p>
            </div>
        `;
        if (countBadge) countBadge.textContent = "0 eventos";
    }
}

function parsePrecio(evento) {
    let val = evento.precio_base || evento.precioBase || evento.precio_desde || evento.precioDesde || evento.precio;

    if (val && typeof val === 'object' && val.N !== undefined) {
        val = val.N;
    }

    const num = parseFloat(val);
    if (isNaN(num) || num <= 0) {
        return "25.00";
    }
    return num.toFixed(2);
}

function renderEventos(lista) {
    const grid = document.getElementById('eventosGrid');
    const countBadge = document.getElementById('eventoCount');

    if (countBadge) countBadge.textContent = `${lista.length} eventos`;

    if (!lista || lista.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full py-16 text-center text-slate-500">
                <p class="text-base font-medium">No hay eventos disponibles en la base de datos.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = lista.map(e => {
        const id = e.id || e.evento_id || e.eventoId || e.PK;
        const titulo = e.titulo || e.nombre || 'Evento sin título';
        const categoria = e.categoria || 'GENERAL';
        const lugar = e.lugar || e.ubicacion || 'Lugar por confirmar';
        const fecha = e.fecha || 'Fecha por confirmar';
        const hora = e.hora || '19:00 hrs';
        const imagen = e.imagen || e.imagen_url || 'https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=800&q=80';
        const precio = parsePrecio(e);

        return `
            <div class="bg-white rounded-2xl overflow-hidden border border-slate-200/80 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col group">
                <div class="relative h-48 overflow-hidden bg-slate-100">
                    <img src="${escapeHTML(imagen)}" alt="${escapeHTML(titulo)}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" onerror="this.src='https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=800&q=80'">
                    <span class="absolute top-3 left-3 text-[10px] font-extrabold tracking-wider uppercase bg-white/90 backdrop-blur-md text-blue-700 px-2.5 py-1 rounded-md shadow-sm">
                        ${escapeHTML(categoria)}
                    </span>
                </div>
                <div class="p-5 flex flex-col flex-grow justify-between">
                    <div>
                        <h3 class="font-bold text-slate-900 text-lg leading-snug mb-2 line-clamp-1">${escapeHTML(titulo)}</h3>
                        <p class="text-xs text-slate-500 mb-4 flex items-center gap-1">
                            <span>📍 ${escapeHTML(lugar)}</span>
                            <span class="text-slate-300">•</span>
                            <span>🗓️ ${escapeHTML(fecha)} - ${escapeHTML(hora)}</span>
                        </p>
                    </div>
                    <div class="pt-4 border-t border-slate-100 flex items-center justify-between mt-auto">
                        <div>
                            <span class="block text-[10px] font-bold uppercase text-slate-400">Desde</span>
                            <span class="text-base font-extrabold text-slate-900">S/ ${precio}</span>
                        </div>
                        <a href="detalle.html?id=${encodeURIComponent(id)}" class="bg-slate-900 text-white text-xs font-semibold px-4 py-2.5 rounded-xl hover:bg-blue-600 transition shadow-sm">
                            Ver Entradas
                        </a>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function filtrarEventos() {
    const input = document.getElementById('searchInput');
    if (!input) return;

    const query = input.value.toLowerCase().trim();
    if (!query) {
        renderEventos(todosLosEventos);
        return;
    }

    const filtrados = todosLosEventos.filter(e => {
        const titulo = (e.titulo || e.nombre || '').toLowerCase();
        const lugar = (e.lugar || e.ubicacion || '').toLowerCase();
        const categoria = (e.categoria || '').toLowerCase();
        return titulo.includes(query) || lugar.includes(query) || categoria.includes(query);
    });

    renderEventos(filtrados);
}

// =========================================================
// HISTORIAL DE COMPRAS
// =========================================================
async function cargarHistorialCompras() {
    const tbody = document.getElementById('tablaHistorial');
    if (!tbody) return;

    const usuarioRaw = localStorage.getItem('usuarioTicketPass');
    if (!usuarioRaw) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-amber-600 py-4">Debes iniciar sesión para consultar tu historial.</td></tr>`;
        return;
    }

    const usuario = JSON.parse(usuarioRaw);

    tbody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center py-8">
                <div class="inline-block animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent mb-2"></div>
                <p class="text-slate-500 text-xs">Cargando tus compras...</p>
            </td>
        </tr>
    `;

    try {
        const res = await fetch(`${API_COMPRAS_URL}/compras/usuario?email=${encodeURIComponent(usuario.email)}`);
        
        let compras = [];
        if (res && res.ok) {
            const data = await res.json();
            if (Array.isArray(data)) {
                compras = data;
            } else if (data.body) {
                const parsed = typeof data.body === 'string' ? JSON.parse(data.body) : data.body;
                compras = Array.isArray(parsed) ? parsed : (parsed.compras || []);
            } else if (data.compras && Array.isArray(data.compras)) {
                compras = data.compras;
            } else if (data.items && Array.isArray(data.items)) {
                compras = data.items;
            }
        }

        if (compras.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-slate-500">No has realizado ninguna compra de entradas aún.</td></tr>`;
            return;
        }

        tbody.innerHTML = compras.map(c => {
            const codigoTicket = c.codigo_ticket || c.ticket_id || c.id || 'N/A';
            const eventoNombre = c.titulo_evento || c.evento_nombre || c.evento_id || 'Evento TicketPass';
            const zona = c.zona || 'General';
            const cantidad = c.cantidad || 1;
            const precioTotal = parseFloat(c.precio_total || c.total || 0).toFixed(2);
            
            let fechaFormateada = 'N/A';
            const rawFecha = c.fecha_compra || c.fecha;
            if (rawFecha) {
                try {
                    const d = new Date(rawFecha);
                    fechaFormateada = d.toLocaleDateString('es-PE', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                } catch (e) {
                    fechaFormateada = rawFecha;
                }
            }

            return `
                <tr class="border-b border-slate-100 hover:bg-slate-50/50 transition">
                    <td class="py-3 px-4 font-mono font-bold text-blue-600">${escapeHTML(codigoTicket)}</td>
                    <td class="py-3 px-4 font-semibold text-slate-800">${escapeHTML(eventoNombre)}</td>
                    <td class="py-3 px-4 text-xs text-slate-500">${escapeHTML(fechaFormateada)}</td>
                    <td class="py-3 px-4 text-slate-700">${escapeHTML(zona)}</td>
                    <td class="py-3 px-4 text-center font-medium text-slate-700">${cantidad}</td>
                    <td class="py-3 px-4 text-right font-extrabold text-slate-900">S/ ${precioTotal}</td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error("Error al cargar historial:", error);
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-red-500 py-4">Ocurrió un error al cargar el historial.</td></tr>`;
    }
}

// =========================================================
// SESIÓN Y AUTENTICACIÓN
// =========================================================
let currentAuthMode = 'login';

function showAuthModal(mode = 'login') {
    currentAuthMode = mode;
    const modal = document.getElementById('authModal');
    const title = document.getElementById('authTitle');
    const subtitle = document.getElementById('authSubtitle');
    const submitBtn = document.getElementById('authSubmitBtn');
    const nombreContainer = document.getElementById('nombreFieldContainer');

    if (!modal) return;

    if (mode === 'register') {
        if (title) title.textContent = "Crear Cuenta";
        if (subtitle) subtitle.textContent = "Regístrate para comprar tus entradas fácilmente";
        if (submitBtn) submitBtn.textContent = "Registrarse";
        if (nombreContainer) nombreContainer.classList.remove('hidden');
    } else {
        if (title) title.textContent = "Iniciar Sesión";
        if (subtitle) subtitle.textContent = "Ingresa tus credenciales para continuar";
        if (submitBtn) submitBtn.textContent = "Ingresar";
        if (nombreContainer) nombreContainer.classList.add('hidden');
    }

    modal.classList.remove('hidden');
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    const form = document.getElementById('formAuth');
    if (modal) modal.classList.add('hidden');
    if (form) form.reset();
}

function handleAuthSubmit(event) {
    if (event) event.preventDefault();

    const emailInput = document.getElementById('authEmail');
    const nombreInput = document.getElementById('authNombre');

    const email = emailInput ? emailInput.value.trim() : "";
    const nombreVal = nombreInput ? nombreInput.value.trim() : "";

    if (!email) {
        showModal(false, "Campo requerido", "Por favor ingresa un correo electrónico.");
        return;
    }

    let nombreFinal = "Usuario";

    if (currentAuthMode === 'register' && nombreVal) {
        nombreFinal = nombreVal;
    } else if (email) {
        const partes = email.split('@');
        nombreFinal = partes[0].charAt(0).toUpperCase() + partes[0].slice(1);
    }

    const usuarioObj = {
        email: email,
        nombre: nombreFinal,
        loginAt: new Date().toISOString()
    };

    localStorage.setItem('usuarioTicketPass', JSON.stringify(usuarioObj));

    closeAuthModal();
    actualizarNavbarUsuario();

    showModal(true, "¡Bienvenido!", `Hola, ${nombreFinal}. Has iniciado sesión correctamente.`);
}

function actualizarNavbarUsuario() {
    const navAuth = document.getElementById('navAuth');
    if (!navAuth) return;

    const usuarioRaw = localStorage.getItem('usuarioTicketPass');

    if (usuarioRaw) {
        const usuario = JSON.parse(usuarioRaw);
        navAuth.innerHTML = `
            <div class="flex items-center gap-3">
                <a href="historial.html" class="text-xs font-semibold text-slate-600 hover:text-blue-600 transition">Mis Compras</a>
                <div class="flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-xl border border-slate-200">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span class="text-xs font-semibold text-slate-700">Hola, <strong class="text-blue-600 font-bold">${escapeHTML(usuario.nombre)}</strong></span>
                </div>
                <button onclick="cerrarSesion()" class="text-xs text-red-600 hover:text-red-700 font-medium bg-red-50 hover:bg-red-100 px-3 py-2 rounded-xl transition border border-red-100">
                    Cerrar Sesión
                </button>
            </div>
        `;
    } else {
        navAuth.innerHTML = `
            <button onclick="showAuthModal('login')" class="text-sm font-medium text-slate-600 hover:text-blue-600 px-3 py-2 rounded-lg transition">
                Iniciar Sesión
            </button>
            <button onclick="showAuthModal('register')" class="text-sm font-semibold bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 transition shadow-sm shadow-blue-200">
                Registrarse
            </button>
        `;
    }
}

function cerrarSesion() {
    localStorage.removeItem('usuarioTicketPass');
    actualizarNavbarUsuario();
    if (window.location.pathname.includes("historial.html")) {
        window.location.href = "index.html";
    } else {
        showModal(true, "Sesión Cerrada", "Has cerrado sesión correctamente.");
    }
}

function showModal(exito, titulo, mensaje) {
    const modal = document.getElementById('statusModal');
    const iconContainer = document.getElementById('statusIcon');
    const titleElem = document.getElementById('statusTitle');
    const msgElem = document.getElementById('statusMessage');

    if (!modal || !iconContainer || !titleElem || !msgElem) return;

    titleElem.textContent = titulo;
    msgElem.textContent = mensaje;

    if (exito) {
        iconContainer.className = "w-12 h-12 rounded-full mx-auto flex items-center justify-center mb-4 bg-emerald-100 text-emerald-600";
        iconContainer.innerHTML = `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`;
    } else {
        iconContainer.className = "w-12 h-12 rounded-full mx-auto flex items-center justify-center mb-4 bg-red-100 text-red-600";
        iconContainer.innerHTML = `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>`;
    }

    modal.classList.remove('hidden');
}

function closeStatusModal() {
    const modal = document.getElementById('statusModal');
    if (modal) modal.classList.add('hidden');
}