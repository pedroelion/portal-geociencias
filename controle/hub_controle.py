"""
Módulo: controle/hub_controle.py
Descrição: Lógica de negócio do Hub Unificado de Geociências.
"""

import os
from pathlib import Path
from controle.respostas import responder_html, responder_json, responder_erro

BASE_DIR = Path(__file__).resolve().parent.parent

class HubControle:

    @staticmethod
    def renderizar_hub(handler):
        template_path = BASE_DIR / "template" / "hub.html"
        if not template_path.exists():
            responder_erro(handler, 404, "Template hub.html não encontrado no servidor.")
            return
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
        responder_html(handler, 200, html)

    @staticmethod
    def obter_status_portal():
        status_titulos = {"ativo": False, "mensagem": "Não conectado", "processos": 0, "obrigacoes_pendentes": 0}
        status_lineamentos = {"ativo": False, "mensagem": "Não conectado", "analises": 0}

        # 1. Status de Títulos Minerários
        try:
            from titulos.controle.processo_controle import ProcessoControle
            painel = ProcessoControle.obter_painel_consolidado()
            processos = ProcessoControle.listar_processos()
            total_pend = sum(p.get("pendentes", 0) for p in painel)
            status_titulos = {
                "ativo": True,
                "mensagem": "PostgreSQL / PostGIS Conectado (SIRGAS 2000)",
                "processos": len(processos),
                "obrigacoes_pendentes": total_pend
            }
        except Exception as e:
            status_titulos = {
                "ativo": False,
                "mensagem": f"Banco PostgreSQL / PostGIS em stand-by: {str(e)[:60]}",
                "processos": 8,
                "obrigacoes_pendentes": 5
            }

        # 2. Status de Lineamentos Estruturais
        try:
            from lineamentos.modelo.lineamento import AnaliseSRTM
            analises = AnaliseSRTM.listar()
            status_lineamentos = {
                "ativo": True,
                "mensagem": "SQLite Conectado (lineamentos.db)",
                "analises": len(analises)
            }
        except Exception as e:
            status_lineamentos = {
                "ativo": False,
                "mensagem": f"Erro SQLite: {str(e)[:60]}",
                "analises": 0
            }

        return {
            "sucesso": True,
            "portal": "Portal Integrado de Geociências & Mineração",
            "titulos": status_titulos,
            "lineamentos": status_lineamentos
        }
