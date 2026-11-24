"""
Módulo: rotas/rotas.py
Descrição: Roteador HTTP unificado em Python puro gerenciando o Hub, Sistema de Títulos e Lineamentos.
"""

import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from controle.hub_controle import HubControle
from controle.respostas import responder_json, responder_html, responder_erro, servir_arquivo_estatico

BASE_DIR = Path(__file__).resolve().parent.parent
TITULOS_DIR = BASE_DIR / "titulos"
LINEAMENTOS_DIR = BASE_DIR / "lineamentos"
STATIC_DIR = BASE_DIR / "static"

class RoteadorPortal(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {self.client_address[0]} - {format % args}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        try:
            # 1. Hub Principal
            if path in ["/", "/index.html"]:
                HubControle.renderizar_hub(self)
                return

            # 2. Status Geral do Portal
            if path == "/api/portal/status":
                dados = HubControle.obter_status_portal()
                responder_json(self, 200, dados)
                return

            # 3. Interface: Títulos Minerários (/titulos)
            if path in ["/titulos", "/titulos/"]:
                titulos_index = TITULOS_DIR / "template" / "index.html"
                with open(titulos_index, "r", encoding="utf-8") as f:
                    html = f.read()
                responder_html(self, 200, html)
                return

            # 4. Interface: Lineamentos Estruturais (/lineamentos)
            if path in ["/lineamentos", "/lineamentos/"]:
                lineamentos_index = LINEAMENTOS_DIR / "template" / "index.html"
                with open(lineamentos_index, "r", encoding="utf-8") as f:
                    html = f.read()
                responder_html(self, 200, html)
                return

            # 5. Arquivos Estáticos com Despacho Inteligente
            if path.startswith("/static/portal/"):
                rel = path[len("/static/portal/"):]
                servir_arquivo_estatico(self, str(STATIC_DIR / rel))
                return

            if path.startswith("/static/titulos/"):
                rel = path[len("/static/titulos/"):]
                servir_arquivo_estatico(self, str(TITULOS_DIR / "static" / rel))
                return

            if path.startswith("/static/lineamentos/"):
                rel = path[len("/static/lineamentos/"):]
                servir_arquivo_estatico(self, str(LINEAMENTOS_DIR / "static" / rel))
                return

            # Fallback para /static/... genérico (prioriza por existência)
            if path.startswith("/static/"):
                rel = path[len("/static/"):]
                # 1. Verifica portal
                p_portal = STATIC_DIR / rel
                if p_portal.exists():
                    servir_arquivo_estatico(self, str(p_portal))
                    return
                # 2. Verifica titulos
                p_tit = TITULOS_DIR / "static" / rel
                if p_tit.exists():
                    servir_arquivo_estatico(self, str(p_tit))
                    return
                # 3. Verifica lineamentos
                p_lin = LINEAMENTOS_DIR / "static" / rel
                if p_lin.exists():
                    servir_arquivo_estatico(self, str(p_lin))
                    return

                responder_erro(self, 404, f"Arquivo estático '{rel}' não encontrado.")
                return

            # 6. APIs: Títulos Minerários
            from titulos.controle.processo_controle import ProcessoControle

            if path in ["/api/painel", "/api/titulos/painel"]:
                dados = ProcessoControle.obter_painel_consolidado()
                responder_json(self, 200, {"sucesso": True, "painel": dados})
                return

            if path in ["/api/alertas-urgentes", "/api/titulos/alertas-urgentes"]:
                dados = ProcessoControle.obter_alertas_urgentes()
                responder_json(self, 200, {"sucesso": True, "alertas": dados})
                return

            if path in ["/api/situacao-espacial", "/api/titulos/situacao-espacial"]:
                geojson = ProcessoControle.obter_situacao_espacial_geojson()
                responder_json(self, 200, geojson)
                return

            if path in ["/api/processos", "/api/titulos/processos"]:
                f_fase = query.get("fase", [None])[0]
                f_alerta = query.get("alerta", [None])[0]
                f_uf = query.get("uf", [None])[0]
                f_substancia = query.get("substancia", [None])[0]
                dados = ProcessoControle.listar_processos(f_fase, f_alerta, f_uf, f_substancia)
                responder_json(self, 200, {"sucesso": True, "processos": dados})
                return

            if (path.startswith("/api/processos/") or path.startswith("/api/titulos/processos/")):
                parts = [p for p in path.split("/") if p]
                # Verifica se é rota de analise espacial (/api/processos/<id>/analise-espacial)
                if len(parts) >= 3 and parts[-1] == "analise-espacial":
                    proc_id = parts[-2]
                    if proc_id.isdigit():
                        analise = ProcessoControle.obter_analise_espacial(int(proc_id))
                        responder_json(self, 200, {"sucesso": True, "analise_espacial": analise})
                        return

                proc_id = parts[-1]
                if proc_id.isdigit():
                    dados = ProcessoControle.obter_processo_detalhado(int(proc_id))
                    if dados:
                        responder_json(self, 200, {"sucesso": True, "processo": dados})
                    else:
                        responder_erro(self, 404, "Processo não encontrado")
                    return

            if path in ["/api/titulares", "/api/titulos/titulares"]:
                dados = ProcessoControle.listar_titulares()
                responder_json(self, 200, {"sucesso": True, "titulares": dados})
                return

            if path in ["/api/eventos", "/api/titulos/eventos"]:
                proc_id = query.get("processo_id", [None])[0]
                dados = ProcessoControle.listar_eventos(int(proc_id) if proc_id else None)
                responder_json(self, 200, {"sucesso": True, "eventos": dados})
                return

            if path in ["/api/obrigacoes", "/api/titulos/obrigacoes"]:
                proc_id = query.get("processo_id", [None])[0]
                tipo = query.get("tipo", [None])[0]
                alerta = query.get("alerta", [None])[0]
                dados = ProcessoControle.listar_obrigacoes(
                    int(proc_id) if proc_id else None,
                    tipo,
                    alerta
                )
                responder_json(self, 200, {"sucesso": True, "obrigacoes": dados})
                return

            # 7. APIs: Lineamentos Estruturais
            if path in ["/api/analises", "/api/lineamentos/analises"]:
                from lineamentos.controle.lineamento_controle import listar_analises
                listar_analises(self)
                return

            # Rota não encontrada
            responder_erro(self, 404, f"Rota GET '{path}' não encontrada no Portal.")

        except Exception as e:
            responder_erro(self, 500, f"Erro interno do servidor: {str(e)}")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            dados = json.loads(body)

            # 1. Inserir Evento (Títulos Minerários)
            if path in ["/api/eventos", "/api/titulos/eventos"]:
                from titulos.controle.processo_controle import ProcessoControle
                processo_id = dados.get("processo_id")
                tipo_evento = dados.get("tipo_evento")
                data_evento = dados.get("data_evento")
                descricao = dados.get("descricao", "")
                documento_sei = dados.get("documento_sei", "")
                responsavel = dados.get("responsavel", "")

                if not (processo_id and tipo_evento and data_evento):
                    responder_erro(self, 400, "Campos 'processo_id', 'tipo_evento' e 'data_evento' são obrigatórios.")
                    return

                res = ProcessoControle.inserir_evento(
                    int(processo_id), tipo_evento, data_evento, descricao, documento_sei, responsavel
                )
                responder_json(self, 201, {
                    "sucesso": True,
                    "mensagem": "Evento registrado com sucesso! Triggers disparados.",
                    "resultado": res
                })
                return

            # 2. Cumprir Obrigação (Títulos Minerários)
            if (path.startswith("/api/obrigacoes/") or path.startswith("/api/titulos/obrigacoes/")) and path.endswith("/cumprir"):
                from titulos.controle.processo_controle import ProcessoControle
                parts = path.split("/")
                obrigacao_id = int(parts[-2])
                data_cumprimento = dados.get("data_cumprimento")
                res = ProcessoControle.cumprir_obrigacao(obrigacao_id, data_cumprimento)
                responder_json(self, 200, {
                    "sucesso": True,
                    "mensagem": "Obrigação cumprida com sucesso!",
                    "resultado": res
                })
                return

            # 3. Criar Análise SRTM (Lineamentos Estruturais)
            if path in ["/api/analises", "/api/lineamentos/analises"]:
                from lineamentos.controle.lineamento_controle import criar_analise
                criar_analise(self, dados)
                return

            responder_erro(self, 404, f"Rota POST '{path}' não encontrada no Portal.")

        except Exception as e:
            responder_erro(self, 500, f"Erro interno no processamento do POST: {str(e)}")
