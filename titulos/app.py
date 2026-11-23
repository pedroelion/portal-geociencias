#!/usr/bin/env python3
"""
Módulo: app.py
Descrição: Ponto de entrada da aplicação corporativa de Gestão de Títulos Minerários.
            Servidor HTTP puro Python na porta 8080 com suporte nativo a IPv6 e IPv4.
"""

import os
import sys
import socket
from http.server import HTTPServer

# Adiciona o diretório atual ao path para importação dos módulos MVC
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from rotas.rotas import Roteador
try:
    from titulos.db.database import init_schema
except ImportError:
    from db.database import init_schema

PORT = int(os.environ.get("PORT", 8080))

class DualStackServer(HTTPServer):
    """Servidor HTTP com suporte a IPv6 dual-stack (aceita conexões IPv6 e IPv4 simultaneamente)."""
    address_family = socket.AF_INET6

    def server_bind(self):
        # Permite conexões dual-stack IPv4 e IPv6 no mesmo socket
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass
        super().server_bind()

def run_server():
    print("=" * 70)
    print("SISTEMA CORPORATIVO DE GESTÃO DE TÍTULOS MINERÁRIOS (ANM / POSTGIS)")
    print("Padrão Arquitetural: Model-View-Controller (MVC)")
    print("=" * 70)

    # 1. Tenta inicializar o banco de dados e aplicar o schema
    try:
        init_schema()
    except Exception as e:
        print(f"[AVISO] Não foi possível conectar ao PostgreSQL de imediato: {e}")
        print("[AVISO] O servidor continuará em execução para servir a interface e APIs.")

    # 2. Inicializa o servidor HTTP IPv6
    try:
        server = DualStackServer(("::", PORT), Roteador)
        print(f"[SERVER] Servidor HTTP IPv6 rodando com sucesso em http://[::]:{PORT}/")
        print(f"[SERVER] Acesse localmente em http://localhost:{PORT}/")
    except Exception as e:
        print(f"[SERVER] Falha ao inicializar IPv6 ('{e}'). Tentando fallback para IPv4...")
        server = HTTPServer(("0.0.0.0", PORT), Roteador)
        print(f"[SERVER] Servidor HTTP IPv4 rodando em http://0.0.0.0:{PORT}/")

    print("-" * 70)
    print("Rotas ativas:")
    print(f"  • Painel Web / Dashboard: http://localhost:{PORT}/")
    print(f"  • API Painel Consolidado: http://localhost:{PORT}/api/painel")
    print(f"  • API Alertas Urgentes:   http://localhost:{PORT}/api/alertas-urgentes")
    print(f"  • API Situação Espacial:  http://localhost:{PORT}/api/situacao-espacial")
    print(f"  • API Processos ANM:      http://localhost:{PORT}/api/processos")
    print(f"  • API Eventos:            http://localhost:{PORT}/api/eventos")
    print(f"  • API Obrigações:         http://localhost:{PORT}/api/obrigacoes")
    print("-" * 70)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Encerrando o servidor com segurança...")
        server.server_close()
        print("[SERVER] Servidor finalizado.")

if __name__ == "__main__":
    run_server()
