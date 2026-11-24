from datetime import datetime
import random
import math

try:
    from lineamentos.db.database import get_connection
except ImportError:
    from db.database import get_connection

class AnaliseSRTM:
    """Modelo representando uma análise de extração de lineamentos estruturais SRTM com atributos espaciais."""

    def __init__(self, nome_projeto, resolucao, status="Concluído", data_extracao=None, 
                 latitude=None, longitude=None, azimute_predominante=None, total_lineamentos=None, id=None):
        self.id = id
        self.nome_projeto = nome_projeto.strip() if nome_projeto else ""
        self.resolucao = resolucao.strip() if resolucao else "SRTM 30m (1 arc-sec)"
        self.status = status.strip() if status else "Concluído"
        self.data_extracao = data_extracao or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.latitude = float(latitude) if latitude is not None and str(latitude).strip() != "" else -15.7801
        self.longitude = float(longitude) if longitude is not None and str(longitude).strip() != "" else -47.9292
        self.azimute_predominante = azimute_predominante or "NE-SW (N45E)"
        self.total_lineamentos = int(total_lineamentos) if total_lineamentos is not None else 120

    def salvar(self):
        """Salva a análise no banco de dados (INSERT ou UPDATE)."""
        with get_connection() as conn:
            cursor = conn.cursor()
            if self.id is None:
                cursor.execute("""
                    INSERT INTO analises_srtm 
                    (nome_projeto, resolucao, status, data_extracao, latitude, longitude, azimute_predominante, total_lineamentos)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.nome_projeto, self.resolucao, self.status, self.data_extracao,
                    self.latitude, self.longitude, self.azimute_predominante, self.total_lineamentos
                ))
                self.id = cursor.lastrowid
            else:
                cursor.execute("""
                    UPDATE analises_srtm
                    SET nome_projeto = ?, resolucao = ?, status = ?, data_extracao = ?,
                        latitude = ?, longitude = ?, azimute_predominante = ?, total_lineamentos = ?
                    WHERE id = ?
                """, (
                    self.nome_projeto, self.resolucao, self.status, self.data_extracao,
                    self.latitude, self.longitude, self.azimute_predominante, self.total_lineamentos,
                    self.id
                ))
            conn.commit()
        return self

    @classmethod
    def listar(cls):
        """Retorna todas as análises cadastradas ordenadas pela mais recente."""
        analises = []
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome_projeto, resolucao, status, data_extracao,
                       latitude, longitude, azimute_predominante, total_lineamentos
                FROM analises_srtm 
                ORDER BY id DESC
            """)
            linhas = cursor.fetchall()
            for row in linhas:
                analises.append(cls(
                    id=row["id"],
                    nome_projeto=row["nome_projeto"],
                    resolucao=row["resolucao"],
                    status=row["status"],
                    data_extracao=row["data_extracao"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    azimute_predominante=row["azimute_predominante"],
                    total_lineamentos=row["total_lineamentos"]
                ))
        return analises

    @classmethod
    def buscar_por_id(cls, analise_id):
        """Busca uma análise específica pelo ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome_projeto, resolucao, status, data_extracao,
                       latitude, longitude, azimute_predominante, total_lineamentos
                FROM analises_srtm 
                WHERE id = ?
            """, (analise_id,))
            row = cursor.fetchone()
            if row:
                return cls(
                    id=row["id"],
                    nome_projeto=row["nome_projeto"],
                    resolucao=row["resolucao"],
                    status=row["status"],
                    data_extracao=row["data_extracao"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    azimute_predominante=row["azimute_predominante"],
                    total_lineamentos=row["total_lineamentos"]
                )
        return None

    def gerar_lineamentos_vetoriais(self):
        """
        Gera segmentos vetoriais determinísticos (GeoJSON LineStrings) representando 
        as fraturas e zonas de cisalhamento extraídas no relevo ao redor do ponto central.
        """
        rng = random.Random(self.id or hash(self.nome_projeto))
        lat_c = self.latitude
        lng_c = self.longitude
        linhas = []

        # Determina o ângulo base predominante
        azimute_base = 45 # NE
        if "nw" in self.azimute_predominante.lower():
            azimute_base = 135
        elif "e-w" in self.azimute_predominante.lower():
            azimute_base = 90
        elif "n-s" in self.azimute_predominante.lower():
            azimute_base = 0

        # Gera de 8 a 16 traços principais de falha/fratura no relevo
        num_tracos = min(18, max(8, (self.total_lineamentos // 10)))
        raio_graus = 0.45 # ~50km de raio de influência do relevo

        for i in range(num_tracos):
            # Centroide do lineamento disperso pelo MDE
            d_lat = rng.uniform(-raio_graus, raio_graus)
            d_lng = rng.uniform(-raio_graus, raio_graus)
            p_lat = lat_c + d_lat
            p_lng = lng_c + d_lng

            # Variação do azimute ao redor da direção predominante
            variacao = rng.gauss(0, 18)
            ang = (azimute_base + variacao) % 180
            rad = math.radians(ang)

            # Comprimento da fratura no terreno (10km a 40km)
            comp = rng.uniform(0.08, 0.28)
            dx = (comp / 2) * math.sin(rad)
            dy = (comp / 2) * math.cos(rad)

            # Classificação por tendência direcional
            tendencia = "NE-SW"
            if 115 <= ang <= 160 or 20 <= (180 - ang) <= 65:
                tendencia = "NW-SE"
            elif 75 <= ang <= 105:
                tendencia = "E-W"
            elif ang <= 20 or ang >= 165:
                tendencia = "N-S"

            linhas.append({
                "type": "Feature",
                "properties": {
                    "projeto_id": self.id,
                    "projeto_nome": self.nome_projeto,
                    "azimute": round(ang, 1),
                    "tendencia": tendencia,
                    "comprimento_km": round(comp * 111, 2)
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [round(p_lng - dx, 5), round(p_lat - dy, 5)],
                        [round(p_lng + dx, 5), round(p_lat + dy, 5)]
                    ]
                }
            })

        return linhas

    def to_dict(self):
        """Serializa o modelo em dicionário Python/JSON com atributos espaciais."""
        return {
            "id": self.id,
            "nome_projeto": self.nome_projeto,
            "resolucao": self.resolucao,
            "status": self.status,
            "data_extracao": self.data_extracao,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "azimute_predominante": self.azimute_predominante,
            "total_lineamentos": self.total_lineamentos,
            "lineamentos_features": self.gerar_lineamentos_vetoriais()
        }
