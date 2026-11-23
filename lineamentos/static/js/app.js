/**
 * SRTM Lineament Studio - Frontend Logic (app.js)
 * Utiliza fetch() nativo para GET e POST nas rotas /api/analises
 */

document.addEventListener("DOMContentLoaded", () => {
    // Elementos da interface
    const formAnalise = document.getElementById("form-analise");
    const tabelaCorpo = document.getElementById("tabela-analises-corpo");
    const btnAtualizar = document.getElementById("btn-atualizar");
    const filtroBusca = document.getElementById("filtro-busca");
    const toastContainer = document.getElementById("toast-container");

    // Elementos de estatísticas
    const statTotal = document.getElementById("stat-total");
    const statConcluidos = document.getElementById("stat-concluidos");
    const statProcessando = document.getElementById("stat-processando");

    // Cache local de análises para busca rápida
    let analisesCache = [];

    // =========================================================================
    // 1. Carregar Análises (GET /api/analises)
    // =========================================================================
    async function carregarAnalises() {
        tabelaCorpo.innerHTML = `<tr><td colspan="5" class="table-loading">Buscando dados no banco SQLite...</td></tr>`;

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
        } catch (erro) {
            console.error("Erro ao carregar análises:", erro);
            tabelaCorpo.innerHTML = `<tr><td colspan="5" class="table-empty" style="color: var(--accent-danger);">Erro ao carregar dados: ${erro.message}</td></tr>`;
            mostrarToast("Não foi possível conectar à API de análises.", "error");
        }
    }

    // =========================================================================
    // 2. Renderizar Tabela e Badges
    // =========================================================================
    function renderizarTabela(lista) {
        if (!lista || lista.length === 0) {
            tabelaCorpo.innerHTML = `<tr><td colspan="5" class="table-empty">Nenhuma análise cadastrada até o momento.</td></tr>`;
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
                    <td><span class="status-pill ${statusClasse}">${escapeHtml(item.status)}</span></td>
                    <td><span class="code-id">${escapeHtml(item.data_extracao)}</span></td>
                </tr>
            `;
        }).join("");
    }

    // =========================================================================
    // 3. Atualizar Indicadores (Cards de Estatísticas)
    // =========================================================================
    function atualizarEstatisticas(lista) {
        const total = lista.length;
        const concluidos = lista.filter(a => (a.status || "").toLowerCase().includes("conclu")).length;
        const processando = lista.filter(a => (a.status || "").toLowerCase().includes("process")).length;

        statTotal.textContent = total;
        statConcluidos.textContent = concluidos;
        statProcessando.textContent = processando;
    }

    // =========================================================================
    // 4. Criar Nova Análise (POST /api/analises)
    // =========================================================================
    formAnalise.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const btnSubmit = document.getElementById("btn-submit");
        const textoOriginal = btnSubmit.innerHTML;

        const nomeProjeto = document.getElementById("nome_projeto").value.trim();
        const resolucao = document.getElementById("resolucao").value;
        const status = document.getElementById("status").value;

        if (!nomeProjeto) {
            mostrarToast("Por favor, preencha o nome do projeto.", "error");
            return;
        }

        const payload = {
            nome_projeto: nomeProjeto,
            resolucao: resolucao,
            status: status
        };

        try {
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = `<span>Processando MDE...</span>`;

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

            mostrarToast("Projeto de extração gravado com sucesso no SQLite!", "success");
            formAnalise.reset();
            await carregarAnalises();
            animarRoseta();
        } catch (erro) {
            console.error("Erro ao enviar análise:", erro);
            mostrarToast(`Falha ao cadastrar: ${erro.message}`, "error");
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = textoOriginal;
        }
    });

    // =========================================================================
    // 5. Filtro de Busca em Tempo Real
    // =========================================================================
    filtroBusca.addEventListener("input", (e) => {
        const termo = e.target.value.toLowerCase().trim();
        if (!termo) {
            renderizarTabela(analisesCache);
            return;
        }

        const filtrados = analisesCache.filter(item => 
            (item.nome_projeto || "").toLowerCase().includes(termo) ||
            (item.resolucao || "").toLowerCase().includes(termo) ||
            (item.status || "").toLowerCase().includes(termo)
        );
        renderizarTabela(filtrados);
    });

    // Botão Atualizar
    btnAtualizar.addEventListener("click", () => {
        carregarAnalises();
        desenharRoseta();
        mostrarToast("Dados sincronizados com o banco SQLite.", "success");
    });

    // =========================================================================
    // 6. Notificações Toast
    // =========================================================================
    function mostrarToast(mensagem, tipo = "success") {
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

    // =========================================================================
    // 7. Visualizador Canvas: Diagrama de Roseta Geológico
    // =========================================================================
    const canvas = document.getElementById("rosette-canvas");
    const ctx = canvas.getContext("2d");

    function desenharRoseta(escalaAnimacao = 1) {
        const width = canvas.width;
        const height = canvas.height;
        const cx = width / 2;
        const cy = height / 2;
        const raioMax = (width / 2) - 30;

        ctx.clearRect(0, 0, width, height);

        // Círculos concêntricos de referência (10%, 20%, 30%, 40%)
        ctx.strokeStyle = "#273449";
        ctx.lineWidth = 1;
        [0.25, 0.5, 0.75, 1.0].forEach(frac => {
            ctx.beginPath();
            ctx.arc(cx, cy, raioMax * frac, 0, 2 * Math.PI);
            ctx.stroke();
        });

        // Eixos ortogonais N-S e E-W
        ctx.strokeStyle = "#334155";
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(cx, cy - raioMax - 10);
        ctx.lineTo(cx, cy + raioMax + 10);
        ctx.moveTo(cx - raioMax - 10, cy);
        ctx.lineTo(cx + raioMax + 10, cy);
        ctx.stroke();
        ctx.setLineDash([]);

        // Rótulos Cardeais
        ctx.fillStyle = "#94a3b8";
        ctx.font = "bold 11px 'Plus Jakarta Sans', sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("N", cx, cy - raioMax - 12);
        ctx.fillText("S", cx, cy + raioMax + 20);
        ctx.fillText("E", cx + raioMax + 16, cy + 4);
        ctx.fillText("W", cx - raioMax - 16, cy + 4);

        // Pétalas azimutais simuladas baseadas em tendências estruturais brasileiras (NE-SW predominante)
        const petalas = [
            { angulo: 45, comprimento: 0.85 * escalaAnimacao, cor: "rgba(16, 185, 129, 0.45)", borda: "#10b981" },   // NE
            { angulo: 225, comprimento: 0.85 * escalaAnimacao, cor: "rgba(16, 185, 129, 0.45)", borda: "#10b981" },  // SW
            { angulo: 135, comprimento: 0.65 * escalaAnimacao, cor: "rgba(56, 189, 248, 0.45)", borda: "#38bdf8" },  // SE
            { angulo: 315, comprimento: 0.65 * escalaAnimacao, cor: "rgba(56, 189, 248, 0.45)", borda: "#38bdf8" },  // NW
            { angulo: 0, comprimento: 0.40 * escalaAnimacao, cor: "rgba(251, 191, 36, 0.35)", borda: "#fbbf24" },    // N
            { angulo: 180, comprimento: 0.40 * escalaAnimacao, cor: "rgba(251, 191, 36, 0.35)", borda: "#fbbf24" },  // S
            { angulo: 90, comprimento: 0.30 * escalaAnimacao, cor: "rgba(168, 85, 247, 0.35)", borda: "#a855f7" },   // E
            { angulo: 270, comprimento: 0.30 * escalaAnimacao, cor: "rgba(168, 85, 247, 0.35)", borda: "#a855f7" }   // W
        ];

        petalas.forEach(p => {
            const rad = (p.angulo - 90) * (Math.PI / 180);
            const abertura = 15 * (Math.PI / 180);
            const r = raioMax * p.comprimento;

            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, r, rad - abertura / 2, rad + abertura / 2);
            ctx.closePath();

            ctx.fillStyle = p.cor;
            ctx.fill();
            ctx.strokeStyle = p.borda;
            ctx.lineWidth = 1.5;
            ctx.stroke();
        });

        // Núcleo central
        ctx.beginPath();
        ctx.arc(cx, cy, 4, 0, 2 * Math.PI);
        ctx.fillStyle = "#ffffff";
        ctx.fill();
    }

    function animarRoseta() {
        let inicio = null;
        const duracao = 400; // ms

        function passo(timestamp) {
            if (!inicio) inicio = timestamp;
            const progresso = Math.min((timestamp - inicio) / duracao, 1);
            desenharRoseta(progresso);
            if (progresso < 1) {
                requestAnimationFrame(passo);
            }
        }
        requestAnimationFrame(passo);
    }

    // Inicialização ao carregar a página
    carregarAnalises();
    desenharRoseta();
});
