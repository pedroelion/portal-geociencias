/* ==============================================================================
   LÓGICA JAVASCRIPT - SISTEMA DE GESTÃO DE TÍTULOS MINERÁRIOS
   ============================================================================== */

let mapInstance = null;
let geojsonLayer = null;
let todosProcessos = [];

document.addEventListener("DOMContentLoaded", () => {
    inicializarMapa();
    carregarPainel();
    carregarAlertasUrgentes();
    carregarProcessos();
    carregarEventos();
    carregarObrigacoes();
    carregarSelectProcessos();
});

let camadaGrade = null;

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

// Grade Georreferenciada / Cartográfica (Fallback Visual e Cartográfico em SIRGAS 2000)
function criarGradeCartografica(map) {
    const graticule = L.layerGroup();

    function desenharGrade() {
        graticule.clearLayers();
        if (!map) return;

        const bounds = map.getBounds();
        const zoom = map.getZoom();

        // Determina espaçamento da grade com base no nível de zoom
        let passo = 5;
        if (zoom >= 11) passo = 0.05;
        else if (zoom >= 9) passo = 0.2;
        else if (zoom >= 7) passo = 0.5;
        else if (zoom >= 5) passo = 1.0;
        else if (zoom >= 3) passo = 2.5;
        else passo = 5;

        const sul = Math.max(-60, Math.floor(bounds.getSouth() / passo) * passo);
        const norte = Math.min(15, Math.ceil(bounds.getNorth() / passo) * passo);
        const oeste = Math.max(-85, Math.floor(bounds.getWest() / passo) * passo);
        const leste = Math.min(-30, Math.ceil(bounds.getEast() / passo) * passo);

        const estiloLinha = {
            color: 'rgba(56, 189, 248, 0.22)',
            weight: 1,
            dashArray: '2, 4',
            interactive: false
        };

        // Paralelos (Latitudes)
        for (let lat = sul; lat <= norte; lat += passo) {
            const latArred = Math.round(lat * 1000) / 1000;
            const linha = L.polyline([[latArred, oeste], [latArred, leste]], estiloLinha);
            graticule.addLayer(linha);

            const rotuloLat = latArred === 0 ? "0° (Equador)" : `${Math.abs(latArred)}°${latArred < 0 ? 'S' : 'N'}`;
            const marcador = L.marker([latArred, oeste + (leste - oeste) * 0.02], {
                icon: L.divIcon({
                    className: 'graticule-label',
                    html: `<span>${rotuloLat}</span>`,
                    iconSize: [42, 14],
                    iconAnchor: [0, 7]
                }),
                interactive: false
            });
            graticule.addLayer(marcador);
        }

        // Meridianos (Longitudes)
        for (let lng = oeste; lng <= leste; lng += passo) {
            const lngArred = Math.round(lng * 1000) / 1000;
            const linha = L.polyline([[sul, lngArred], [norte, lngArred]], estiloLinha);
            graticule.addLayer(linha);

            const rotuloLng = `${Math.abs(lngArred)}°${lngArred < 0 ? 'W' : 'E'}`;
            const marcador = L.marker([sul + (norte - sul) * 0.04, lngArred], {
                icon: L.divIcon({
                    className: 'graticule-label',
                    html: `<span>${rotuloLng}</span>`,
                    iconSize: [42, 14],
                    iconAnchor: [21, 0]
                }),
                interactive: false
            });
            graticule.addLayer(marcador);
        }
    }

    map.on('moveend zoomend', desenharGrade);
    desenharGrade();
    return graticule;
}

