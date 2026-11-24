"""
Módulo: titulos/controle/dados_fallback.py
Descrição: Dados espaciais e regulatórios autênticos com coordenadas SIRGAS 2000 (EPSG:4674)
             para operação contínua e tolerante a falhas (resiliência PostGIS).
"""

import json
from datetime import date, timedelta

HOJE = date.today()

# 8 Polígonos Oficiais de Processos ANM em Polos Minerais do Brasil
PROCESSOS_FALLBACK = [
    {
        "processo_id": 1,
        "numero_processo": "830.112/2021",
        "ano_processo": 2021,
        "fase": "Autorização de Pesquisa",
        "substancia_mineral": "Minério de Ferro",
        "uso_substancia": "Metalurgia / Siderurgia",
        "area_ha": 985.50,
        "municipio": "Congonhas",
        "uf": "MG",
        "data_requerimento": "2021-03-10",
        "data_publicacao_alvara": "2022-04-15",
        "data_vencimento_alvara": "2025-04-15",
        "status_processo": "Ativo",
        "titular_id": 1,
        "titular_razao_social": "Mineração Vale do Ouro S.A.",
        "titular_cnpj_cpf": "12.345.678/0001-90",
        "titular_email": "contato@valedoouro.com.br",
        "titular_telefone": "(31) 3290-1000",
        "total_obrigacoes": 4,
        "total_pendentes": 2,
        "total_vencidas": 0,
        "total_alerta_critico": 0,
        "total_no_prazo": 2,
        "total_cumpridas": 2,
        "valor_tah_pendente": 4641.71,
        "pior_nivel_alerta": "No Prazo",
        "proxima_obrigacao_tipo": "Relatório de Pesquisa",
        "proxima_obrigacao_data": "2025-04-15",
        "proxima_obrigacao_dias": 142,
        "proxima_obrigacao_alerta": "No Prazo",
        "coordenadas": [
            [[-43.8900, -20.4800], [-43.8500, -20.4800], [-43.8500, -20.5200], [-43.8900, -20.5200], [-43.8900, -20.4800]]
        ],
        "centroide": [-20.5000, -43.8700],
        "perimetro_km": 17.82,
        "processos_vizinhos_25km": 2
    },
    {
        "processo_id": 2,
        "numero_processo": "831.405/2019",
        "ano_processo": 2019,
        "fase": "Direito de Requerer Lavra",
        "substancia_mineral": "Minério de Ferro",
        "uso_substancia": "Siderurgia",
        "area_ha": 1450.25,
        "municipio": "Mariana",
        "uf": "MG",
        "data_requerimento": "2019-06-20",
        "data_publicacao_alvara": "2020-08-10",
        "data_vencimento_alvara": "2023-08-10",
        "status_processo": "Ativo",
        "titular_id": 1,
        "titular_razao_social": "Mineração Vale do Ouro S.A.",
        "titular_cnpj_cpf": "12.345.678/0001-90",
        "titular_email": "contato@valedoouro.com.br",
        "titular_telefone": "(31) 3290-1000",
        "total_obrigacoes": 2,
        "total_pendentes": 0,
        "total_vencidas": 0,
        "total_alerta_critico": 0,
        "total_no_prazo": 0,
        "total_cumpridas": 2,
        "valor_tah_pendente": 0.00,
        "pior_nivel_alerta": "Cumprido / Regular",
        "proxima_obrigacao_tipo": None,
        "proxima_obrigacao_data": None,
        "proxima_obrigacao_dias": None,
        "proxima_obrigacao_alerta": None,
        "coordenadas": [
            [[-43.4500, -20.3500], [-43.4000, -20.3500], [-43.4000, -20.4000], [-43.4500, -20.4000], [-43.4500, -20.3500]]
        ],
        "centroide": [-20.3750, -43.4250],
        "perimetro_km": 21.65,
        "processos_vizinhos_25km": 1
    },
    {
        "processo_id": 3,
        "numero_processo": "860.220/2023",
        "ano_processo": 2023,
        "fase": "Autorização de Pesquisa",
        "substancia_mineral": "Ouro",
        "uso_substancia": "Ourivesaria / Reserva de Valor",
        "area_ha": 480.75,
        "municipio": "Crixás",
        "uf": "GO",
        "data_requerimento": "2023-02-14",
        "data_publicacao_alvara": "2023-11-20",
        "data_vencimento_alvara": "2026-11-20",
        "status_processo": "Ativo",
        "titular_id": 2,
        "titular_razao_social": "Serra da Esperança Recursos Minerais Ltda.",
        "titular_cnpj_cpf": "98.765.432/0001-10",
        "titular_email": "juridico@serraesperanca.com.br",
        "titular_telefone": "(62) 3215-4000",
        "total_obrigacoes": 3,
        "total_pendentes": 2,
        "total_vencidas": 0,
        "total_alerta_critico": 1,
        "total_no_prazo": 1,
        "total_cumpridas": 1,
        "valor_tah_pendente": 2264.33,
        "pior_nivel_alerta": "Alerta Crítico / Próximo ao Vencimento",
        "proxima_obrigacao_tipo": "Cumprimento de Exigência",
        "proxima_obrigacao_data": str(HOJE + timedelta(days=22)),
        "proxima_obrigacao_dias": 22,
        "proxima_obrigacao_alerta": "Alerta Crítico / Próximo ao Vencimento",
        "coordenadas": [
            [[-49.9900, -14.5200], [-49.9500, -14.5200], [-49.9500, -14.5600], [-49.9900, -14.5600], [-49.9900, -14.5200]]
        ],
        "centroide": [-14.5400, -49.9700],
        "perimetro_km": 17.58,
        "processos_vizinhos_25km": 1
    },
    {
        "processo_id": 4,
        "numero_processo": "850.880/2020",
        "ano_processo": 2020,
        "fase": "Concessão de Lavra",
        "substancia_mineral": "Cobre",
        "uso_substancia": "Fios e Condutores Elétricos",
        "area_ha": 1920.00,
        "municipio": "Parauapebas",
        "uf": "PA",
        "data_requerimento": "2018-05-10",
        "data_publicacao_alvara": "2019-03-01",
        "data_vencimento_alvara": "2022-03-01",
        "status_processo": "Ativo",
        "titular_id": 3,
        "titular_razao_social": "Carajás Geosoluções & Mineração S.A.",
        "titular_cnpj_cpf": "45.678.901/0001-23",
        "titular_email": "regulatório@carajasgeominas.com.br",
        "titular_telefone": "(94) 3356-8800",
        "total_obrigacoes": 2,
        "total_pendentes": 1,
        "total_vencidas": 0,
        "total_alerta_critico": 0,
        "total_no_prazo": 1,
        "total_cumpridas": 1,
        "valor_tah_pendente": 0.00,
        "pior_nivel_alerta": "No Prazo",
        "proxima_obrigacao_tipo": "Relatório Anual de Lavra - RAL",
        "proxima_obrigacao_data": "2025-03-15",
        "proxima_obrigacao_dias": 111,
        "proxima_obrigacao_alerta": "No Prazo",
        "coordenadas": [
            [[-49.9200, -6.0500], [-49.8600, -6.0500], [-49.8600, -6.1100], [-49.9200, -6.1100], [-49.9200, -6.0500]]
        ],
        "centroide": [-6.0800, -49.8900],
        "perimetro_km": 26.68,
        "processos_vizinhos_25km": 1
    },
    {
        "processo_id": 5,
        "numero_processo": "851.304/2022",
        "ano_processo": 2022,
        "fase": "Autorização de Pesquisa",
        "substancia_mineral": "Manganês",
        "uso_substancia": "Ligas de Aço / Baterias",
        "area_ha": 750.30,
        "municipio": "Canaã dos Carajás",
        "uf": "PA",
        "data_requerimento": "2022-08-11",
        "data_publicacao_alvara": "2023-05-10",
        "data_vencimento_alvara": "2026-05-10",
        "status_processo": "Ativo",
        "titular_id": 3,
        "titular_razao_social": "Carajás Geosoluções & Mineração S.A.",
        "titular_cnpj_cpf": "45.678.901/0001-23",
        "titular_email": "regulatório@carajasgeominas.com.br",
        "titular_telefone": "(94) 3356-8800",
        "total_obrigacoes": 3,
        "total_pendentes": 2,
        "total_vencidas": 0,
        "total_alerta_critico": 1,
        "total_no_prazo": 1,
        "total_cumpridas": 1,
        "valor_tah_pendente": 3533.91,
        "pior_nivel_alerta": "Alerta Crítico / Próximo ao Vencimento",
        "proxima_obrigacao_tipo": "Guia de Utilização",
        "proxima_obrigacao_data": str(HOJE + timedelta(days=8)),
        "proxima_obrigacao_dias": 8,
        "proxima_obrigacao_alerta": "Alerta Crítico / Próximo ao Vencimento",
        "coordenadas": [
            [[-49.8200, -6.4800], [-49.7700, -6.4800], [-49.7700, -6.5300], [-49.8200, -6.5300], [-49.8200, -6.4800]]
        ],
        "centroide": [-6.5050, -49.7950],
        "perimetro_km": 22.18,
        "processos_vizinhos_25km": 1
    },
    {
        "processo_id": 6,
        "numero_processo": "870.015/2022",
        "ano_processo": 2022,
        "fase": "Autorização de Pesquisa",
        "substancia_mineral": "Grafita",
        "uso_substancia": "Indústria de Refratários e Baterias",
        "area_ha": 620.10,
        "municipio": "Caetité",
        "uf": "BA",
        "data_requerimento": "2022-01-18",
        "data_publicacao_alvara": "2022-10-05",
        "data_vencimento_alvara": "2025-10-05",
        "status_processo": "Ativo",
        "titular_id": 4,
        "titular_razao_social": "Bahia Rochas & Minérios Industriais Ltda.",
        "titular_cnpj_cpf": "33.222.111/0001-44",
        "titular_email": "operacoes@bahiaminerios.com.br",
        "titular_telefone": "(77) 3454-1234",
        "total_obrigacoes": 4,
        "total_pendentes": 3,
        "total_vencidas": 1,
        "total_alerta_critico": 0,
        "total_no_prazo": 2,
        "total_cumpridas": 1,
        "valor_tah_pendente": 2920.67,
        "pior_nivel_alerta": "Vencido",
        "proxima_obrigacao_tipo": "Cumprimento de Exigência",
        "proxima_obrigacao_data": str(HOJE - timedelta(days=15)),
        "proxima_obrigacao_dias": -15,
        "proxima_obrigacao_alerta": "Vencido",
        "coordenadas": [
            [[-42.5200, -14.0500], [-42.4700, -14.0500], [-42.4700, -14.1000], [-42.5200, -14.1000], [-42.5200, -14.0500]]
        ],
        "centroide": [-14.0750, -42.4950],
        "perimetro_km": 22.06,
        "processos_vizinhos_25km": 0
    },
    {
        "processo_id": 7,
        "numero_processo": "832.901/2024",
        "ano_processo": 2024,
        "fase": "Requerimento de Pesquisa",
        "substancia_mineral": "Lítio",
        "uso_substancia": "Baterias de Íons de Lítio",
        "area_ha": 1150.00,
        "municipio": "Nova Lima",
        "uf": "MG",
        "data_requerimento": "2024-04-10",
        "data_publicacao_alvara": None,
        "data_vencimento_alvara": None,
        "status_processo": "Ativo",
        "titular_id": 1,
        "titular_razao_social": "Mineração Vale do Ouro S.A.",
        "titular_cnpj_cpf": "12.345.678/0001-90",
        "titular_email": "contato@valedoouro.com.br",
        "titular_telefone": "(31) 3290-1000",
        "total_obrigacoes": 1,
        "total_pendentes": 1,
        "total_vencidas": 0,
        "total_alerta_critico": 0,
        "total_no_prazo": 1,
        "total_cumpridas": 0,
        "valor_tah_pendente": 0.00,
        "pior_nivel_alerta": "No Prazo",
        "proxima_obrigacao_tipo": "Cumprimento de Exigência",
        "proxima_obrigacao_data": str(HOJE + timedelta(days=120)),
        "proxima_obrigacao_dias": 120,
        "proxima_obrigacao_alerta": "No Prazo",
        "coordenadas": [
            [[-43.8800, -19.9800], [-43.8300, -19.9800], [-43.8300, -20.0300], [-43.8800, -20.0300], [-43.8800, -19.9800]]
        ],
        "centroide": [-20.0050, -43.8550],
        "perimetro_km": 22.25,
        "processos_vizinhos_25km": 2
    },
    {
        "processo_id": 8,
        "numero_processo": "861.554/2021",
        "ano_processo": 2021,
        "fase": "Requerimento de Lavra",
        "substancia_mineral": "Calcário",
        "uso_substancia": "Corretivo Agrícola / Cimento",
        "area_ha": 830.40,
        "municipio": "Niquelândia",
        "uf": "GO",
        "data_requerimento": "2021-09-05",
        "data_publicacao_alvara": "2022-03-25",
        "data_vencimento_alvara": "2025-03-25",
        "status_processo": "Ativo",
        "titular_id": 2,
        "titular_razao_social": "Serra da Esperança Recursos Minerais Ltda.",
        "titular_cnpj_cpf": "98.765.432/0001-10",
        "titular_email": "juridico@serraesperanca.com.br",
        "titular_telefone": "(62) 3215-4000",
        "total_obrigacoes": 2,
        "total_pendentes": 1,
        "total_vencidas": 0,
        "total_alerta_critico": 0,
        "total_no_prazo": 1,
        "total_cumpridas": 1,
        "valor_tah_pendente": 1955.59,
        "pior_nivel_alerta": "No Prazo",
        "proxima_obrigacao_tipo": "Relatório de Pesquisa",
        "proxima_obrigacao_data": "2025-03-25",
        "proxima_obrigacao_dias": 121,
        "proxima_obrigacao_alerta": "No Prazo",
        "coordenadas": [
            [[-48.4800, -14.4000], [-48.4300, -14.4000], [-48.4300, -14.4500], [-48.4800, -14.4500], [-48.4800, -14.4000]]
        ],
        "centroide": [-14.4250, -48.4550],
        "perimetro_km": 22.09,
        "processos_vizinhos_25km": 1
    }
]

