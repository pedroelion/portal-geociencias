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
    """Cria a tabela analises_srtm com suporte a coordenadas espaciais e semeia dados."""
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
                data_extracao TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                azimute_predominante TEXT,
                total_lineamentos INTEGER
            )
        """)
        
        # Migração graciosa de colunas caso a tabela antiga já exista sem os campos espaciais
        cursor.execute("PRAGMA table_info(analises_srtm)")
        colunas_existentes = [col["name"] for col in cursor.fetchall()]
        
        if "latitude" not in colunas_existentes:
            cursor.execute("ALTER TABLE analises_srtm ADD COLUMN latitude REAL")
        if "longitude" not in colunas_existentes:
            cursor.execute("ALTER TABLE analises_srtm ADD COLUMN longitude REAL")
        if "azimute_predominante" not in colunas_existentes:
            cursor.execute("ALTER TABLE analises_srtm ADD COLUMN azimute_predominante TEXT")
        if "total_lineamentos" not in colunas_existentes:
            cursor.execute("ALTER TABLE analises_srtm ADD COLUMN total_lineamentos INTEGER")

        # Verificar se a tabela está vazia ou se os registros existentes não têm coordenadas
        cursor.execute("SELECT COUNT(*) AS total FROM analises_srtm")
        total = cursor.fetchone()["total"]
        
        exemplos = [
            (
                "Cinturão Brasília - Lineamento Transbrasiliano",
                "SRTM 30m (1 arc-sec)",
                "Concluído",
                datetime(2026, 11, 10, 14, 32).strftime("%Y-%m-%d %H:%M:%S"),
                -15.7801,
                -47.9292,
                "NE-SW (N45E)",
                142
            ),
            (
                "Borda Sudeste do Cráton São Francisco",
                "SRTM 30m (1 arc-sec)",
                "Concluído",
                datetime(2026, 11, 15, 9, 18).strftime("%Y-%m-%d %H:%M:%S"),
                -19.9167,
                -43.9345,
                "NW-SE (N135E)",
                98
            ),
            (
                "Bacia Sedimentar do Paraná - Falhas de Guapiara",
                "SRTM 90m (3 arc-sec)",
                "Em Processamento",
                datetime(2026, 11, 18, 16, 45).strftime("%Y-%m-%d %H:%M:%S"),
                -23.8833,
                -48.5333,
                "NW-SE (N120E)",
                115
            ),
            (
                "Província Mineral de Carajás - Falhas E-W",
                "SRTM 30m (1 arc-sec)",
                "Pendente",
                datetime(2026, 11, 19, 11, 5).strftime("%Y-%m-%d %H:%M:%S"),
                -6.0500,
                -50.1500,
                "E-W (N90E)",
                87
            ),
            (
                "Cinturão Ribeira - Setor Serra do Mar",
                "SRTM 30m (1 arc-sec)",
                "Concluído",
                datetime(2026, 11, 20, 15, 20).strftime("%Y-%m-%d %H:%M:%S"),
                -22.5050,
                -43.1780,
                "NE-SW (N55E)",
                164
            )
        ]

        if total == 0:
            cursor.executemany("""
                INSERT INTO analises_srtm (nome_projeto, resolucao, status, data_extracao, latitude, longitude, azimute_predominante, total_lineamentos)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, exemplos)
            conn.commit()
            print(f"[DB] Banco de dados inicializado em: {caminho} com {len(exemplos)} registros espaciais.")
        else:
            # Atualiza registros antigos que estejam sem coordenadas
            cursor.execute("SELECT id, nome_projeto FROM analises_srtm WHERE latitude IS NULL")
            sem_coords = cursor.fetchall()
            for r in sem_coords:
                pid = r["id"]
                pnome = r["nome_projeto"].lower()
                for ex in exemplos:
                    if ex[0].lower() in pnome or pnome in ex[0].lower():
                        cursor.execute("""
                            UPDATE analises_srtm
                            SET latitude = ?, longitude = ?, azimute_predominante = ?, total_lineamentos = ?
                            WHERE id = ?
                        """, (ex[4], ex[5], ex[6], ex[7], pid))
                        break
                else:
                    # Coordenadas padrão no Brasil central se não bater nome exato
                    cursor.execute("""
                        UPDATE analises_srtm
                        SET latitude = -15.5 + (id * 1.2), longitude = -48.0 - (id * 0.8), azimute_predominante = 'NE-SW (N45E)', total_lineamentos = 90
                        WHERE id = ?
                    """, (pid,))
            conn.commit()
            print(f"[DB] Banco de dados pronto em: {caminho} ({total} registros com dados espaciais).")

if __name__ == "__main__":
    init_db()
