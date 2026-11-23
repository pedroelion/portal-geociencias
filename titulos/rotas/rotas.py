"""
Módulo: rotas/rotas.py
Descrição: Roteador HTTP herdando de BaseHTTPRequestHandler mapeando endpoints GET/POST e estáticos.
"""

import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
try:
    from titulos.controle.processo_controle import ProcessoControle
except ImportError:
    from controle.processo_controle import ProcessoControle
try:
    from titulos.controle.respostas import responder_json, responder_html, responder_erro, servir_arquivo_estatico
except ImportError:
    from controle.respostas import responder_json, responder_html, responder_erro, servir_arquivo_estatico

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Roteador(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        """Suporte a CORS preflight."""
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
            # 1. Página inicial (Dashboard)
            if path in ["/", "/index.html"]:
                template_path = os.path.join(BASE_DIR, "template", "index.html")
                with open(template_path, "r", encoding="utf-8") as f:
                    html = f.read()
                responder_html(self, 200, html)
                return

            # 2. Arquivos estáticos (/static/...)
            if path.startswith("/static/titulos/"): path = "/static/" + path[len("/static/titulos/"):];
            if path.startswith("/static/"):
                rel_path = path[len("/static/"):]
                disk_path = os.path.join(BASE_DIR, "static", rel_path)
                if path.endswith(".css"):
                    servir_arquivo_estatico(self, disk_path, "text/css; charset=utf-8")
                elif path.endswith(".js"):
                    servir_arquivo_estatico(self, disk_path, "application/javascript; charset=utf-8")
                elif path.endswith(".png"):
                    servir_arquivo_estatico(self, disk_path, "image/png")
                elif path.endswith(".svg"):
                    servir_arquivo_estatico(self, disk_path, "image/svg+xml")
                else:
                    servir_arquivo_estatico(self, disk_path, "application/octet-stream")
                return

            # 3. API: Painel Consolidado
            if path == "/api/painel":
                dados = ProcessoControle.obter_painel_consolidado()
                responder_json(self, 200, {"sucesso": True, "painel": dados})
                return

            # 4. API: Alertas Urgentes
            if path == "/api/alertas-urgentes":
                dados = ProcessoControle.obter_alertas_urgentes()
                responder_json(self, 200, {"sucesso": True, "alertas": dados})
                return

            # 5. API: GeoJSON Situação Espacial
            if path == "/api/situacao-espacial":
                geojson = ProcessoControle.obter_situacao_espacial_geojson()
                responder_json(self, 200, geojson)
                return

            # 6. API: Listagem de Processos
            if path == "/api/processos":
                f_fase = query.get("fase", [None])[0]
                f_alerta = query.get("alerta", [None])[0]
                dados = ProcessoControle.listar_processos(f_fase, f_alerta)
                responder_json(self, 200, {"sucesso": True, "processos": dados})
                return

            # 7. API: Detalhes de um Processo específico (/api/processos/<id>)
            if path.startswith("/api/processos/") and len(path.split("/")) == 4:
                proc_id = path.split("/")[3]
                dados = ProcessoControle.obter_processo_detalhado(int(proc_id))
                if dados:
                    responder_json(self, 200, {"sucesso": True, "processo": dados})
                else:
                    responder_erro(self, 404, "Processo não encontrado")
                return

            # 8. API: Titulares
            if path == "/api/titulares":
                dados = ProcessoControle.listar_titulares()
                responder_json(self, 200, {"sucesso": True, "titulares": dados})
                return

            # 9. API: Eventos
            if path == "/api/eventos":
                proc_id = query.get("processo_id", [None])[0]
                dados = ProcessoControle.listar_eventos(int(proc_id) if proc_id else None)
                responder_json(self, 200, {"sucesso": True, "eventos": dados})
                return

            # 10. API: Obrigações
            if path == "/api/obrigacoes":
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

            # Rota não encontrada
            responder_erro(self, 404, f"Rota GET '{path}' não encontrada")

        except Exception as e:
            responder_erro(self, 500, f"Erro interno do servidor: {str(e)}")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            dados = json.loads(body)

            # 1. API: Inserir Evento
            if path == "/api/eventos":
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
                    "mensagem": "Evento registrado com sucesso! Triggers de obrigações disparados.",
                    "resultado": res
                })
                return

            # 2. API: Cumprir Obrigação (/api/obrigacoes/<id>/cumprir)
            if path.startswith("/api/obrigacoes/") and path.endswith("/cumprir"):
                parts = path.split("/")
                obrigacao_id = int(parts[3])
                data_cumprimento = dados.get("data_cumprimento")
                res = ProcessoControle.cumprir_obrigacao(obrigacao_id, data_cumprimento)
                responder_json(self, 200, {
                    "sucesso": True,
                    "mensagem": "Obrigação cumprida com sucesso!",
                    "resultado": res
                })
                return

            responder_erro(self, 404, f"Rota POST '{path}' não encontrada")

        except Exception as e:
            responder_erro(self, 500, f"Erro interno no processamento do POST: {str(e)}")
