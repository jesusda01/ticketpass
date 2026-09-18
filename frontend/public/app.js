// Reemplaza estas URLs con las que obtendrás al hacer serverless deploy
const API_EVENTOS = "https://10ddg10yq7.execute-api.us-east-1.amazonaws.com/dev";
const API_COMPRAS = "https://70s2wf7nsj.execute-api.us-east-1.amazonaws.com/dev";

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("gridEventos")) {
        cargarEventos();
    } else if (document.getElementById("formReserva")) {
        cargarDetalleEvento();
        iniciarTimer();
    }
});

// ==========================================
// PÁGINA PRINCIPAL (INDEX.HTML)
// ==========================================
async function cargarEventos(categoria = "") {
    try {
        let url = `${API_EVENTOS}/eventos`;
        if (categoria) url += `?categoria=${encodeURIComponent(categoria)}`;

        const res = await fetch(url);
        const eventos = await res.json();

        const grid = document.getElementById("gridEventos");
        grid.innerHTML = "";

        eventos.forEach(e => {
            grid.innerHTML += `
                <div class="card">
                    <div class="card-img-container">
                        <img src="${e.imagen_url}" class="card-img" alt="${e.titulo}">
                        <span class="badge-categoria">${e.categoria}</span>
                    </div>
                    <div class="card-body">
                        <h3 class="card-title">${e.titulo}</h3>
                        <p class="card-info">📍 ${e.lugar}</p>
                        <p class="card-info">📅 ${e.fecha}</p>
                        <div class="card-footer">
                            <span class="card-precio">Desde S/ ${parseFloat(e.precio_base).toFixed(2)}</span>
                            <a href="detalle.html?id=${e.id}" class="btn-ver-mas">Ver detalle</a>
                        </div>
                    </div>
                </div>
            `;
        });
    } catch (err) {
        console.error("Error al cargar eventos:", err);
    }
}

function filtrarCategoria(cat) {
    document.querySelectorAll(".filter-btn").forEach(btn => btn.classList.remove("active"));
    if (event && event.target) {
        event.target.classList.add("active");
    }
    cargarEventos(cat);
}

// ==========================================
// PÁGINA DE DETALLE (DETALLE.HTML)
// ==========================================
let eventoActual = null;

async function cargarDetalleEvento() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");

    if (!id) {
        window.location.href = "index.html";
        return;
    }

    try {
        const res = await fetch(`${API_EVENTOS}/eventos/${id}`);
        eventoActual = await res.json();

        // Mapeo con los IDs exactos de tu detalle.html
        document.getElementById("imgEvento").src = eventoActual.imagen_url;
        document.getElementById("tituloEvento").innerText = eventoActual.titulo;
        
        if (document.getElementById("categoriaEvento")) {
            document.getElementById("categoriaEvento").innerText = eventoActual.categoria;
        }

        document.getElementById("lugarEvento").innerText = `📍 ${eventoActual.lugar}`;
        document.getElementById("fechaEvento").innerText = `📅 ${eventoActual.fecha}`;
        document.getElementById("descripcionEvento").innerText = eventoActual.descripcion;

        const selectZona = document.getElementById("selectZona");
        selectZona.innerHTML = "";

        eventoActual.zonas.forEach(z => {
            selectZona.innerHTML += `<option value="${z.nombre}" data-precio="${z.precio}">${z.nombre} - S/ ${parseFloat(z.precio).toFixed(2)}</option>`;
        });

        // Eventos del formulario para actualizar calculos en tiempo real
        selectZona.addEventListener("change", actualizarTotal);
        document.getElementById("inputCantidad").addEventListener("input", actualizarTotal);
        document.getElementById("checkReembolso").addEventListener("change", actualizarTotal);
        document.getElementById("formReserva").addEventListener("submit", realizarCompra);

        const btnCerrar = document.getElementById("btnCerrarModal");
        if (btnCerrar) {
            btnCerrar.addEventListener("click", cerrarModal);
        }

        actualizarTotal();
    } catch (err) {
        console.error("Error al cargar detalle:", err);
    }
}

function actualizarTotal() {
    if (!eventoActual) return;

    const selectZona = document.getElementById("selectZona");
    const precioZona = parseFloat(selectZona.options[selectZona.selectedIndex].dataset.precio);
    const cantidad = parseInt(document.getElementById("inputCantidad").value) || 1;
    const esReembolsable = document.getElementById("checkReembolso").checked;

    let subtotal = precioZona * cantidad;
    let extraReembolso = esReembolsable ? (12.99 * cantidad) : 0;
    let total = subtotal + extraReembolso;

    document.getElementById("txtTotal").innerText = `S/ ${total.toFixed(2)}`;
}

async function realizarCompra(e) {
    e.preventDefault();

    const selectZona = document.getElementById("selectZona");
    const zonaNombre = selectZona.value;
    const precioUnitario = parseFloat(selectZona.options[selectZona.selectedIndex].dataset.precio);
    const cantidad = parseInt(document.getElementById("inputCantidad").value);
    const esReembolsable = document.getElementById("checkReembolso").checked;
    const emailComprador = document.getElementById("inputEmail").value;
    const metodoPago = document.getElementById("selectMetodo").value;

    const payload = {
        evento_id: eventoActual.id,
        zona_nombre: zonaNombre,
        precio_unitario: precioUnitario,
        cantidad: cantidad,
        es_reembolsable: esReembolsable,
        email_comprador: emailComprador,
        metodo_pago: metodoPago
    };

    try {
        const res = await fetch(`${API_COMPRAS}/comprar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            document.getElementById("modalCodigo").innerText = data.codigo_ticket;
            document.getElementById("modalMonto").innerText = `S/ ${parseFloat(data.monto_total).toFixed(2)}`;
            document.getElementById("modalCompra").style.display = "flex";
        } else {
            alert("Error en la compra: " + (data.message || data.error));
        }
    } catch (err) {
        console.error("Error procesando compra:", err);
    }
}

function cerrarModal() {
    document.getElementById("modalCompra").style.display = "none";
    window.location.href = "index.html";
}

function iniciarTimer() {
    let tiempo = 15 * 60;
    const timerElem = document.getElementById("timer");
    
    const intervalo = setInterval(() => {
        let minutos = Math.floor(tiempo / 60);
        let segundos = tiempo % 60;
        segundos = segundos < 10 ? '0' + segundos : segundos;
        
        if (timerElem) timerElem.innerText = `${minutos}:${segundos}`;

        if (--tiempo < 0) {
            clearInterval(intervalo);
            alert("El tiempo de reserva ha expirado.");
            window.location.href = "index.html";
        }
    }, 1000);
}