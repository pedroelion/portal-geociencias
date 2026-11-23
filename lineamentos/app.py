import os
import sys
import socket
from http.server import HTTPServer

# Adiciona o diretório raiz ao sys.path para importações relativas seguras
DIRETORIO_RAIZ = os.path.dirname(os.path.abspath(__file__))
if DIRETORIO_RAIZ not in sys.path:
    sys.path.insert(0, DIRETORIO_RAIZ)

try:
    from lineamentos.db.database import init_db
except ImportError:
    from db.database import init_db
from rotas.rotas import Roteador

class ServidorIPv6(HTTPServer):
    """HTTPServer com suporte explícito a IPv6 e Dual-Stack."""
    address_family = socket.AF_INET6

    def server_bind(self):
        # Permite reutilização rápida da porta
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Habilita Dual-Stack se suportado pelo SO (atende tanto IPv4 quanto IPv6)
        try:
            if hasattr(socket, "IPV6_V6ONLY"):
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except Exception:
            pass
        super().server_bind()

def main():
    porta = int(os.environ.get("PORT", 8081))
    host = "::"

    print("=" * 70)
    print("  PROJETO 4: EXTRAÇÃO DE LINEAMENTOS ESTRUTURAIS (SRTM)")
    print("  Servidor Web Puro (Python Standard Library - http.server)")
    print("=" * 70)

    # Inicializa a estrutura do banco SQLite
    print("[1/2] Inicializando banco de dados SQLite...")
    init_db()

    # Cria e inicia o servidor HTTPServer IPv6
    print(f"[2/2] Vinculando socket IPv6 em [{host}]:{porta}...")
    servidor = ServidorIPv6((host, porta), Roteador)

    print("\n Servidor ativo e aguardando conexões!")
    print(f" -> Local (IPv6 Loopback):   http://[::1]:{porta}")
    print(f" -> Acesso Remoto (VM IPv6): http://[2804:14:8286:6b01:a00:27ff:fe6b:96d0]:{porta}")
    print(f" -> Localhost (IPv4 Fallback): http://localhost:{porta}")
    print("\nPressione Ctrl+C para encerrar o servidor.\n" + "-" * 70)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Sinal de interrupção recebido. Encerrando servidor HTTP...")
        servidor.server_close()
        print("[+] Servidor finalizado com sucesso.")

if __name__ == "__main__":
    main()