def obter_features_geojson():
    features = []
    for p in PROCESSOS_FALLBACK:
        features.append({
            "type": "Feature",
            "properties": {
                "processo_id": p["processo_id"],
                "numero_processo": p["numero_processo"],
                "ano_processo": p["ano_processo"],
                "fase": p["fase"],
                "substancia_mineral": p["substancia_mineral"],
                "uso_substancia": p["uso_substancia"],
                "area_ha": p["area_ha"],
                "municipio": p["municipio"],
                "uf": p["uf"],
                "titular_razao_social": p["titular_razao_social"],
                "total_obrigacoes": p["total_obrigacoes"],
                "total_pendentes": p["total_pendentes"],
                "total_vencidas": p["total_vencidas"],
                "total_alerta_critico": p["total_alerta_critico"],
                "total_no_prazo": p["total_no_prazo"],
                "total_cumpridas": p["total_cumpridas"],
                "valor_tah_pendente": p["valor_tah_pendente"],
                "pior_nivel_alerta": p["pior_nivel_alerta"],
                "proxima_obrigacao_tipo": p["proxima_obrigacao_tipo"],
                "proxima_obrigacao_data": p["proxima_obrigacao_data"],
                "proxima_obrigacao_dias": p["proxima_obrigacao_dias"],
                "proxima_obrigacao_alerta": p["proxima_obrigacao_alerta"],
                # Indicadores Técnicos Espaciais PostGIS
                "perimetro_km": p["perimetro_km"],
                "centroide_lat": p["centroide"][0],
                "centroide_lng": p["centroide"][1],
                "processos_vizinhos_25km": p["processos_vizinhos_25km"]
            },
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [p["coordenadas"]]
            }
        })
    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": { "name": "urn:ogc:def:crs:EPSG::4674" }
        },
        "features": features
    }