// 1. Inicialização do Mapa Leaflet com Camadas Livres (Sem API Key)
function inicializarMapa() {
    mapInstance = L.map("map", {
        zoomControl: true,
        attributionControl: true
    }).setView([-15.7801, -47.9292], 4); // Centro do Brasil

    // Provedores de Basemap Livres (Sem necessidade de API Key)
    // 1.1. Esri Dark Gray (Tema escuro profissional para GIS)
    const esriDark = criarTileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 16, attribution: "Esri Dark Gray &bull; Sem API Key" }
    );

    // 1.2. OpenStreetMap Padrão
    const osm = criarTileLayer(
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        { maxZoom: 19, attribution: "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a>" }
    );

    // 1.3. Esri World Imagery (Satélite Alta Resolução)
    const esriSat = criarTileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 19, attribution: "Esri World Imagery (Satélite)" }
    );

    // 1.4. Esri World Topo
    const esriTopo = criarTileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 19, attribution: "Esri Topográfico" }
    );

    // 1.5. Fundo Cartográfico Puro (Offline / Sem Tiles de Rede)
    const gradeOffline = L.layerGroup();

    // Ativa Esri Dark Gray por padrão
    esriDark.addTo(mapInstance);

    // 2. Grade de Coordenadas Geográficas (SIRGAS 2000)
    camadaGrade = criarGradeCartografica(mapInstance);
    camadaGrade.addTo(mapInstance);

    // 3. Controle de Camadas
    const baseMaps = {
        "🗺️ Esri Dark Gray (Elegante)": esriDark,
        "🌍 OpenStreetMap (Padrão)": osm,
        "🛰️ Satélite Esri (Alta Resolução)": esriSat,
        "🏔️ Esri Topográfico": esriTopo,
        "📐 Grade Cartográfica (Modo Offline)": gradeOffline
    };

    const overlayMaps = {
        "🌐 Grade de Coordenadas (SIRGAS 2000)": camadaGrade
    };

    L.control.layers(baseMaps, overlayMaps, {
        position: "topright",
        collapsed: true
    }).addTo(mapInstance);

    // 4. Barra de Escala Métrica Oficial
    L.control.scale({
        metric: true,
        imperial: false,
        position: "bottomleft"
    }).addTo(mapInstance);

    carregarGeoJSON();
}

