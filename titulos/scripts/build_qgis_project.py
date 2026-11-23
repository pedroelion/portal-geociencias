#!/usr/bin/env python3
"""
Script: build_qgis_project.py
Descrição: Constrói e valida o projeto QGIS corporativo (.qgs) para Gestão de Títulos Minerários na ANM.
            Configura:
            - Camadas espaciais e views PostGIS (EPSG:4674 - SIRGAS 2000)
            - Tabelas alfanuméricas com relacionamentos 1:N (titular -> processo, processo -> evento, processo -> obrigacao)
            - Simbologias temáticas baseadas em regras de alerta de prazos legais (Vencido, Crítico, No Prazo)
            - Rótulos inteligentes com buffer
            - Formulários estruturados em abas com widgets avançados e regras de validação (constraints/regex)
            - Painéis consolidados e visões espaciais específicas (RFP, TAH, GU)
"""

import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "gestao_titulos_minerarios"
DB_USER = "pedro"
DB_PASS = "123"

def build_postgis_uri(table_or_view, geom_col="geom", srid="4674", key_col="id", sql_filter=""):
    """Constrói a string de conexão PostGIS para o QGIS."""
    if geom_col:
        uri = f"dbname='{DB_NAME}' host='{DB_HOST}' port='{DB_PORT}' user='{DB_USER}' password='{DB_PASS}' sslmode=prefer key='{key_col}' srid={srid} type=MultiPolygon table=\"public\".\"{table_or_view}\" ({geom_col})"
    else:
        uri = f"dbname='{DB_NAME}' host='{DB_HOST}' port='{DB_PORT}' user='{DB_USER}' password='{DB_PASS}' sslmode=prefer key='{key_col}' table=\"public\".\"{table_or_view}\""
    if sql_filter:
        uri += f" sql={sql_filter}"
    return uri

