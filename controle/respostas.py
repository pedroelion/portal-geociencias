"""
Módulo: controle/respostas.py
Descrição: Utilitários HTTP padronizados para o Portal de Geociências (Python Standard Library).
"""

import os
import json
import mimetypes
from decimal import Decimal
from datetime import date, datetime

def serializador_json(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return str(obj)

def responder_json(handler, status_code, dados):
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
    corpo = html_content.encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(corpo)))
    handler.end_headers()
    handler.wfile.write(corpo)

def responder_erro(handler, status_code, mensagem):
    responder_json(handler, status_code, {"sucesso": False, "erro": mensagem})

def servir_arquivo_estatico(handler, filepath, content_type=None):
    if not os.path.exists(filepath) or os.path.isdir(filepath):
        handler.send_error(404, f"Arquivo estático '{os.path.basename(filepath)}' não encontrado")
        return

    if not content_type:
        content_type, _ = mimetypes.guess_type(filepath)
        if not content_type:
            content_type = "application/octet-stream"
        if filepath.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif filepath.endswith(".js"):
            content_type = "application/javascript; charset=utf-8"

    with open(filepath, "rb") as f:
        conteudo = f.read()

    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(conteudo)))
    handler.send_header("Cache-Control", "public, max-age=3600")
    handler.end_headers()
    handler.wfile.write(conteudo)
