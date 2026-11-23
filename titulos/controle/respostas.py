"""
Módulo: controle/respostas.py
Descrição: Funções auxiliares para padronização de respostas HTTP (JSON, HTML, estáticos).
"""

import os
import json

from decimal import Decimal
from datetime import date, datetime

def serializador_json(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return str(obj)

def responder_json(handler, status_code, dados):
    """Envia resposta JSON com cabeçalhos apropriados."""
    corpo = json.dumps(dados, ensure_ascii=False, indent=2, default=serializador_json).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(corpo)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(corpo)

def responder_html(handler, status_code, html_content):
    """Envia resposta HTML."""
    corpo = html_content.encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(corpo)))
    handler.end_headers()
    handler.wfile.write(corpo)

def responder_erro(handler, status_code, mensagem):
    """Envia mensagem de erro em formato JSON."""
    responder_json(handler, status_code, {"sucesso": False, "erro": mensagem})

def servir_arquivo_estatico(handler, filepath, content_type):
    """Lê e envia arquivo estático do disco."""
    if not os.path.exists(filepath):
        handler.send_error(404, "Arquivo nao encontrado")
        return
    with open(filepath, "rb") as f:
        conteudo = f.read()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(conteudo)))
    handler.end_headers()
    handler.wfile.write(conteudo)
