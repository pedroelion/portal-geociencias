import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
from pathlib import Path
try:
    from lineamentos.controle.lineamento_controle import renderizar_index, listar_analises, criar_analise
except ImportError:
    from controle.lineamento_controle import renderizar_index, listar_analises, criar_analise
try:
    from lineamentos.controle.respostas import responder_estatico, responder_erro
except ImportError:
    from controle.respostas import responder_estatico, responder_erro

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

class Roteador(BaseHTTPRequestHandler):
    """Roteador HTTP personalizado herdando de BaseHTTPRequestHandler."""

    def log_message(self, format, *args):
        """Formata os logs do servidor no console com timestamp e endereço do cliente."""
        print(f"[{self.log_date_time_string()}] {self.client_address[0]} - {format % args}")

    def do_OPTIONS(self):
        """Trata requisições preflight do CORS."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Roteia requisições HTTP GET."""
        parsed_url = urllib.parse.urlparse(self.path)
        caminho = parsed_url.path

        # Rota principal
        if caminho in ("/", "/index.html"):
            renderizar_index(self)
            return

        # Rota API: Listar análises
        if caminho == "/api/analises":
            listar_analises(self)
            return

        # Rota de Arquivos Estáticos: /static/...
        if caminho.startswith("/static/lineamentos/"): caminho = "/static/" + caminho[len("/static/lineamentos/"):];
        if caminho.startswith("/static/"):
            # Remove o prefixo '/static/' para obter o caminho relativo dentro de static
            relativo = caminho[len("/static/"):].lstrip("/")
            arquivo_alvo = (STATIC_DIR / relativo).resolve()

            # Proteção contra Directory Traversal
            try:
                arquivo_alvo.relative_to(STATIC_DIR.resolve())
            except ValueError:
                responder_erro(self, 403, "Acesso não autorizado.")
                return

            responder_estatico(self, arquivo_alvo)
            return

        # Rota não encontrada
        responder_erro(self, 404, f"Rota GET '{caminho}' não encontrada no servidor.")

    def do_POST(self):
        """Roteia requisições HTTP POST."""
        parsed_url = urllib.parse.urlparse(self.path)
        caminho = parsed_url.path

        if caminho == "/api/analises":
            try:
                length_header = self.headers.get("Content-Length")
                if not length_header:
                    responder_erro(self, 400, "Cabeçalho 'Content-Length' ausente.")
                    return

                comprimento = int(length_header)
                corpo_bytes = self.rfile.read(comprimento)
                payload = json.loads(corpo_bytes.decode("utf-8"))
            except json.JSONDecodeError:
                responder_erro(self, 400, "JSON malformado na requisição.")
                return
            except Exception as e:
                responder_erro(self, 400, f"Erro ao processar corpo da requisição: {str(e)}")
                return

            criar_analise(self, payload)
            return

        # Rota não encontrada
        responder_erro(self, 404, f"Rota POST '{caminho}' não encontrada no servidor.")
