#!/usr/bin/env python3
"""
Portal Integrado de Geociências & Mineração
Ponto de entrada unificado em Python puro (Standard Library - http.server)
Porta configurável via variável de ambiente PORT (padrão 8000).
"""

import os
import sys
import socket
from http.server import HTTPServer

# Adiciona diretório raiz do portal e dos subsistemas ao sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from rotas.rotas import RoteadorPortal

PORT = int(os.environ.get("PORT", 8000))

class DualStackServer(HTTPServer):
    """Servidor HTTP puro Python com suporte a Dual-Stack IPv6 e IPv4."""
    address_family = socket.AF_INET6

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            if hasattr(socket, "IPV6_V6ONLY"):
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except Exception:
            pass
        super().server_bind()

def main():
    print("=" * 75)
    print("  PORTAL INTEGRADO DE GEOCIÊNCIAS & MINERAÇÃO")
    print("  Arquitetura: Model-View-Controller (MVC) em Python Puro")
    print("  (Sem frameworks web externos • Apenas Biblioteca Padrão)")
    print("=" * 75)

    # 1. Tenta inicializar banco SQLite de lineamentos
    try:
        from lineamentos.db.database import init_db
        init_db()
    except Exception as e:
        print(f"  [AVISO] SQLite Lineamentos: {e}")

    # 2. Tenta inicializar banco PostGIS de títulos minerários
    try:
        from titulos.db.database import init_schema
        init_schema()
    except Exception as e:
        print(f"  [AVISO] PostGIS Títulos Minerários: {e}")

    # 3. Inicia servidor HTTP
    try:
        servidor = DualStackServer(("::", PORT), RoteadorPortal)
        print(f"  [+] Servidor Dual-Stack IPv6/IPv4 ativo na porta {PORT}!")
    except Exception:
        servidor = HTTPServer(("0.0.0.0", PORT), RoteadorPortal)
        print(f"  [+] Servidor IPv4 ativo na porta {PORT}!")

    print("-" * 75)
    print("  Rotas Principais:")
    print(f"    • Hub Central de Geociências:           http://localhost:{PORT}/")
    print(f"    • Tema 1 - Gestão de Títulos Minerários: http://localhost:{PORT}/titulos")
    print(f"    • Projeto 4 - Lineamentos Estruturais:  http://localhost:{PORT}/lineamentos")
    print(f"    • Status e Métricas dos Subsistemas:   http://localhost:{PORT}/api/portal/status")
    print("-" * 75)
    print("  Para encerrar o servidor, pressione Ctrl + C.\n")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Encerrando o servidor do Portal...")
        servidor.server_close()
        print("[+] Servidor finalizado com sucesso.")

if __name__ == "__main__":
    main()