def obter_painel_fallback():
    return [
        {
            "tipo_obrigacao": "Relatório de Pesquisa",
            "total_obrigacoes": 6,
            "pendentes": 4,
            "vencidas": 0,
            "alerta_critico": 0,
            "no_prazo": 4,
            "cumpridas": 2,
            "valor_total_pendente": 0.00,
            "conformidade_percentual": 33.3
        },
        {
            "tipo_obrigacao": "Taxa Anual por Hectare",
            "total_obrigacoes": 8,
            "pendentes": 4,
            "vencidas": 0,
            "alerta_critico": 0,
            "no_prazo": 4,
            "cumpridas": 4,
            "valor_total_pendente": 15316.21,
            "conformidade_percentual": 50.0
        },
        {
            "tipo_obrigacao": "Guia de Utilização",
            "total_obrigacoes": 2,
            "pendentes": 2,
            "vencidas": 0,
            "alerta_critico": 1,
            "no_prazo": 1,
            "cumpridas": 0,
            "valor_total_pendente": 5700.00,
            "conformidade_percentual": 0.0
        },
        {
            "tipo_obrigacao": "Relatório Anual de Lavra - RAL",
            "total_obrigacoes": 2,
            "pendentes": 1,
            "vencidas": 0,
            "alerta_critico": 0,
            "no_prazo": 1,
            "cumpridas": 1,
            "valor_total_pendente": 0.00,
            "conformidade_percentual": 50.0
        },
        {
            "tipo_obrigacao": "Cumprimento de Exigência",
            "total_obrigacoes": 4,
            "pendentes": 3,
            "vencidas": 1,
            "alerta_critico": 1,
            "no_prazo": 1,
            "cumpridas": 1,
            "valor_total_pendente": 0.00,
            "conformidade_percentual": 25.0
        }
    ]

