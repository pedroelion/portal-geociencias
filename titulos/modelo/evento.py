"""
Módulo: modelo/evento.py
Descrição: Modelo de dados para Histórico de Eventos Regulatórios do processo (1:N).
"""

class Evento:
    def __init__(self, id=None, processo_id=None, tipo_evento="", data_evento=None,
                 descricao="", documento_sei=None, responsavel=None, criado_em=None):
        self.id = id
        self.processo_id = processo_id
        self.tipo_evento = tipo_evento
        self.data_evento = str(data_evento) if data_evento else None
        self.descricao = descricao
        self.documento_sei = documento_sei
        self.responsavel = responsavel
        self.criado_em = str(criado_em) if criado_em else None

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            processo_id=data.get("processo_id"),
            tipo_evento=data.get("tipo_evento", ""),
            data_evento=data.get("data_evento"),
            descricao=data.get("descricao", ""),
            documento_sei=data.get("documento_sei"),
            responsavel=data.get("responsavel"),
            criado_em=data.get("criado_em")
        )

    def to_dict(self):
        return {
            "id": self.id,
            "processo_id": self.processo_id,
            "tipo_evento": self.tipo_evento,
            "data_evento": self.data_evento,
            "descricao": self.descricao,
            "documento_sei": self.documento_sei,
            "responsavel": self.responsavel,
            "criado_em": self.criado_em
        }
