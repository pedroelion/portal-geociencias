"""
Módulo: modelo/processo.py
Descrição: Modelo de dados para Processo Minerário na ANM e poligonal PostGIS.
"""

class Processo:
    def __init__(self, id=None, numero_processo="", ano_processo=2024, titular_id=None,
                 fase="Autorização de Pesquisa", substancia_mineral="", uso_substancia="Uso Industrial",
                 area_ha=0.0, municipio="", uf="", data_requerimento=None, data_publicacao_alvara=None,
                 prazo_alvara_anos=3, data_vencimento_alvara=None, data_portaria_lavra=None,
                 status_processo="Ativo", geom_geojson=None, criado_em=None):
        self.id = id
        self.numero_processo = numero_processo
        self.ano_processo = ano_processo
        self.titular_id = titular_id
        self.fase = fase
        self.substancia_mineral = substancia_mineral
        self.uso_substancia = uso_substancia
        self.area_ha = float(area_ha) if area_ha else 0.0
        self.municipio = municipio
        self.uf = uf
        self.data_requerimento = str(data_requerimento) if data_requerimento else None
        self.data_publicacao_alvara = str(data_publicacao_alvara) if data_publicacao_alvara else None
        self.prazo_alvara_anos = prazo_alvara_anos
        self.data_vencimento_alvara = str(data_vencimento_alvara) if data_vencimento_alvara else None
        self.data_portaria_lavra = str(data_portaria_lavra) if data_portaria_lavra else None
        self.status_processo = status_processo
        self.geom_geojson = geom_geojson
        self.criado_em = str(criado_em) if criado_em else None

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id") or data.get("processo_id"),
            numero_processo=data.get("numero_processo", ""),
            ano_processo=data.get("ano_processo", 2024),
            titular_id=data.get("titular_id"),
            fase=data.get("fase", "Autorização de Pesquisa"),
            substancia_mineral=data.get("substancia_mineral", ""),
            uso_substancia=data.get("uso_substancia", "Uso Industrial"),
            area_ha=data.get("area_ha", 0.0),
            municipio=data.get("municipio", ""),
            uf=data.get("uf", ""),
            data_requerimento=data.get("data_requerimento"),
            data_publicacao_alvara=data.get("data_publicacao_alvara"),
            prazo_alvara_anos=data.get("prazo_alvara_anos", 3),
            data_vencimento_alvara=data.get("data_vencimento_alvara"),
            data_portaria_lavra=data.get("data_portaria_lavra"),
            status_processo=data.get("status_processo", "Ativo"),
            geom_geojson=data.get("geom_geojson") or data.get("geojson"),
            criado_em=data.get("criado_em")
        )

    def to_dict(self):
        return {
            "id": self.id,
            "numero_processo": self.numero_processo,
            "ano_processo": self.ano_processo,
            "titular_id": self.titular_id,
            "fase": self.fase,
            "substancia_mineral": self.substancia_mineral,
            "uso_substancia": self.uso_substancia,
            "area_ha": self.area_ha,
            "municipio": self.municipio,
            "uf": self.uf,
            "data_requerimento": self.data_requerimento,
            "data_publicacao_alvara": self.data_publicacao_alvara,
            "prazo_alvara_anos": self.prazo_alvara_anos,
            "data_vencimento_alvara": self.data_vencimento_alvara,
            "data_portaria_lavra": self.data_portaria_lavra,
            "status_processo": self.status_processo,
            "geom_geojson": self.geom_geojson,
            "criado_em": self.criado_em
        }