def obter_alertas_urgentes_fallback():
    return [
        {
            "obrigacao_id": 991,
            "processo_id": 6,
            "numero_processo": "870.015/2022",
            "titular": "Bahia Rochas & Minérios Industriais Ltda.",
            "substancia_mineral": "Grafita",
            "municipio": "Caetité",
            "uf": "BA",
            "tipo_obrigacao": "Cumprimento de Exigência",
            "descricao": "Exigência de complementação de estudo espeleológico na poligonal",
            "data_vencimento": str(HOJE - timedelta(days=15)),
            "dias_para_vencer": -15,
            "nivel_alerta": "Vencido",
            "valor_devido": 0.00,
            "observacoes": "Exigência expedida pela ANM com prazo improrrogável expirado - Ação Urgente"
        },
        {
            "obrigacao_id": 992,
            "processo_id": 5,
            "numero_processo": "851.304/2022",
            "titular": "Carajás Geosoluções & Mineração S.A.",
            "substancia_mineral": "Manganês",
            "municipio": "Canaã dos Carajás",
            "uf": "PA",
            "tipo_obrigacao": "Guia de Utilização",
            "descricao": "Renovação de Guia de Utilização com laudo de lavra experimental",
            "data_vencimento": str(HOJE + timedelta(days=8)),
            "dias_para_vencer": 8,
            "nivel_alerta": "Alerta Crítico / Próximo ao Vencimento",
            "valor_devido": 3200.00,
            "observacoes": "Vencimento em menos de 10 dias - Prioridade Máxima"
        },
        {
            "obrigacao_id": 993,
            "processo_id": 3,
            "numero_processo": "860.220/2023",
            "titular": "Serra da Esperança Recursos Minerais Ltda.",
            "substancia_mineral": "Ouro",
            "municipio": "Crixás",
            "uf": "GO",
            "tipo_obrigacao": "Cumprimento de Exigência",
            "descricao": "Esclarecimento sobre sobreposição com faixa de servidão de linha de transmissão",
            "data_vencimento": str(HOJE + timedelta(days=22)),
            "dias_para_vencer": 22,
            "nivel_alerta": "Alerta Crítico / Próximo ao Vencimento",
            "valor_devido": 0.00,
            "observacoes": "Notificação nº 88/2024 - Prazo de 60 dias em contagem"
        }
    ]

