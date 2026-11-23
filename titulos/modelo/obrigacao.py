"""
Módulo: modelo/obrigacao.py
Descrição: Modelo de dados para Prazos Legais e Obrigações (RFP, TAH, GU, RAL, Exigências).
"""

class Obrigacao:
    def __init__(self, id=None, processo_id=None, tipo_obrigacao="", descricao="",
                 ano_exercicio=None, data_referencia=None, data_vencimento=None,
                 data_cumprimento=None, status="Pendente", dias_para_vencer=None,
                 nivel_alerta="No Prazo", valor_devido=0.0, numero_guia_documento=None,
                 observacoes="", criado_em=None, atualizado_em=None):
        self.id = id
        self.processo_id = processo_id
        self.tipo_obrigacao = tipo_obrigacao
        self.descricao = descricao
        self.ano_exercicio = ano_exercicio
        self.data_referencia = str(data_referencia) if data_referencia else None
        self.data_vencimento = str(data_vencimento) if data_vencimento else None
        self.data_cumprimento = str(data_cumprimento) if data_cumprimento else None
        self.status = status
        self.dias_para_vencer = dias_para_vencer
        self.nivel_alerta = nivel_alerta
        self.valor_devido = float(valor_devido) if valor_devido else 0.0
        self.numero_guia_documento = numero_guia_documento
        self.observacoes = observacoes
        self.criado_em = str(criado_em) if criado_em else None
        self.atualizado_em = str(atualizado_em) if atualizado_em else None

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id") or data.get("obrigacao_id"),
            processo_id=data.get("processo_id"),
            tipo_obrigacao=data.get("tipo_obrigacao", ""),
            descricao=data.get("descricao", ""),
            ano_exercicio=data.get("ano_exercicio"),
            data_referencia=data.get("data_referencia"),
            data_vencimento=data.get("data_vencimento"),
            data_cumprimento=data.get("data_cumprimento"),
            status=data.get("status", "Pendente"),
            dias_para_vencer=data.get("dias_para_vencer"),
            nivel_alerta=data.get("nivel_alerta", "No Prazo"),
            valor_devido=data.get("valor_devido", 0.0),
            numero_guia_documento=data.get("numero_guia_documento"),
            observacoes=data.get("observacoes", ""),
            criado_em=data.get("criado_em"),
            atualizado_em=data.get("atualizado_em")
        )

    def to_dict(self):
        return {
            "id": self.id,
            "processo_id": self.processo_id,
            "tipo_obrigacao": self.tipo_obrigacao,
            "descricao": self.descricao,
            "ano_exercicio": self.ano_exercicio,
            "data_referencia": self.data_referencia,
            "data_vencimento": self.data_vencimento,
            "data_cumprimento": self.data_cumprimento,
            "status": self.status,
            "dias_para_vencer": self.dias_para_vencer,
            "nivel_alerta": self.nivel_alerta,
            "valor_devido": self.valor_devido,
            "numero_guia_documento": self.numero_guia_documento,
            "observacoes": self.observacoes,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em
        }
