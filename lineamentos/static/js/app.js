/**
 * SRTM Lineament Studio - Frontend Logic (app.js)
 * Visualizador Espacial Leaflet + Diagrama de Roseta + SQLite API
 */

let mapInstance = null;
let camadaLineamentos = null;
let camadaProjetos = null;
let camadaAreas = null;
let analisesCache = [];
let projetoAtivoId = null;

// Helper para criar tile layers com supressão graciosa de erros
function criarTileLayer(url, opcoes) {
    const layer = L.tileLayer(url, opcoes);
    layer.on('tileerror', (e) => {
        if (e.tile) {
            e.tile.style.opacity = '0';
        }
    });
    return layer;
}

document.addEventListener("DOMContentLoaded", () => {
    inicializarMapa();

    const formAnalise = document.getElementById("form-analise");
    const tabelaCorpo = document.getElementById("tabela-analises-corpo");
    const btnAtualizar = document.getElementById("btn-atualizar");
    const filtroBusca = document.getElementById("filtro-busca");
    const btnEnquadrar = document.getElementById("btn-enquadrar-mapa");

    if (btnEnquadrar) {
        btnEnquadrar.addEventListener("click", () => enquadrarTodosProjetos());
    }

    if (btnAtualizar) {
        btnAtualizar.addEventListener("click", () => {
            carregarAnalises();
            mostrarToast("Dados sincronizados com o banco SQLite.", "success");
        });
    }

    if (filtroBusca) {
        filtroBusca.addEventListener("input", (e) => {
            const termo = e.target.value.toLowerCase().trim();
            if (!termo) {
                renderizarTabela(analisesCache);
                return;
            }

            const filtrados = analisesCache.filter(item => 
                (item.nome_projeto || "").toLowerCase().includes(termo) ||
                (item.resolucao || "").toLowerCase().includes(termo) ||
                (item.azimute_predominante || "").toLowerCase().includes(termo) ||
                (item.status || "").toLowerCase().includes(termo)
            );
            renderizarTabela(filtrados);
        });
    }

    if (formAnalise) {
        formAnalise.addEventListener("submit", async (evento) => {
            evento.preventDefault();

            const btnSubmit = document.getElementById("btn-submit");
            const textoOriginal = btnSubmit.innerHTML;

            const nomeProjeto = document.getElementById("nome_projeto").value.trim();
            const resolucao = document.getElementById("resolucao").value;
            const status = document.getElementById("status").value;
            const azimute = document.getElementById("azimute_predominante").value;
            const lat = parseFloat(document.getElementById("latitude").value) || -15.7801;
            const lng = parseFloat(document.getElementById("longitude").value) || -47.9292;

            if (!nomeProjeto) {
                mostrarToast("Por favor, preencha o nome do projeto.", "error");
                return;
            }

            const payload = {
                nome_projeto: nomeProjeto,
                resolucao: resolucao,
                status: status,
                azimute_predominante: azimute,
                latitude: lat,
                longitude: lng,
                total_lineamentos: Math.floor(Math.random() * 80) + 90
            };

            try {
                btnSubmit.disabled = true;
                btnSubmit.innerHTML = `<span>Processando e Vetorizando MDE...</span>`;

                const resposta = await fetch("/api/analises", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                const resultado = await resposta.json();

                if (!resposta.ok) {
                    throw new Error(resultado.mensagem || `Erro HTTP ${resposta.status}`);
                }

                mostrarToast("Projeto gravado e plotado no mapa com sucesso!", "success");
                formAnalise.reset();
                aplicarPresetRegiao("-15.7801,-47.9292");

                await carregarAnalises();
                if (resultado.analise && resultado.analise.id) {
                    focarProjetoNoMapa(resultado.analise.id, true);
                }
            } catch (erro) {
                console.error("Erro ao enviar análise:", erro);
                mostrarToast(`Falha ao cadastrar: ${erro.message}`, "error");
            } finally {
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = textoOriginal;
            }
        });
    }

    carregarAnalises();
    desenharRoseta();
});

// =============================================================================
// 1. Inicialização do Mapa Leaflet com Camadas Livres
// =============================================================================
function inicializarMapa() {
    const mapEl = document.getElementById("lineaments-map");
    if (!mapEl) return;

    mapInstance = L.map("lineaments-map", {
        zoomControl: true,
        attributionControl: true
    }).setView([-15.7801, -47.9292], 4);

    // 1.1. Esri World Topo / Shaded Relief (Ideal para relevo e geomorfologia)
    const esriTopo = criarTileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 18, attribution: "Esri Relevo & Topografia &bull; Sem API Key" }
    );

    // 1.2. Esri Dark Gray (Modo Noturno)
    const esriDark = criarTileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 16, attribution: "Esri Dark Canvas" }
    );

    // 1.3. Esri Satélite (Alta Resolução)
    const esriSat = criarTileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 19, attribution: "Esri Satélite (Imagem Real)" }
    );

    // 1.4. OpenStreetMap Padrão
    const osm = criarTileLayer(
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        { maxZoom: 19, attribution: "&copy; OpenStreetMap contributors" }
    );

    // Ativa Esri Topográfico por padrão (destaca relevo SRTM)
    esriTopo.addTo(mapInstance);

    // Grupos de camadas
    camadaLineamentos = L.layerGroup().addTo(mapInstance);
    camadaProjetos = L.layerGroup().addTo(mapInstance);
    camadaAreas = L.layerGroup().addTo(mapInstance);

    // Controle de Camadas
    const baseMaps = {
        "Esri Relevo & Topo (MDE)": esriTopo,
        "Esri Dark (Noturno)": esriDark,
        "Satélite Esri (Alta Resolução)": esriSat,
        "OpenStreetMap (Padrão)": osm
    };

    const overlayMaps = {
        "Lineamentos Estruturais (SRTM)": camadaLineamentos,
        "Centros de Extração": camadaProjetos,
        "Áreas de Varredura MDE": camadaAreas
    };

    L.control.layers(baseMaps, overlayMaps, {
        position: "topright",
        collapsed: true
    }).addTo(mapInstance);

    L.control.scale({
        metric: true,
        imperial: false,
        position: "bottomleft"
    }).addTo(mapInstance);
}

