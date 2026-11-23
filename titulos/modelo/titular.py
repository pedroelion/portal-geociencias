"""
Módulo: modelo/titular.py
Descrição: Modelo de dados para Titular de direitos minerários (SIGMINE).
"""

class Titular:
    def __init__(self, id=None, cnpj_cpf="", razao_social="", nome_fantasia=None,
                 tipo_pessoa="PJ", email="", telefone=None, endereco=None,
                 cidade="", uf="", criado_em=None):
        self.id = id
        self.cnpj_cpf = cnpj_cpf
        self.razao_social = razao_social
        self.nome_fantasia = nome_fantasia or razao_social
        self.tipo_pessoa = tipo_pessoa
        self.email = email
        self.telefone = telefone
        self.endereco = endereco
        self.cidade = cidade
        self.uf = uf
        self.criado_em = str(criado_em) if criado_em else None

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            cnpj_cpf=data.get("cnpj_cpf", ""),
            razao_social=data.get("razao_social", ""),
            nome_fantasia=data.get("nome_fantasia"),
            tipo_pessoa=data.get("tipo_pessoa", "PJ"),
            email=data.get("email", ""),
            telefone=data.get("telefone"),
            endereco=data.get("endereco"),
            cidade=data.get("cidade", ""),
            uf=data.get("uf", ""),
            criado_em=data.get("criado_em")
        )

    def to_dict(self):
        return {
            "id": self.id,
            "cnpj_cpf": self.cnpj_cpf,
            "razao_social": self.razao_social,
            "nome_fantasia": self.nome_fantasia,
            "tipo_pessoa": self.tipo_pessoa,
            "email": self.email,
            "telefone": self.telefone,
            "endereco": self.endereco,
            "cidade": self.cidade,
            "uf": self.uf,
            "criado_em": self.criado_em
        }