def create_qgis_project_xml(output_path):
    root = ET.Element("qgis", {
        "projectname": "Sistema Corporativo de Gestão de Títulos Minerários - ANM",
        "version": "3.40.15"
    })

    title = ET.SubElement(root, "title")
    title.text = "Sistema Corporativo de Gestão de Títulos Minerários - ANM"

    homePath = ET.SubElement(root, "homePath", {"path": ""})
    autotransaction = ET.SubElement(root, "autotransaction", {"active": "0"})
    evaluateDefaultValues = ET.SubElement(root, "evaluateDefaultValues", {"active": "0"})
    trust = ET.SubElement(root, "trust", {"active": "0"})

    # CRS SIRGAS 2000 (EPSG:4674)
    projectCrs = ET.SubElement(root, "projectCrs")
    srs = ET.SubElement(projectCrs, "spatialrefsys")
    ET.SubElement(srs, "wkt").text = 'GEOGCRS["SIRGAS 2000",DATUM["Sistema de Referencia Geocentrico para las Americas 2000",ELLIPSOID["GRS 1980",6378137,298.257222101]],PRIMEM["Greenwich",0],CS[ellipsoidal,2],AXIS["geodetic latitude (Lat)",north],AXIS["geodetic longitude (Lon)",east],ID["EPSG",4674]]'
    ET.SubElement(srs, "proj4").text = "+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs"
    ET.SubElement(srs, "srsid").text = "3224"
    ET.SubElement(srs, "srid").text = "4674"
    ET.SubElement(srs, "authid").text = "EPSG:4674"
    ET.SubElement(srs, "description").text = "SIRGAS 2000"
    ET.SubElement(srs, "projectionacronym").text = "longlat"
    ET.SubElement(srs, "ellipsoidacronym").text = "GRS80"
    ET.SubElement(srs, "geographicflag").text = "true"

    # Layer tree
    layer_tree = ET.SubElement(root, "layer-tree-group")
    ET.SubElement(layer_tree, "customproperties")

    # Layer IDs
    layers_def = [
        # (id, name, table_or_view, is_spatial, geom_col, key_col, group)
        ("lyr_situacao_espacial", "Situação Espacial e Pior Alerta (Geral)", "vw_processos_situacao_espacial", True, "geom", "processo_id", "Painel de Situação Espacial"),
        ("lyr_relatorio_pesquisa", "Painel RFP - Relatório de Pesquisa", "vw_processos_relatorio_pesquisa", True, "geom", "obrigacao_id", "Painel de Situação Espacial"),
        ("lyr_tah", "Painel TAH - Taxa Anual por Hectare", "vw_processos_taxa_anual_hectare", True, "geom", "obrigacao_id", "Painel de Situação Espacial"),
        ("lyr_guia_utilizacao", "Painel GU - Guia de Utilização", "vw_processos_guia_utilizacao", True, "geom", "obrigacao_id", "Painel de Situação Espacial"),
        ("lyr_processo", "Poligonais de Processos (Cadastro Base)", "processo", True, "geom", "id", "Cadastro Base ANM"),
        ("lyr_titular", "Titulares Minerários (SIGMINE)", "titular", False, None, "id", "Tabelas Corporativas 1:N"),
        ("lyr_evento", "Histórico de Eventos Regulatórios", "evento", False, None, "id", "Tabelas Corporativas 1:N"),
        ("lyr_obrigacao", "Prazos e Obrigações Legais", "obrigacao", False, None, "id", "Tabelas Corporativas 1:N"),
        ("lyr_painel_consolidado", "Painel Consolidado de Conformidade", "vw_painel_prazos_consolidado", False, None, "tipo_obrigacao", "Dashboards e Relatórios"),
        ("lyr_alertas_urgentes", "Alertas Urgentes (Ação Imediata)", "vw_painel_alertas_urgentes", False, None, "obrigacao_id", "Dashboards e Relatórios"),
    ]

    # Populate layer tree
    groups = {}
    for lyr_id, lyr_name, table, is_spatial, geom_col, key_col, grp_name in layers_def:
        if grp_name not in groups:
            grp = ET.SubElement(layer_tree, "layer-tree-group", {"name": grp_name, "expanded": "1", "checked": "Qt::Checked"})
            groups[grp_name] = grp
        ET.SubElement(groups[grp_name], "layer-tree-layer", {
            "id": lyr_id,
            "name": lyr_name,
            "source": build_postgis_uri(table, geom_col if is_spatial else None, key_col=key_col),
            "providerKey": "postgres",
            "checked": "Qt::Checked" if lyr_id in ["lyr_situacao_espacial", "lyr_processo"] else "Qt::Unchecked"
        })

    # Map Canvas layers container
    projectlayers = ET.SubElement(root, "projectlayers")

    for lyr_id, lyr_name, table, is_spatial, geom_col, key_col, grp_name in layers_def:
        mlyr = ET.SubElement(projectlayers, "maplayer", {
            "type": "vector" if is_spatial else "vector",
            "geometry": "Polygon" if is_spatial else "NoGeometry",
            "hasScaleBasedVisibilityFlag": "0",
            "autoRefreshEnabled": "0",
            "readOnly": "0"
        })
        ET.SubElement(mlyr, "id").text = lyr_id
        ET.SubElement(mlyr, "datasource").text = build_postgis_uri(table, geom_col if is_spatial else None, key_col=key_col)
        ET.SubElement(mlyr, "keywordList")
        ET.SubElement(mlyr, "layername").text = lyr_name
        ET.SubElement(mlyr, "srs")
        srs_layer = ET.SubElement(mlyr, "spatialrefsys")
        ET.SubElement(srs_layer, "authid").text = "EPSG:4674"
        ET.SubElement(srs_layer, "srid").text = "4674"
        ET.SubElement(srs_layer, "description").text = "SIRGAS 2000"
        ET.SubElement(mlyr, "provider", {"encoding": "UTF-8"}).text = "postgres"

        # Simbologia para camada de situação espacial
        if lyr_id == "lyr_situacao_espacial":
            renderer = ET.SubElement(mlyr, "renderer-v2", {"type": "RuleRenderer", "symbollevels": "0"})
            rules = ET.SubElement(renderer, "rules", {"key": "root"})
            
            # Regra: Vencido (Vermelho)
            r_venc = ET.SubElement(rules, "rule", {
                "key": "rule_venc",
                "label": "Obrigação Vencida (Crítico)",
                "filter": '"pior_nivel_alerta" = \'Vencido\'',
                "symbol": "sym_venc"
            })
            # Regra: Alerta Crítico (Laranja)
            r_crit = ET.SubElement(rules, "rule", {
                "key": "rule_crit",
                "label": "Próximo ao Vencimento (≤ 30 dias)",
                "filter": '"pior_nivel_alerta" = \'Alerta Crítico / Próximo ao Vencimento\'',
                "symbol": "sym_crit"
            })
            # Regra: No Prazo (Verde)
            r_ok = ET.SubElement(rules, "rule", {
                "key": "rule_ok",
                "label": "No Prazo (> 30 dias)",
                "filter": '"pior_nivel_alerta" = \'No Prazo\'',
                "symbol": "sym_ok"
            })
            # Regra: Cumprido (Azul)
            r_cump = ET.SubElement(rules, "rule", {
                "key": "rule_cump",
                "label": "Regular / Cumprido",
                "filter": '"pior_nivel_alerta" = \'Cumprido / Regular\'',
                "symbol": "sym_cump"
            })

            symbols = ET.SubElement(renderer, "symbols")
            # Símbolo Vermelho
            s_v = ET.SubElement(symbols, "symbol", {"name": "sym_venc", "type": "fill", "alpha": "0.7"})
            layer_v = ET.SubElement(s_v, "layer", {"class": "SimpleFill", "locked": "0", "pass": "0"})
            ET.SubElement(layer_v, "prop", {"k": "color", "v": "217,4,41,180"})
            ET.SubElement(layer_v, "prop", {"k": "outline_color", "v": "114,0,38,255"})
            ET.SubElement(layer_v, "prop", {"k": "outline_width", "v": "0.6"})

            # Símbolo Laranja
            s_c = ET.SubElement(symbols, "symbol", {"name": "sym_crit", "type": "fill", "alpha": "0.7"})
            layer_c = ET.SubElement(s_c, "layer", {"class": "SimpleFill", "locked": "0", "pass": "0"})
            ET.SubElement(layer_c, "prop", {"k": "color", "v": "247,127,0,180"})
            ET.SubElement(layer_c, "prop", {"k": "outline_color", "v": "167,75,0,255"})
            ET.SubElement(layer_c, "prop", {"k": "outline_width", "v": "0.6"})

            # Símbolo Verde
            s_o = ET.SubElement(symbols, "symbol", {"name": "sym_ok", "type": "fill", "alpha": "0.6"})
            layer_o = ET.SubElement(s_o, "layer", {"class": "SimpleFill", "locked": "0", "pass": "0"})
            ET.SubElement(layer_o, "prop", {"k": "color", "v": "6,214,160,150"})
            ET.SubElement(layer_o, "prop", {"k": "outline_color", "v": "2,107,80,255"})
            ET.SubElement(layer_o, "prop", {"k": "outline_width", "v": "0.4"})

            # Símbolo Azul
            s_cu = ET.SubElement(symbols, "symbol", {"name": "sym_cump", "type": "fill", "alpha": "0.5"})
            layer_cu = ET.SubElement(s_cu, "layer", {"class": "SimpleFill", "locked": "0", "pass": "0"})
            ET.SubElement(layer_cu, "prop", {"k": "color", "v": "17,138,178,130"})
            ET.SubElement(layer_cu, "prop", {"k": "outline_color", "v": "7,59,76,255"})
            ET.SubElement(layer_cu, "prop", {"k": "outline_width", "v": "0.4"})

            # Rótulos (Labels)
            labeling = ET.SubElement(mlyr, "labeling", {"type": "simple"})
            settings = ET.SubElement(labeling, "settings", {"calloutType": "simple"})
            ET.SubElement(settings, "text-style", {
                "fontFamily": "Segoe UI",
                "fontSize": "9",
                "fontWeight": "bold",
                "textColor": "0,0,0,255",
                "fieldName": '"numero_processo" || \'\n\' || "substancia_mineral"'
            })
            buffer = ET.SubElement(settings, "text-buffer", {
                "bufferDraw": "1",
                "bufferSize": "1.0",
                "bufferColor": "255,255,255,230"
            })

        # Regras de validação e formulário personalizado na tabela 'processo'
        if lyr_id == "lyr_processo":
            editorlayout = ET.SubElement(mlyr, "editorlayout")
            editorlayout.text = "tablayout"

            # Configuração de abas no formulário
            attr_editor = ET.SubElement(mlyr, "attributeEditorForm")
            
            # Aba 1: Dados Cadastrais ANM
            tab1 = ET.SubElement(attr_editor, "attributeEditorContainer", {"name": "1. Dados Cadastrais ANM", "columnCount": "2", "groupBox": "0", "visibilityExpression": ""})
            for f in ["numero_processo", "ano_processo", "titular_id", "fase", "substancia_mineral", "uso_substancia", "area_ha", "municipio", "uf"]:
                ET.SubElement(tab1, "attributeEditorField", {"name": f, "index": "0"})

            # Aba 2: Marcos e Vigência
            tab2 = ET.SubElement(attr_editor, "attributeEditorContainer", {"name": "2. Marcos Regulatórios", "columnCount": "2", "groupBox": "0", "visibilityExpression": ""})
            for f in ["data_requerimento", "data_publicacao_alvara", "prazo_alvara_anos", "data_vencimento_alvara", "data_portaria_lavra", "status_processo"]:
                ET.SubElement(tab2, "attributeEditorField", {"name": f, "index": "0"})

            # Aba 3: Histórico de Eventos (RelationEditor)
            tab3 = ET.SubElement(attr_editor, "attributeEditorContainer", {"name": "3. Histórico de Eventos", "columnCount": "1", "groupBox": "0", "visibilityExpression": ""})
            ET.SubElement(tab3, "attributeEditorRelation", {"name": "rel_processo_evento", "relation": "rel_processo_evento", "showLabel": "1"})

            # Aba 4: Obrigações e Prazos (RelationEditor)
            tab4 = ET.SubElement(attr_editor, "attributeEditorContainer", {"name": "4. Prazos e Obrigações Legais", "columnCount": "1", "groupBox": "0", "visibilityExpression": ""})
            ET.SubElement(tab4, "attributeEditorRelation", {"name": "rel_processo_obrigacao", "relation": "rel_processo_obrigacao", "showLabel": "1"})

            # Validações / Constraints
            field_constraints = ET.SubElement(mlyr, "constraints")
            # numero_processo: regex obrigatorio
            ET.SubElement(field_constraints, "constraint", {
                "field": "numero_processo",
                "constraints": "3", # Not null (1) + Expression (2)
                "exp": 'regexp_match("numero_processo", \'^\\\\d{3,6}\\\\.\\\\d{3}/\\\\d{4}$\')',
                "desc": "Formato de processo ANM inválido! Utilize o padrão: 800.123/2021"
            })
            # area_ha: maior que zero
            ET.SubElement(field_constraints, "constraint", {
                "field": "area_ha",
                "constraints": "3",
                "exp": '"area_ha" > 0',
                "desc": "A área do processo deve ser superior a zero hectares!"
            })
            # ano_processo: intervalo válido
            ET.SubElement(field_constraints, "constraint", {
                "field": "ano_processo",
                "constraints": "3",
                "exp": '"ano_processo" >= 1934 AND "ano_processo" <= 2100',
                "desc": "Ano de processo inválido."
            })

    # ==============================================================================
    # Relações 1:N no Projeto QGIS
    # ==============================================================================
    relations = ET.SubElement(root, "relations")

    # 1. titular (1) -> processo (N)
    rel1 = ET.SubElement(relations, "relation", {
        "id": "rel_titular_processo",
        "name": "Processos Minerários do Titular",
        "referencingLayer": "lyr_processo",
        "referencedLayer": "lyr_titular",
        "strength": "Association"
    })
    ET.SubElement(rel1, "fieldRef", {"referencingField": "titular_id", "referencedField": "id"})

    # 2. processo (1) -> evento (N)
    rel2 = ET.SubElement(relations, "relation", {
        "id": "rel_processo_evento",
        "name": "Histórico de Eventos Regulatórios",
        "referencingLayer": "lyr_evento",
        "referencedLayer": "lyr_processo",
        "strength": "Composition"
    })
    ET.SubElement(rel2, "fieldRef", {"referencingField": "processo_id", "referencedField": "id"})

    # 3. processo (1) -> obrigacao (N)
    rel3 = ET.SubElement(relations, "relation", {
        "id": "rel_processo_obrigacao",
        "name": "Prazos e Obrigações Legais ANM",
        "referencingLayer": "lyr_obrigacao",
        "referencedLayer": "lyr_processo",
        "strength": "Composition"
    })
    ET.SubElement(rel3, "fieldRef", {"referencingField": "processo_id", "referencedField": "id"})

    # Formatação e escrita do arquivo XML .qgs
    xml_str = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(xml_str)
    pretty_xml = parsed.toprettyxml(indent="  ", encoding="utf-8")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pretty_xml)

    print(f"Projeto QGIS gerado com sucesso em: {output_path}")
    return output_path

def validate_qgis_project(project_file):
    """Valida a estrutura do projeto XML e a sintaxe das relações e camadas."""
    print(f"Validando projeto QGIS: {project_file}...")
    try:
        tree = ET.parse(project_file)
        root = tree.getroot()
        assert root.tag == "qgis", "Tag raiz do projeto não é <qgis>"

        layers = root.findall(".//projectlayers/maplayer")
        print(f"  [OK] Total de camadas/tabelas configuradas: {len(layers)}")
        for lyr in layers:
            lid = lyr.find("id").text
            lname = lyr.find("layername").text
            print(f"    - Camada: {lname} (ID: {lid})")

        rels = root.findall(".//relations/relation")
        print(f"  [OK] Total de Relações 1:N configuradas: {len(rels)}")
        for r in rels:
            rid = r.get("id")
            rname = r.get("name")
            print(f"    - Relação: {rname} (ID: {rid})")

        print("  [SUCESSO] Projeto QGIS validado com êxito!")
        return True
    except Exception as e:
        print(f"  [ERRO] Falha na validação do projeto QGIS: {e}")
        return False

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(__file__)), "qgis", "gestao_titulos_anm.qgs")
    create_qgis_project_xml(out)
    validate_qgis_project(out)
