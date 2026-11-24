// ==============================================================================
// HUB GEOCIÊNCIAS - TELEMETRIA, CONTROLE E PAINEL EXECUTIVO
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
    carregarStatusPortal();
});

async function carregarStatusPortal() {
    try {
        const resp = await fetch("/api/portal/status");
        const json = await resp.json();

        if (json.sucesso) {
            // 1. Títulos Minerários - KPIs
            if (json.titulos) {
                const elProc = document.getElementById("kpi-processos");
                const elOb = document.getElementById("kpi-obrigacoes");
                if (elProc) elProc.textContent = json.titulos.processos || "0";
                if (elOb) elOb.textContent = json.titulos.obrigacoes_pendentes || "0";
            }

            // 2. Lineamentos Estruturais - KPIs
            if (json.lineamentos) {
                const elAn = document.getElementById("kpi-analises");
                if (elAn) elAn.textContent = json.lineamentos.analises || "0";
            }

            // 3. Status Pill Telemetria
            const elStatus = document.getElementById("status-portal-txt");
            if (elStatus) {
                const titAtivo = json.titulos && json.titulos.ativo;
                const linAtivo = json.lineamentos && json.lineamentos.ativo;

                if (titAtivo && linAtivo) {
                    elStatus.textContent = "Todos os Módulos Operacionais (PostGIS + SQLite)";
                    elStatus.style.color = "#34d399";
                } else if (linAtivo) {
                    elStatus.textContent = "SQLite Ativo • PostGIS em Stand-by Local";
                    elStatus.style.color = "#38bdf8";
                } else {
                    elStatus.textContent = "Módulos Prontos para Execução";
                }
            }

            // 4. Painel Executivo: Alertas Críticos ANM em Destaque
            const elAlertas = document.getElementById("hub-alertas-criticos-lista");
            if (elAlertas) {
                if (json.alertas_criticos_destaque && json.alertas_criticos_destaque.length > 0) {
                    elAlertas.innerHTML = json.alertas_criticos_destaque.map(a => {
                        const isVencido = a.nivel_alerta === "Vencido";
                        const diasTxt = isVencido 
                            ? `Vencido há ${Math.abs(a.dias_para_vencer)} dia(s)` 
                            : `Vence em ${a.dias_para_vencer} dia(s)`;
                        const classeBorda = isVencido ? "vencido" : "critico";
                        const badgeClasse = isVencido ? "vencido" : "critico";

                        return `
                            <div class="exec-alert-item ${classeBorda}">
                                <div class="exec-alert-top">
                                    <span class="exec-alert-processo">Processo ${a.numero_processo} &bull; ${a.substancia_mineral}</span>
                                    <span class="badge-status ${badgeClasse}">${a.nivel_alerta}</span>
                                </div>
                                <div class="exec-alert-titular">${a.titular} &bull; ${a.municipio}/${a.uf}</div>
                                <div class="exec-alert-info">
                                    <span>${a.tipo_obrigacao}:</span>
                                    <strong style="color: ${isVencido ? '#ef4444' : '#f59e0b'};">${diasTxt}</strong>
                                </div>
                            </div>
                        `;
                    }).join("");
                } else {
                    elAlertas.innerHTML = `<p class="exec-placeholder">Nenhuma obrigação crítica ou vencida no momento.</p>`;
                }
            }

            // 5. Painel Executivo: Projeto SRTM em Foco
            const elProj = document.getElementById("hub-projeto-foco-content");
            if (elProj) {
                if (json.projeto_srtm_foco) {
                    const p = json.projeto_srtm_foco;
                    elProj.innerHTML = `
                        <div class="exec-project-header">
                            <div>
                                <h4 class="exec-project-name">${p.nome_projeto}</h4>
                                <span class="badge-tech">${p.resolucao}</span>
                            </div>
                            <span class="badge-coord">${p.latitude.toFixed(2)}°, ${p.longitude.toFixed(2)}°</span>
                        </div>
                        <div class="exec-project-grid">
                            <div class="exec-project-stat">
                                <span class="stat-lbl">Orientação Azimutal</span>
                                <strong class="stat-val" style="color: #c084fc;">${p.azimute_predominante}</strong>
                            </div>
                            <div class="exec-project-stat">
                                <span class="stat-lbl">Feições Detectadas</span>
                                <strong class="stat-val">${p.total_lineamentos}</strong>
                            </div>
                            <div class="exec-project-stat">
                                <span class="stat-lbl">Extensão Total</span>
                                <strong class="stat-val">${p.comprimento_total_km} km</strong>
                            </div>
                            <div class="exec-project-stat">
                                <span class="stat-lbl">Densidade de Falhas</span>
                                <strong class="stat-val">${p.densidade_km_km2} km/km²</strong>
                            </div>
                        </div>
                    `;
                } else {
                    elProj.innerHTML = `<p class="exec-placeholder">Nenhum projeto de lineamentos cadastrado.</p>`;
                }
            }
        }
    } catch (e) {
        console.warn("Falha ao consultar telemetria:", e);
        const elStatus = document.getElementById("status-portal-txt");
        if (elStatus) {
            elStatus.textContent = "Servidor Web Puro Ativo";
        }
    }
}