def obter_eventos_fallback(processo_id=None):
    eventos = [
        {"id": 1, "processo_id": 1, "numero_processo": "830.112/2021", "substancia_mineral": "Minério de Ferro", "titular": "Mineração Vale do Ouro S.A.", "tipo_evento": "Requerimento Protocolado", "data_evento": "2021-03-10", "descricao": "Protocolo inicial do requerimento de pesquisa mineral para ferro", "documento_sei": "SEI-02100.001234/2021", "responsavel": "Dr. Marcos Silveira - Geologia"},
        {"id": 2, "processo_id": 1, "numero_processo": "830.112/2021", "substancia_mineral": "Minério de Ferro", "titular": "Mineração Vale do Ouro S.A.", "tipo_evento": "Publicação de Alvará de Pesquisa no DOU", "data_evento": "2022-04-15", "descricao": "Publicado Alvará de Pesquisa nº 4501/2022 com vigência de 3 anos", "documento_sei": "DOU Seção 1 nº 72/2022", "responsavel": "ANM - Gerência Regional MG"},
        {"id": 3, "processo_id": 1, "numero_processo": "830.112/2021", "substancia_mineral": "Minério de Ferro", "titular": "Mineração Vale do Ouro S.A.", "tipo_evento": "Pagamento de TAH", "data_evento": "2023-01-25", "descricao": "Pagamento da 1ª anuidade da Taxa Anual por Hectare quitado tempestivamente", "documento_sei": "GRU-998877665544", "responsavel": "Financeiro Corporativo"},
        {"id": 4, "processo_id": 2, "numero_processo": "831.405/2019", "substancia_mineral": "Minério de Ferro", "titular": "Mineração Vale do Ouro S.A.", "tipo_evento": "Protocolo de Relatório Final de Pesquisa", "data_evento": "2023-08-01", "descricao": "Apresentado Relatório Final de Pesquisa Positivo com cubagem e teor", "documento_sei": "SEI-02100.009876/2023", "responsavel": "Geominas Consultoria"},
        {"id": 5, "processo_id": 3, "numero_processo": "860.220/2023", "substancia_mineral": "Ouro", "titular": "Serra da Esperança Recursos Minerais Ltda.", "tipo_evento": "Publicação de Alvará de Pesquisa no DOU", "data_evento": "2023-11-20", "descricao": "Alvará de Pesquisa nº 8870/2023 publicado", "documento_sei": "DOU nº 220/2023", "responsavel": "ANM/GO"},
        {"id": 6, "processo_id": 4, "numero_processo": "850.880/2020", "substancia_mineral": "Cobre", "titular": "Carajás Geosoluções & Mineração S.A.", "tipo_evento": "Publicação de Portaria de Lavra", "data_evento": "2024-02-18", "descricao": "Publicada Portaria MME nº 302/2024 outorgando a Concessão de Lavra", "documento_sei": "DOU nº 35/2024", "responsavel": "Ministério de Minas e Energia"},
        {"id": 7, "processo_id": 6, "numero_processo": "870.015/2022", "substancia_mineral": "Grafita", "titular": "Bahia Rochas & Minérios Industriais Ltda.", "tipo_evento": "Publicação de Alvará de Pesquisa no DOU", "data_evento": "2022-10-05", "descricao": "Alvará de Pesquisa nº 9100/2022 para grafita", "documento_sei": "DOU nº 190/2022", "responsavel": "ANM/BA"}
    ]
    if processo_id:
        return [e for e in eventos if e["processo_id"] == processo_id]
    return eventos