// 2. Carregar Camada Espacial GeoJSON do PostGIS
async function carregarGeoJSON() {
    try {
        const resp = await fetch("/api/situacao-espacial");
        const data = await resp.json();

        if (geojsonLayer) {
            mapInstance.removeLayer(geojsonLayer);
        }

        geojsonLayer = L.geoJSON(data, {
            style: (feature) => {
                const alerta = feature.properties.pior_nivel_alerta;
                let cor = "#10b981"; // No Prazo (Verde)
                let corBorda = "#047857";

                if (alerta === "Vencido") {
                    cor = "#ef4444"; // Vermelho
                    corBorda = "#b91c1c";
                } else if (alerta === "Alerta Crítico / Próximo ao Vencimento") {
                    cor = "#f59e0b"; // Âmbar / Laranja
                    corBorda = "#b45309";
                } else if (alerta === "Cumprido / Regular") {
                    cor = "#3b82f6"; // Azul
                    corBorda = "#1d4ed8";
                } else if (alerta === "Sem Obrigações Registradas") {
                    cor = "#94a3b8"; // Cinza
                    corBorda = "#475569";
                }

                return {
                    fillColor: cor,
                    fillOpacity: 0.65,
                    color: corBorda,
                    weight: 2.2,
                    dashArray: ""
                };
            },
            onEachFeature: (feature, layer) => {
                const p = feature.properties;

                // Tooltip informativo no hover
                layer.bindTooltip(`
                    <div style="font-weight: 600; font-size: 12px;">Processo ${p.numero_processo}</div>
                    <div style="font-size: 11px; color: #cbd5e1;">${p.substancia_mineral} &bull; <span style="color:${getCorAlerta(p.pior_nivel_alerta)}; font-weight: 600;">${p.pior_nivel_alerta}</span></div>
                `, {
                    direction: "top",
                    className: "map-tooltip",
                    sticky: true
                });

                // Popup detalhado com dados cadastrais e prazos
                const popupContent = `
                    <div style="font-family: 'Inter', sans-serif; min-width: 240px; color: #f8fafc;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.12); padding-bottom: 6px; margin-bottom: 8px;">
                            <h4 style="margin: 0; color: #38bdf8; font-size: 14px;">ANM: ${p.numero_processo}</h4>
                            <span style="font-size: 10px; background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; font-family: monospace;">EPSG:4674</span>
                        </div>
                        <p style="margin: 3px 0; font-size: 12px;"><strong>Titular:</strong> ${p.titular_razao_social}</p>
                        <p style="margin: 3px 0; font-size: 12px;"><strong>Fase:</strong> ${p.fase}</p>
                        <p style="margin: 3px 0; font-size: 12px;"><strong>Substância:</strong> ${p.substancia_mineral} (${p.uso_substancia || 'Geral'})</p>
                        <p style="margin: 3px 0; font-size: 12px;"><strong>Área:</strong> ${p.area_ha ? p.area_ha.toLocaleString("pt-BR") : '-'} ha</p>
                        <p style="margin: 3px 0; font-size: 12px;"><strong>Município:</strong> ${p.municipio}/${p.uf}</p>
                        <hr style="margin: 8px 0; border: none; border-top: 1px solid rgba(255,255,255,0.1);" />
                        <p style="margin: 3px 0; font-size: 12px;"><strong>Situação de Prazo:</strong> 
                            <span style="font-weight: 700; color: ${getCorAlerta(p.pior_nivel_alerta)};">${p.pior_nivel_alerta}</span>
                        </p>
                        ${p.proxima_obrigacao_tipo ? `
                            <p style="margin: 4px 0 0; font-size: 11px; color: #94a3b8; background: rgba(0,0,0,0.25); padding: 5px 8px; border-radius: 4px; border-left: 3px solid ${getCorAlerta(p.proxima_obrigacao_alerta || p.pior_nivel_alerta)};">
                                Próxima Obrigação: <strong>${p.proxima_obrigacao_tipo}</strong><br>
                                Vencimento em: <strong>${p.proxima_obrigacao_dias !== null ? p.proxima_obrigacao_dias + ' dias' : '-'}</strong>
                            </p>
                        ` : ''}
                    </div>
                `;
                layer.bindPopup(popupContent);

                layer.on("mouseover", () => layer.setStyle({ fillOpacity: 0.88, weight: 3.2 }));
                layer.on("mouseout", () => geojsonLayer.resetStyle(layer));
            }
        }).addTo(mapInstance);

        ajustarZoomPoligonais();
    } catch (e) {
        console.error("Erro ao carregar GeoJSON:", e);
    }
}

function getCorAlerta(alerta) {
    if (alerta === "Vencido") return "#ef4444";
    if (alerta === "Alerta Crítico / Próximo ao Vencimento") return "#f59e0b";
    if (alerta === "No Prazo") return "#10b981";
    if (alerta === "Cumprido / Regular") return "#3b82f6";
    return "#94a3b8";
}

