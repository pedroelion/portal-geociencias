from pathlib import Path
from datetime import datetime
try:
    from lineamentos.modelo.lineamento import AnaliseSRTM
except ImportError:
    from modelo.lineamento import AnaliseSRTM
try:
    from lineamentos.controle.respostas import responder_html, responder_json, responder_erro
except ImportError:
    from controle.respostas import responder_html, responder_json, responder_erro

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_INDEX = BASE_DIR / "template" / "index.html"

def renderizar_index(handler):
    """Renderiza a página inicial index.html."""
    if not TEMPLATE_INDEX.exists():
        responder_erro(handler, 404, "Template index.html não foi encontrado no servidor.")
        return

    try:
        with open(TEMPLATE_INDEX, "r", encoding="utf-8") as f:
            conteudo = f.read()
        responder_html(handler, conteudo)
    except Exception as e:
        responder_erro(handler, 500, f"Falha ao carregar o template HTML: {str(e)}")

def listar_analises(handler):
    """Retorna a lista de análises de lineamentos em formato JSON."""
    try:
        analises = AnaliseSRTM.listar()
        dados = [a.to_dict() for a in analises]
        responder_json(handler, {
            "sucesso": True,
            "total": len(dados),
            "analises": dados
        })
    except Exception as e:
        responder_erro(handler, 500, f"Erro ao consultar análises no banco: {str(e)}")

def criar_analise(handler, payload: dict):
    """Processa a criação de uma nova análise a partir do payload recebido."""
    if not payload:
        responder_erro(handler, 400, "Corpo da requisição vazio ou formato JSON inválido.")
        return

    nome_projeto = payload.get("nome_projeto", "").strip()
    resolucao = payload.get("resolucao", "").strip()
    status = payload.get("status", "Concluído").strip()
    data_extracao = payload.get("data_extracao", "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not nome_projeto:
        responder_erro(handler, 422, "O campo 'nome_projeto' é obrigatório.")
        return

    if not resolucao:
        resolucao = "SRTM 30m (1 arc-sec)"

    try:
        nova_analise = AnaliseSRTM(
            nome_projeto=nome_projeto,
            resolucao=resolucao,
            status=status,
            data_extracao=data_extracao
        )
        nova_analise.salvar()

        responder_json(handler, {
            "sucesso": True,
            "mensagem": "Análise de lineamentos cadastrada com sucesso!",
            "analise": nova_analise.to_dict()
        }, status=201)
    except Exception as e:
        responder_erro(handler, 500, f"Erro ao salvar a análise no banco: {str(e)}")