// =============================================================================
// 2. Carregar Análises do SQLite
// =============================================================================
async function carregarAnalises() {
    const tabelaCorpo = document.getElementById("tabela-analises-corpo");
    if (!tabelaCorpo) return;

    tabelaCorpo.innerHTML = `<tr><td colspan="8" class="table-loading">Buscando dados no banco SQLite...</td></tr>`;

    try {
        const resposta = await fetch("/api/analises", {
            method: "GET",
            headers: { "Accept": "application/json" }
        });

        if (!resposta.ok) {
            throw new Error(`Falha na resposta do servidor (HTTP ${resposta.status})`);
        }

        const dados = await resposta.json();
        analisesCache = dados.analises || [];
        renderizarTabela(analisesCache);
        atualizarEstatisticas(analisesCache);
        plotarProjetosNoMapa(analisesCache);
    } catch (erro) {
        console.error("Erro ao carregar análises:", erro);
        tabelaCorpo.innerHTML = `<tr><td colspan="8" class="table-empty" style="color: var(--accent-danger);">Erro ao carregar dados: ${erro.message}</td></tr>`;
        mostrarToast("Não foi possível conectar à API de análises.", "error");
    }
}

// =============================================================================
// 3. Plotagem no Mapa Leaflet (Traços e Marcadores)
// =============================================================================
function plotarProjetosNoMapa(projetos) {
    if (!mapInstance || !camadaProjetos || !camadaLineamentos) return;

    camadaProjetos.clearLayers();
    camadaLineamentos.clearLayers();
    camadaAreas.clearLayers();

    if (!projetos || projetos.length === 0) return;

    projetos.forEach(p => {
        const lat = p.latitude || -15.78;
        const lng = p.longitude || -47.93;

        // 1. Bounding box / Área de varredura do MDE (retângulo translúcido de ~1°x1°)
        const boundsArea = [
            [lat - 0.35, lng - 0.35],
            [lat + 0.35, lng + 0.35]
        ];
        const rect = L.rectangle(boundsArea, {
            color: "rgba(139, 92, 246, 0.4)",
            weight: 1,
            dashArray: "3, 6",
            fillColor: "rgba(79, 70, 229, 0.08)",
            fillOpacity: 0.2
        });
        camadaAreas.addLayer(rect);

        // 2. Traços de Lineamentos Vetoriais (LineStrings simulando falhas/fraturas do SRTM)
        if (p.lineamentos_features && Array.isArray(p.lineamentos_features)) {
            p.lineamentos_features.forEach(f => {
                const coords = f.geometry.coordinates.map(c => [c[1], c[0]]); // GeoJSON [lng, lat] para Leaflet [lat, lng]
                const tend = f.properties.tendencia || "NE-SW";

                let corLinha = "#c084fc"; // NE-SW (Violeta)
                if (tend === "NW-SE") corLinha = "#38bdf8"; // NW-SE (Azul)
                else if (tend === "E-W") corLinha = "#fbbf24"; // E-W (Âmbar)
                else if (tend === "N-S") corLinha = "#10b981"; // N-S (Verde)

                const linha = L.polyline(coords, {
                    color: corLinha,
                    weight: 2.2,
                    opacity: 0.85
                });

                linha.bindTooltip(`
                    <strong>Lineamento ${tend}</strong><br>
                    Azimute: ${f.properties.azimute}°<br>
                    Extensão: ${f.properties.comprimento_km} km
                `, { className: "map-tooltip" });

                linha.on("click", () => focarProjetoNoMapa(p.id, false));
                camadaLineamentos.addLayer(linha);
            });
        }

        // 3. Marcador Central Pulsante do Projeto
        const iconCustom = L.divIcon({
            className: "project-map-marker-wrap",
            html: `
                <div class="project-map-marker ${projetoAtivoId === p.id ? 'active' : ''}">
                    <span class="marker-pulse"></span>
                    <span class="marker-core"></span>
                </div>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });

        const marker = L.marker([lat, lng], { icon: iconCustom });
        
        const popupContent = `
            <div class="marker-popup-card">
                <span class="popup-tag">${escapeHtml(p.resolucao)}</span>
                <h4>${escapeHtml(p.nome_projeto)}</h4>
                <div class="popup-meta">
                    <div><strong>Azimute:</strong> ${escapeHtml(p.azimute_predominante || 'NE-SW')}</div>
                    <div><strong>Lineamentos:</strong> ${p.total_lineamentos || 120} detectados</div>
                    <div><strong>Status:</strong> ${escapeHtml(p.status)}</div>
                </div>
                <button class="btn btn-primary btn-sm popup-btn" onclick="focarProjetoNoMapa(${p.id}, true)">
                    Focar e Analisar Roseta
                </button>
            </div>
        `;

        marker.bindPopup(popupContent);
        marker.on("click", () => focarProjetoNoMapa(p.id, false));
        camadaProjetos.addLayer(marker);
    });
}

// =============================================================================
// 4. Focar Projeto no Mapa e Sincronizar Diagrama de Roseta
// =============================================================================
function focarProjetoNoMapa(projetoId, abrirPopup = true) {
    const proj = analisesCache.find(p => p.id === projetoId);
    if (!proj) return;

    projetoAtivoId = proj.id;

    // Atualiza marcador visual ativo
    plotarProjetosNoMapa(analisesCache);

    if (mapInstance && proj.latitude && proj.longitude) {
        mapInstance.flyTo([proj.latitude, proj.longitude], 9, {
            animate: true,
            duration: 1.2
        });

        if (abrirPopup) {
            setTimeout(() => {
                camadaProjetos.eachLayer(layer => {
                    const latlng = layer.getLatLng();
                    if (Math.abs(latlng.lat - proj.latitude) < 0.001 && Math.abs(latlng.lng - proj.longitude) < 0.001) {
                        layer.openPopup();
                    }
                });
            }, 800);
        }
    }

    // Atualiza Card de Informações
    const elNome = document.getElementById("active-nome");
    const elAz = document.getElementById("active-azimute");
    const elLin = document.getElementById("active-lineamentos");
    const elRes = document.getElementById("active-res");

    if (elNome) elNome.textContent = proj.nome_projeto;
    if (elAz) elAz.textContent = proj.azimute_predominante || "NE-SW (N45E)";
    if (elLin) elLin.textContent = `${proj.total_lineamentos || 120} feições estruturais`;
    if (elRes) elRes.textContent = proj.resolucao;

    // Re-anima o diagrama de roseta centrado no projeto
    animarRosetaParaProjeto(proj);
}

// Exposto globalmente para botões na tabela HTML
window.focarProjetoNoMapa = focarProjetoNoMapa;

window.centralizarProjetoNoMapa = function(projetoId) {
    const mapCard = document.querySelector(".map-card");
    if (mapCard) {
        mapCard.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    focarProjetoNoMapa(projetoId, true);
};

function enquadrarTodosProjetos() {
    if (!mapInstance || analisesCache.length === 0) return;
    const pontos = analisesCache
        .filter(p => p.latitude && p.longitude)
        .map(p => [p.latitude, p.longitude]);

    if (pontos.length > 0) {
        const bounds = L.latLngBounds(pontos);
        mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 10 });
    }
}

// =============================================================================
// 5. Renderizar Tabela de Análises
// =============================================================================
function renderizarTabela(lista) {
    const tabelaCorpo = document.getElementById("tabela-analises-corpo");
    if (!tabelaCorpo) return;

    if (!lista || lista.length === 0) {
        tabelaCorpo.innerHTML = `<tr><td colspan="8" class="table-empty">Nenhuma análise cadastrada até o momento.</td></tr>`;
        return;
    }

    tabelaCorpo.innerHTML = lista.map(item => {
        let statusClasse = "pendente";
        const st = (item.status || "").toLowerCase();
        if (st.includes("conclu")) statusClasse = "concluido";
        else if (st.includes("process")) statusClasse = "processando";

        return `
            <tr>
                <td><span class="code-id">#${item.id}</span></td>
                <td><strong>${escapeHtml(item.nome_projeto)}</strong></td>
                <td><span class="res-tag">${escapeHtml(item.resolucao)}</span></td>
                <td><span class="az-pill">${escapeHtml(item.azimute_predominante || 'NE-SW')}</span></td>
                <td><strong>${item.total_lineamentos || 120}</strong></td>
                <td><span class="status-pill ${statusClasse}">${escapeHtml(item.status)}</span></td>
                <td><span class="code-id">${escapeHtml(item.data_extracao)}</span></td>
                <td style="text-align: center;">
                    <button class="btn btn-secondary btn-sm" onclick="centralizarProjetoNoMapa(${item.id})">
                        Ver no Mapa
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

function atualizarEstatisticas(lista) {
    const statTotal = document.getElementById("stat-total");
    const statConcluidos = document.getElementById("stat-concluidos");
    const statProcessando = document.getElementById("stat-processando");

    if (!statTotal) return;

    const total = lista.length;
    const concluidos = lista.filter(a => (a.status || "").toLowerCase().includes("conclu")).length;
    const processando = lista.filter(a => (a.status || "").toLowerCase().includes("process")).length;

    statTotal.textContent = total;
    statConcluidos.textContent = concluidos;
    statProcessando.textContent = processando;
}

// =============================================================================
// 6. Preset de Regiões no Formulário
// =============================================================================
window.aplicarPresetRegiao = function(valor) {
    const rowCoords = document.getElementById("row-custom-coords");
    const inputLat = document.getElementById("latitude");
    const inputLng = document.getElementById("longitude");

    if (valor === "custom") {
        if (rowCoords) rowCoords.style.display = "flex";
    } else {
        if (rowCoords) rowCoords.style.display = "none";
        const parts = valor.split(",");
        if (parts.length === 2 && inputLat && inputLng) {
            inputLat.value = parseFloat(parts[0].trim());
            inputLng.value = parseFloat(parts[1].trim());
        }
    }
};

// =============================================================================
// 7. Visualizador Canvas: Diagrama de Roseta Geológico
// =============================================================================
const canvas = document.getElementById("rosette-canvas");
const ctx = canvas ? canvas.getContext("2d") : null;

function desenharRoseta(escalaAnimacao = 1, projeto = null) {
    if (!ctx || !canvas) return;

    const width = canvas.width;
    const height = canvas.height;
    const cx = width / 2;
    const cy = height / 2;
    const raioMax = (width / 2) - 28;

    ctx.clearRect(0, 0, width, height);

    // Círculos concêntricos de referência
    ctx.strokeStyle = "rgba(139, 92, 246, 0.18)";
    ctx.lineWidth = 1;
    [0.25, 0.5, 0.75, 1.0].forEach(frac => {
        ctx.beginPath();
        ctx.arc(cx, cy, raioMax * frac, 0, 2 * Math.PI);
        ctx.stroke();
    });

    // Eixos ortogonais N-S e E-W
    ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(cx, cy - raioMax - 8);
    ctx.lineTo(cx, cy + raioMax + 8);
    ctx.moveTo(cx - raioMax - 8, cy);
    ctx.lineTo(cx + raioMax + 8, cy);
    ctx.stroke();
    ctx.setLineDash([]);

    // Rótulos Cardeais
    ctx.fillStyle = "#94a3b8";
    ctx.font = "bold 11px 'Plus Jakarta Sans', sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("N", cx, cy - raioMax - 10);
    ctx.fillText("S", cx, cy + raioMax + 18);
    ctx.fillText("E", cx + raioMax + 14, cy + 4);
    ctx.fillText("W", cx - raioMax - 14, cy + 4);

    // Ajusta pesos das pétalas de acordo com a tendência do projeto ativo
    let pesoNE = 0.85;
    let pesoNW = 0.65;
    let pesoNS = 0.40;
    let pesoEW = 0.35;

    if (projeto && projeto.azimute_predominante) {
        const az = projeto.azimute_predominante.toLowerCase();
        if (az.includes("nw")) {
            pesoNW = 0.95;
            pesoNE = 0.45;
            pesoEW = 0.35;
        } else if (az.includes("e-w")) {
            pesoEW = 0.95;
            pesoNE = 0.40;
            pesoNW = 0.40;
        } else if (az.includes("n-s")) {
            pesoNS = 0.95;
            pesoNE = 0.35;
            pesoNW = 0.35;
        } else {
            pesoNE = 0.95;
            pesoNW = 0.55;
        }
    }

    const petalas = [
        { angulo: 45, comprimento: pesoNE * escalaAnimacao, cor: "rgba(168, 85, 247, 0.55)", borda: "#a855f7" },
        { angulo: 225, comprimento: pesoNE * escalaAnimacao, cor: "rgba(168, 85, 247, 0.55)", borda: "#a855f7" },
        { angulo: 135, comprimento: pesoNW * escalaAnimacao, cor: "rgba(56, 189, 248, 0.55)", borda: "#38bdf8" },
        { angulo: 315, comprimento: pesoNW * escalaAnimacao, cor: "rgba(56, 189, 248, 0.55)", borda: "#38bdf8" },
        { angulo: 0, comprimento: pesoNS * escalaAnimacao, cor: "rgba(16, 185, 129, 0.50)", borda: "#10b981" },
        { angulo: 180, comprimento: pesoNS * escalaAnimacao, cor: "rgba(16, 185, 129, 0.50)", borda: "#10b981" },
        { angulo: 90, comprimento: pesoEW * escalaAnimacao, cor: "rgba(245, 158, 11, 0.50)", borda: "#f59e0b" },
        { angulo: 270, comprimento: pesoEW * escalaAnimacao, cor: "rgba(245, 158, 11, 0.50)", borda: "#f59e0b" }
    ];

    petalas.forEach(p => {
        const rad = (p.angulo - 90) * (Math.PI / 180);
        const abertura = 14 * (Math.PI / 180);
        const r = raioMax * p.comprimento;

        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, r, rad - abertura / 2, rad + abertura / 2);
        ctx.closePath();

        ctx.fillStyle = p.cor;
        ctx.fill();
        ctx.strokeStyle = p.borda;
        ctx.lineWidth = 1.6;
        ctx.stroke();
    });

    // Núcleo central
    ctx.beginPath();
    ctx.arc(cx, cy, 4, 0, 2 * Math.PI);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
}

function animarRosetaParaProjeto(proj) {
    let inicio = null;
    const duracao = 350;

    function passo(timestamp) {
        if (!inicio) inicio = timestamp;
        const progresso = Math.min((timestamp - inicio) / duracao, 1);
        desenharRoseta(progresso, proj);
        if (progresso < 1) {
            requestAnimationFrame(passo);
        }
    }
    requestAnimationFrame(passo);
}

// =============================================================================
// 8. Toast Notifications
// =============================================================================
function mostrarToast(mensagem, tipo = "success") {
    const toastContainer = document.getElementById("toast-container");
    if (!toastContainer) return;

    const toast = document.createElement("div");
    toast.className = `toast ${tipo}`;
    const iconSvg = tipo === "success" 
        ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`
        : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
    toast.innerHTML = `
        <span class="toast-icon">${iconSvg}</span>
        <span>${escapeHtml(mensagem)}</span>
    `;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function escapeHtml(texto) {
    if (!texto) return "";
    return String(texto)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