// 3. Carregar KPIs e Painel Consolidado
async function carregarPainel() {
    try {
        const resp = await fetch("/api/painel");
        const json = await resp.json();
        if (!json.sucesso) return;

        const painel = json.painel;
        const tbody = document.getElementById("corpo-tabela-painel");
        tbody.innerHTML = "";

        let totalGeral = 0;
        let vencidasGeral = 0;
        let criticosGeral = 0;
        let prazoGeral = 0;
        let cumpridasGeral = 0;

        painel.forEach(item => {
            totalGeral += parseInt(item.total_obrigacoes || 0);
            vencidasGeral += parseInt(item.vencidas || 0);
            criticosGeral += parseInt(item.alerta_critico || 0);
            prazoGeral += parseInt(item.no_prazo || 0);
            cumpridasGeral += parseInt(item.cumpridas || 0);

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${item.tipo_obrigacao}</strong></td>
                <td>${item.total_obrigacoes}</td>
                <td><span class="badge-status neutral">${item.pendentes}</span></td>
                <td><span class="badge-status vencido">${item.vencidas}</span></td>
                <td><span class="badge-status critico">${item.alerta_critico}</span></td>
                <td><span class="badge-status prazo">${item.no_prazo}</span></td>
                <td><span class="badge-status cumprido">${item.cumpridas}</span></td>
                <td>R$ ${parseFloat(item.valor_total_pendente || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}</td>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>${item.conformidade_percentual}%</span>
                        <div style="flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                            <div style="width: ${item.conformidade_percentual}%; height: 100%; background: #06d6a0;"></div>
                        </div>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Atualiza KPI cards
        document.getElementById("val-vencidas").innerText = vencidasGeral;
        document.getElementById("val-criticos").innerText = criticosGeral;
        document.getElementById("val-no-prazo").innerText = prazoGeral;
        const conformidade = totalGeral > 0 ? ((cumpridasGeral / totalGeral) * 100).toFixed(1) : 0;
        document.getElementById("val-conformidade").innerText = `${conformidade}%`;

    } catch (e) {
        console.error("Erro ao carregar painel:", e);
    }
}

// 4. Carregar Alertas Urgentes
async function carregarAlertasUrgentes() {
    try {
        const resp = await fetch("/api/alertas-urgentes");
        const json = await resp.json();
        if (!json.sucesso) return;

        const alertas = json.alertas;
        const container = document.getElementById("lista-alertas-urgentes");
        const badge = document.getElementById("badge-urgentes");
        badge.innerText = alertas.length;

        if (alertas.length === 0) {
            container.innerHTML = '<p class="placeholder-text">Nenhuma obrigação crítica ou vencida no momento.</p>';
            return;
        }

        container.innerHTML = "";
        alertas.forEach(a => {
            const isVencido = a.nivel_alerta === "Vencido";
            const diasTxt = isVencido 
                ? `Vencido há ${Math.abs(a.dias_para_vencer)} dia(s)` 
                : `Vence em ${a.dias_para_vencer} dia(s)`;

            const div = document.createElement("div");
            div.className = `alert-item ${isVencido ? 'vencido' : 'critico'}`;
            div.innerHTML = `
                <div class="alert-item-header">
                    <span class="alert-processo">${a.numero_processo} (${a.substancia_mineral})</span>
                    <span class="alert-days">${diasTxt}</span>
                </div>
                <div class="alert-titular">${a.titular} • ${a.municipio}/${a.uf}</div>
                <div class="alert-tipo">${a.tipo_obrigacao}</div>
                <div class="alert-desc">${a.descricao || a.observacoes || 'Sem observações adicionais.'}</div>
                <div style="margin-top: 8px; display: flex; justify-content: flex-end;">
                    <button class="btn btn-secondary btn-sm" onclick="cumprirObrigacao(${a.obrigacao_id})">✓ Dar Baixa</button>
                </div>
            `;
            container.appendChild(div);
        });

    } catch (e) {
        console.error("Erro ao carregar alertas urgentes:", e);
    }
}

// 5. Carregar Processos
async function carregarProcessos() {
    try {
        const filtroAlerta = document.getElementById("filtro-alerta-processo").value;
        let url = "/api/processos";
        if (filtroAlerta) url += `?alerta=${encodeURIComponent(filtroAlerta)}`;

        const resp = await fetch(url);
        const json = await resp.json();
        if (!json.sucesso) return;

        todosProcessos = json.processos;
        document.getElementById("val-total-processos").innerText = todosProcessos.length;
        renderizarTabelaProcessos(todosProcessos);

    } catch (e) {
        console.error("Erro ao carregar processos:", e);
    }
}

function renderizarTabelaProcessos(processos) {
    const tbody = document.getElementById("corpo-tabela-processos");
    tbody.innerHTML = "";

    if (processos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="loading">Nenhum processo encontrado.</td></tr>';
        return;
    }

    processos.forEach(p => {
        let classeBadge = "prazo";
        if (p.pior_nivel_alerta === "Vencido") classeBadge = "vencido";
        else if (p.pior_nivel_alerta === "Alerta Crítico / Próximo ao Vencimento") classeBadge = "critico";
        else if (p.pior_nivel_alerta === "Cumprido / Regular") classeBadge = "cumprido";

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${p.numero_processo}</strong></td>
            <td>${p.titular_razao_social}</td>
            <td>${p.fase}</td>
            <td>${p.substancia_mineral}</td>
            <td>${p.area_ha.toLocaleString("pt-BR")} ha</td>
            <td>${p.municipio}/${p.uf}</td>
            <td><span class="badge-status ${classeBadge}">${p.pior_nivel_alerta}</span></td>
            <td>
                ${p.proxima_obrigacao_tipo ? `
                    <span style="font-size: 11px;">${p.proxima_obrigacao_tipo} (${p.proxima_obrigacao_dias}d)</span>
                ` : '<span style="color: #64748b;">-</span>'}
            </td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="centralizarMapa(${p.processo_id})">📍 Mapa</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filtrarTabelaProcessos() {
    const termo = document.getElementById("filtro-busca-processo").value.toLowerCase();
    const filtrados = todosProcessos.filter(p => 
        p.numero_processo.toLowerCase().includes(termo) ||
        p.titular_razao_social.toLowerCase().includes(termo) ||
        p.substancia_mineral.toLowerCase().includes(termo) ||
        p.municipio.toLowerCase().includes(termo)
    );
    renderizarTabelaProcessos(filtrados);
}

// 6. Carregar Eventos
async function carregarEventos() {
    try {
        const resp = await fetch("/api/eventos");
        const json = await resp.json();
        if (!json.sucesso) return;

        const tbody = document.getElementById("corpo-tabela-eventos");
        tbody.innerHTML = "";

        json.eventos.forEach(e => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${formatarData(e.data_evento)}</td>
                <td><strong>${e.numero_processo}</strong></td>
                <td>${e.tipo_evento}</td>
                <td>${e.documento_sei || '-'}</td>
                <td>${e.responsavel || '-'}</td>
                <td>${e.descricao || '-'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Erro ao carregar eventos:", e);
    }
}

// 7. Carregar Obrigações
async function carregarObrigacoes() {
    try {
        const resp = await fetch("/api/obrigacoes");
        const json = await resp.json();
        if (!json.sucesso) return;

        const tbody = document.getElementById("corpo-tabela-obrigacoes");
        tbody.innerHTML = "";

        json.obrigacoes.forEach(o => {
            let classeBadge = "prazo";
            if (o.nivel_alerta === "Vencido") classeBadge = "vencido";
            else if (o.nivel_alerta === "Alerta Crítico / Próximo ao Vencimento") classeBadge = "critico";
            else if (o.nivel_alerta === "Cumprido") classeBadge = "cumprido";

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${o.numero_processo}</strong></td>
                <td>${o.tipo_obrigacao}</td>
                <td>${formatarData(o.data_vencimento)}</td>
                <td><strong>${o.dias_para_vencer !== null ? o.dias_para_vencer + ' dias' : '-'}</strong></td>
                <td><span class="badge-status ${classeBadge}">${o.nivel_alerta}</span></td>
                <td>${o.valor_devido > 0 ? 'R$ ' + o.valor_devido.toLocaleString("pt-BR", { minimumFractionDigits: 2 }) : '-'}</td>
                <td><span class="badge-status neutral">${o.status}</span></td>
                <td>
                    ${o.status === 'Pendente' ? `
                        <button class="btn btn-secondary btn-sm" onclick="cumprirObrigacao(${o.id})">✓ Baixa</button>
                    ` : '<span style="color: #06d6a0;">Concluído</span>'}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Erro ao carregar obrigações:", e);
    }
}

// 8. Funções de Modal e Cadastro de Evento
async function carregarSelectProcessos() {
    try {
        const resp = await fetch("/api/processos");
        const json = await resp.json();
        if (!json.sucesso) return;

        const select = document.getElementById("ev-processo-id");
        select.innerHTML = '<option value="">Selecione o processo...</option>';
        json.processos.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.processo_id;
            opt.innerText = `${p.numero_processo} - ${p.substancia_mineral} (${p.titular_razao_social})`;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error("Erro ao popular select de processos:", e);
    }
}

function abrirModalEvento() {
    document.getElementById("modal-evento").classList.add("active");
    document.getElementById("ev-data-evento").valueAsDate = new Date();
}

function fecharModalEvento() {
    document.getElementById("modal-evento").classList.remove("active");
}

async function enviarNovoEvento(event) {
    event.preventDefault();
    const btn = document.getElementById("btn-salvar-evento");
    btn.disabled = true;
    btn.innerText = "Registrando e disparando triggers...";

    const payload = {
        processo_id: parseInt(document.getElementById("ev-processo-id").value),
        tipo_evento: document.getElementById("ev-tipo-evento").value,
        data_evento: document.getElementById("ev-data-evento").value,
        documento_sei: document.getElementById("ev-documento-sei").value,
        responsavel: document.getElementById("ev-responsavel").value,
        descricao: document.getElementById("ev-descricao").value
    };

    try {
        const resp = await fetch("/api/eventos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const res = await resp.json();

        if (res.sucesso) {
            alert("✓ " + res.mensagem);
            fecharModalEvento();
            // Atualiza todos os dados
            carregarPainel();
            carregarAlertasUrgentes();
            carregarProcessos();
            carregarEventos();
            carregarObrigacoes();
            carregarGeoJSON();
        } else {
            alert("Erro: " + res.erro);
        }
    } catch (e) {
        alert("Falha de comunicação: " + e.message);
    } finally {
        btn.disabled = false;
        btn.innerText = "Salvar Evento";
    }
}

async function cumprirObrigacao(obrigacaoId) {
    if (!confirm("Confirmar cumprimento e baixa desta obrigação legal?")) return;

    try {
        const resp = await fetch(`/api/obrigacoes/${obrigacaoId}/cumprir`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({})
        });
        const res = await resp.json();
        if (res.sucesso) {
            alert("✓ Obrigação baixada com sucesso!");
            carregarPainel();
            carregarAlertasUrgentes();
            carregarProcessos();
            carregarObrigacoes();
            carregarGeoJSON();
        } else {
            alert("Erro: " + res.erro);
        }
    } catch (e) {
        alert("Falha ao cumprir obrigação: " + e.message);
    }
}

// 9. Abas e Utilitários
function trocarAba(abaId) {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

    event.target.classList.add("active");
    document.getElementById(abaId).classList.add("active");
}

function formatarData(dataStr) {
    if (!dataStr) return "-";
    const partes = dataStr.split("-");
    if (partes.length === 3) {
        return `${partes[2]}/${partes[1]}/${partes[0]}`;
    }
    return dataStr;
}

function centralizarMapa(processoId) {
    if (!geojsonLayer) return;
    geojsonLayer.eachLayer(layer => {
        if (layer.feature && layer.feature.properties && layer.feature.properties.processo_id === processoId) {
            mapInstance.fitBounds(layer.getBounds(), { maxZoom: 13 });
            layer.openPopup();
        }
    });
}

function ajustarZoomPoligonais() {
    if (geojsonLayer && geojsonLayer.getLayers().length > 0) {
        mapInstance.fitBounds(geojsonLayer.getBounds(), { padding: [35, 35] });
    }
}

