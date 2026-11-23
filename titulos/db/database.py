"""
Módulo: db/database.py
Descrição: Gerenciador de conexão com PostgreSQL/PostGIS e execução de comandos SQL.
"""

import os
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_DISPONIVEL = True
except ImportError:
    psycopg2 = None
    RealDictCursor = None
    PSYCOPG2_DISPONIVEL = False

# Configurações de Conexão com Suporte a Nuvem (Render, Railway, Fly.io, etc.)
DATABASE_URL = os.environ.get("DATABASE_URL")
DB_HOST = os.environ.get("DB_HOST", os.environ.get("PGHOST", "localhost"))
DB_PORT = os.environ.get("DB_PORT", os.environ.get("PGPORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", os.environ.get("PGDATABASE", "gestao_titulos_minerarios"))
DB_USER = os.environ.get("DB_USER", os.environ.get("PGUSER", "pedro"))
DB_PASS = os.environ.get("DB_PASS", os.environ.get("PGPASSWORD", "123"))

def get_connection():
    """Retorna uma nova conexão com o banco de dados PostgreSQL/PostGIS."""
    if not PSYCOPG2_DISPONIVEL:
        raise RuntimeError("Driver 'psycopg2' não está instalado no ambiente Python.")

    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, connect_timeout=5)

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=5
    )

def execute_query(query, params=None):
    """Executa consulta SELECT e retorna lista de dicionários."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            rows = cur.fetchall()
            # Converte objetos RealDictRow para dicionários comuns
            return [dict(r) for r in rows]
    finally:
        conn.close()

def execute_single(query, params=None):
    """Executa consulta SELECT e retorna um único registro."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()

def execute_commit(query, params=None):
    """Executa comando INSERT/UPDATE/DELETE com commit e retorna linhas afetadas ou id."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            conn.commit()
            try:
                res = cur.fetchone()
                return dict(res) if res else True
            except psycopg2.ProgrammingError:
                return True
    finally:
        conn.close()

def init_schema():
    """Verifica e inicializa o schema executando os scripts SQL se necessário."""
    try:
        # Testa se a tabela processo existe
        res = execute_single("SELECT to_regclass('public.processo') AS tbl;")
        if res and res.get("tbl"):
            print("[DB] Schema já inicializado e tabelas existentes.")
            return True
    except Exception as e:
        print(f"[DB] Verificação de schema: {e}")

    # Aplica os arquivos SQL em ordem
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_files = [
        os.path.join(base_dir, "sql", "01_schema_postgis.sql"),
        os.path.join(base_dir, "sql", "02_triggers_prazos.sql"),
        os.path.join(base_dir, "sql", "03_views_painel.sql"),
    ]
    for sf in sql_files:
        if os.path.exists(sf):
            print(f"[DB] Aplicando {os.path.basename(sf)}...")
            with open(sf, "r", encoding="utf-8") as f:
                content = f.read()
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(content)
                conn.commit()
            finally:
                conn.close()
    print("[DB] Schema inicializado com sucesso!")
    return True
