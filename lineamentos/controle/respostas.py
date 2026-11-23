import json
import mimetypes
import os
from pathlib import Path

def responder_html(handler, conteudo: str, status: int = 200):
    """Envia uma resposta HTTP com corpo HTML UTF-8."""
    corpo = conteudo.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(corpo)))
    handler.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
    handler.end_headers()
    handler.wfile.write(corpo)

def responder_json(handler, dados, status: int = 200):
    """Envia uma resposta HTTP formatada em JSON UTF-8."""
    corpo = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(corpo)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    handler.wfile.write(corpo)

def responder_estatico(handler, caminho_arquivo: Path):
    """Lê e envia arquivos estáticos (CSS, JS, imagens, ícones) com tipo MIME correto."""
    if not caminho_arquivo.is_file():
        responder_erro(handler, 404, f"Arquivo estático '{caminho_arquivo.name}' não encontrado.")
        return

    mime_type, _ = mimetypes.guess_type(str(caminho_arquivo))
    if mime_type is None:
        mime_type = "application/octet-stream"

    try:
        with open(caminho_arquivo, "rb") as f:
            conteudo = f.read()

        handler.send_response(200)
        handler.send_header("Content-Type", mime_type)
        handler.send_header("Content-Length", str(len(conteudo)))
        handler.send_header("Cache-Control", "public, max-age=3600")
        handler.end_headers()
        handler.wfile.write(conteudo)
    except Exception as e:
        responder_erro(handler, 500, f"Erro ao ler arquivo estático: {str(e)}")

def responder_erro(handler, codigo: int, mensagem: str):
    """Envia uma resposta de erro padronizada."""
    resposta = {
        "erro": True,
        "codigo": codigo,
        "mensagem": mensagem
    }
    responder_json(handler, resposta, status=codigo)
