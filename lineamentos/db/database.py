import sqlite3
import os
from pathlib import Path
from datetime import datetime

DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "lineamentos.db"

def get_connection(db_file=None):
    """Retorna uma conexão ativa com o banco SQLite."""
    caminho = db_file or DB_PATH
    conn = sqlite3.connect(str(caminho))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_file=None):
    """Cria a tabela analises_srtm e insere dados iniciais se estiver vazia."""
    caminho = db_file or DB_PATH
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    
    with get_connection(caminho) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analises_srtm (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_projeto TEXT NOT NULL,
                resolucao TEXT NOT NULL,
                status TEXT NOT NULL,
                data_extracao TEXT NOT NULL
            )
        """)
        
        # Verificar se a tabela está vazia para semear dados de demonstração geológica
        cursor.execute("SELECT COUNT(*) AS total FROM analises_srtm")
        total = cursor.fetchone()["total"]
        
        if total == 0:
            exemplos = [
                (
                    "Cinturão Brasília - Lineamento Transbrasiliano",
                    "SRTM 30m (1 arc-sec)",
                    "Concluído",
                    datetime(2026, 11, 10, 14, 32).strftime("%Y-%m-%d %H:%M:%S")
                ),
                (
                    "Borda Sudeste do Cráton São Francisco",
                    "SRTM 30m (1 arc-sec)",
                    "Concluído",
                    datetime(2026, 11, 15, 9, 18).strftime("%Y-%m-%d %H:%M:%S")
                ),
                (
                    "Bacia Sedimentar do Paraná - Falhas de Guapiara",
                    "SRTM 90m (3 arc-sec)",
                    "Em Processamento",
                    datetime(2026, 11, 18, 16, 45).strftime("%Y-%m-%d %H:%M:%S")
                ),
                (
                    "Província Mineral de Carajás - Falhas E-W",
                    "SRTM 30m (1 arc-sec)",
                    "Pendente",
                    datetime(2026, 11, 19, 11, 5).strftime("%Y-%m-%d %H:%M:%S")
                )
            ]
            cursor.executemany("""
                INSERT INTO analises_srtm (nome_projeto, resolucao, status, data_extracao)
                VALUES (?, ?, ?, ?)
            """, exemplos)
            conn.commit()
            print(f"[DB] Banco de dados inicializado com sucesso em: {caminho} com {len(exemplos)} registros.")
        else:
            print(f"[DB] Banco de dados pronto em: {caminho} ({total} registros existentes).")

if __name__ == "__main__":
    init_db()
