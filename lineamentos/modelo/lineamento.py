from datetime import datetime
try:
    from lineamentos.db.database import get_connection
except ImportError:
    from db.database import get_connection

class AnaliseSRTM:
    """Modelo representando uma análise de extração de lineamentos estruturais SRTM."""

    def __init__(self, nome_projeto, resolucao, status="Concluído", data_extracao=None, id=None):
        self.id = id
        self.nome_projeto = nome_projeto.strip() if nome_projeto else ""
        self.resolucao = resolucao.strip() if resolucao else "SRTM 30m (1 arc-sec)"
        self.status = status.strip() if status else "Concluído"
        self.data_extracao = data_extracao or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def salvar(self):
        """Salva a análise no banco de dados (INSERT ou UPDATE)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            if self.id is None:
                cursor.execute("""
                    INSERT INTO analises_srtm (nome_projeto, resolucao, status, data_extracao)
                    VALUES (?, ?, ?, ?)
                """, (self.nome_projeto, self.resolucao, self.status, self.data_extracao))
                self.id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE analises_srtm
                    SET nome_projeto = ?, resolucao = ?, status = ?, data_extracao = ?
                    WHERE id = ?
                """, (self.nome_projeto, self.resolucao, self.status, self.data_extracao, self.id))
            conn.commit()
        return self

    @classmethod
    def listar(cls):
        """Retorna todas as análises cadastradas ordenadas pela mais recente."""
        analises = []
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome_projeto, resolucao, status, data_extracao FROM analises_srtm ORDER BY id DESC")
            linhas = cursor.fetchall()
            for row in linhas:
                analises.append(cls(
                    id=row["id"],
                    nome_projeto=row["nome_projeto"],
                    resolucao=row["resolucao"],
                    status=row["status"],
                    data_extracao=row["data_extracao"]
                ))
        return analises

    @classmethod
    def buscar_por_id(cls, analise_id):
        """Busca uma análise específica pelo ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome_projeto, resolucao, status, data_extracao FROM analises_srtm WHERE id = ?", (analise_id,))
            row = cursor.fetchone()
            if row:
                return cls(
                    id=row["id"],
                    nome_projeto=row["nome_projeto"],
                    resolucao=row["resolucao"],
                    status=row["status"],
                    data_extracao=row["data_extracao"]
                )
        return None

    def to_dict(self):
        """Serializa o modelo em dicionário Python/JSON."""
        return {
            "id": self.id,
            "nome_projeto": self.nome_projeto,
            "resolucao": self.resolucao,
            "status": self.status,
            "data_extracao": self.data_extracao
        }
