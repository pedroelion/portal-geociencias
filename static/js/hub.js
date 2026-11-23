// ==============================================================================
// HUB GEOCIÊNCIAS - TELEMETRIA E CONTROLE
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
    carregarStatusPortal();
});

async function carregarStatusPortal() {
    try {
        const resp = await fetch("/api/portal/status");
        const json = await resp.json();

        if (json.sucesso) {
            // Títulos Minerários
            if (json.titulos) {
                const elProc = document.getElementById("kpi-processos");
                const elOb = document.getElementById("kpi-obrigacoes");
                if (elProc) elProc.textContent = json.titulos.processos || "0";
                if (elOb) elOb.textContent = json.titulos.obrigacoes_pendentes || "0";
            }

            // Lineamentos Estruturais
            if (json.lineamentos) {
                const elAn = document.getElementById("kpi-analises");
                if (elAn) elAn.textContent = json.lineamentos.analises || "0";
            }

            // Status Pill
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
        }
    } catch (e) {
        console.warn("Falha ao consultar telemetria:", e);
        const elStatus = document.getElementById("status-portal-txt");
        if (elStatus) {
            elStatus.textContent = "Servidor Web Puro Ativo";
        }
    }
}