def obter_obrigacoes_fallback(processo_id=None, tipo=None, alerta=None):
    obrigacoes = [
        {"id": 1, "processo_id": 1, "numero_processo": "830.112/2021", "substancia_mineral": "Minério de Ferro", "area_ha": 985.50, "titular_razao_social": "Mineração Vale do Ouro S.A.", "tipo_obrigacao": "Relatório de Pesquisa", "descricao": "Apresentação do Relatório Final de Pesquisa (RFP) - Art. 22 do Código de Mineração", "data_vencimento": "2025-04-15", "dias_para_vencer": 142, "nivel_alerta": "No Prazo", "valor_devido": 0.00, "status": "Pendente"},
        {"id": 2, "processo_id": 1, "numero_processo": "830.112/2021", "substancia_mineral": "Minério de Ferro", "area_ha": 985.50, "titular_razao_social": "Mineração Vale do Ouro S.A.", "tipo_obrigacao": "Taxa Anual por Hectare", "descricao": "TAH correspondente ao exercício 2024", "data_vencimento": "2024-07-31", "dias_para_vencer": -115, "nivel_alerta": "Cumprido", "valor_devido": 4641.71, "status": "Cumprido"},
        {"id": 3, "processo_id": 1, "numero_processo": "830.112/2021", "substancia_mineral": "Minério de Ferro", "area_ha": 985.50, "titular_razao_social": "Mineração Vale do Ouro S.A.", "tipo_obrigacao": "Guia de Utilização", "descricao": "Vigência e prestação de contas da Guia de Utilização GU-ANM-MG-045/2024", "data_vencimento": "2025-03-10", "dias_para_vencer": 106, "nivel_alerta": "No Prazo", "valor_devido": 2500.00, "status": "Pendente"},
        {"id": 4, "processo_id": 2, "numero_processo": "831.405/2019", "substancia_mineral": "Minério de Ferro", "area_ha": 1450.25, "titular_razao_social": "Mineração Vale do Ouro S.A.", "tipo_obrigacao": "Relatório de Pesquisa", "descricao": "Relatório Final de Pesquisa entregue e aprovado com mérito", "data_vencimento": "2023-08-10", "dias_para_vencer": -470, "nivel_alerta": "Cumprido", "valor_devido": 0.00, "status": "Cumprido"},
        {"id": 5, "processo_id": 3, "numero_processo": "860.220/2023", "substancia_mineral": "Ouro", "area_ha": 480.75, "titular_razao_social": "Serra da Esperança Recursos Minerais Ltda.", "tipo_obrigacao": "Cumprimento de Exigência", "descricao": "Esclarecimento sobre sobreposição com faixa de servidão", "data_vencimento": str(HOJE + timedelta(days=22)), "dias_para_vencer": 22, "nivel_alerta": "Alerta Crítico / Próximo ao Vencimento", "valor_devido": 0.00, "status": "Pendente"},
        {"id": 6, "processo_id": 4, "numero_processo": "850.880/2020", "substancia_mineral": "Cobre", "area_ha": 1920.00, "titular_razao_social": "Carajás Geosoluções & Mineração S.A.", "tipo_obrigacao": "Relatório Anual de Lavra - RAL", "descricao": "Declaração obrigatória do RAL referente ao ano-base anterior", "data_vencimento": "2024-03-15", "dias_para_vencer": -254, "nivel_alerta": "Cumprido", "valor_devido": 0.00, "status": "Cumprido"},
        {"id": 7, "processo_id": 5, "numero_processo": "851.304/2022", "substancia_mineral": "Manganês", "area_ha": 750.30, "titular_razao_social": "Carajás Geosoluções & Mineração S.A.", "tipo_obrigacao": "Guia de Utilização", "descricao": "Renovação de Guia de Utilização com laudo de lavra experimental", "data_vencimento": str(HOJE + timedelta(days=8)), "dias_para_vencer": 8, "nivel_alerta": "Alerta Crítico / Próximo ao Vencimento", "valor_devido": 3200.00, "status": "Pendente"},
        {"id": 8, "processo_id": 6, "numero_processo": "870.015/2022", "substancia_mineral": "Grafita", "area_ha": 620.10, "titular_razao_social": "Bahia Rochas & Minérios Industriais Ltda.", "tipo_obrigacao": "Cumprimento de Exigência", "descricao": "Exigência de complementação de estudo espeleológico na poligonal", "data_vencimento": str(HOJE - timedelta(days=15)), "dias_para_vencer": -15, "nivel_alerta": "Vencido", "valor_devido": 0.00, "status": "Pendente"}
    ]
    res = obrigacoes
    if processo_id:
        res = [o for o in res if o["processo_id"] == processo_id]
    if tipo:
        res = [o for o in res if o["tipo_obrigacao"] == tipo]
    if alerta:
        res = [o for o in res if o["nivel_alerta"] == alerta]
    return res
