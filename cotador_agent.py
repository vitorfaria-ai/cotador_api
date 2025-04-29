import pandas as pd
import unicodedata
import re

def normalizar_texto(texto):
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')  # remove acentos
    texto = texto.lower().strip()
    texto = re.sub(r'\b(s|es|is|os|as)\b', '', texto)  # remove plurais simples (ex.: dentes → dent)
    texto = re.sub(r'\s+', ' ', texto)  # remove espaços extras
    return texto
    
def comparar_termos(problema, termo):
    problema = normalizar_texto(problema)
    termo = normalizar_texto(termo)
    return termo in problema or problema in termo

def adicionar_mensagem_transbordo(mensagem, cobertura_reconhecida):
    if not cobertura_reconhecida:
        return (f"Essa cobertura é especial, então para te orientar melhor, vou te passar o plano padrão agora, e te coloco em contato com um especialista para te passar mais detalhes. O que acha? 😉\n\n"
                f"{mensagem}")
    return mensagem


def buscar_plano_fallback(planos, tipo_contrato, operadora_preferida, regras_operadora):
    planos_filtrados = planos[planos["tipo_contrato"] == tipo_contrato]
    planos_operadora = planos_filtrados[planos_filtrados["operadora"].str.contains(operadora_preferida, case=False, na=False)]
    if planos_operadora.empty:
        return None
    planos_com_prioridade = planos_operadora.merge(regras_operadora[["operadora", "prioridade"]], on="operadora").sort_values(by="prioridade")
    return planos_com_prioridade


def cotador_agent(input_usuario, planos, beneficios, formas_pagamento, regras_operadora):
    tipo_contrato = input_usuario["tipo_contrato"]
    problemas_dores = input_usuario["problemas_dores"]
    quantidade_vidas = input_usuario.get("quantidade_vidas", 1)
    operadora_preferida = input_usuario.get("operadora_preferida")

    coberturas_basicas = [
        "urgência", "emergência", "consulta", "limpeza", "profilaxia", "flúor",
        "raio x", "radiografia", "panorâmico", "periapical", 
        "gengiva", "periodontia",
        "canal", "endodontia",
        "odontopediatria", "pediatria",
        "restauração", "dentística",
        "cirurgia", "extração", "siso", "incluso",
        "prótese rol", "prótese básica",
        "documentação ortodôntica", "documentação básica"
    ]
    try:
        quantidade_vidas = int(quantidade_vidas)
        if quantidade_vidas < 1:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("O campo 'quantidade_vidas' precisa ser um número inteiro maior que zero.")

    if isinstance(problemas_dores, str):
        problemas_dores = [p.strip() for p in problemas_dores.split(",") if p.strip()]

    if not problemas_dores:
        raise ValueError("O campo 'problemas_dores' não pode ser vazio.")

    # Separar dores em básicas e especiais
    dores_basicas = []
    dores_especiais = []

    for problema in problemas_dores:
        problema_normalizado = normalizar_texto(problema)
        if any(comparar_termos(problema, palavra) for palavra in coberturas_basicas):
            dores_basicas.append(problema)
        else:
            dores_especiais.append(problema)


    correlacoes = {
        "autoligado": {"cobertura_associada": "tem_ortodontia", "mensagem": "Este plano não cobre aparelho autoligado, mas é o mais completo para tratamentos ortodônticos tradicionais.", "relacionado": True},
        "invisalign": {"cobertura_associada": "tem_ortodontia", "mensagem": "Este plano não cobre Invisalign, mas é o mais completo para tratamentos ortodônticos convencionais.", "relacionado": True},
        "alinhador invisível": {"cobertura_associada": "tem_ortodontia", "mensagem": "Este plano não cobre alinhador invisível, mas é o mais completo para tratamentos ortodônticos tradicionais.", "relacionado": True},
        "implante": {"mensagem": "Nenhum plano cobre implante dentário. Mas muitos clientes nessa situação optam pelo Dental E90, que é o plano de próteses mais completo do Brasil.", "plano_dedicado": "Dental E90", "relacionado": False},
        "protocolo": {"mensagem": "Nenhum plano cobre protocolo dentário. Mas muitos clientes nessa situação optam pelo Dental E90, que é o plano de próteses mais completo do Brasil.", "plano_dedicado": "Dental E90", "relacionado": False},
        "coroa de cerâmica": {"mensagem": "Para 'coroa de cerâmica', recomendamos planos com cobertura estética como o E90, Premium Top ou Master.", "plano_dedicado": "Dental E90", "relacionado": False},
        "inlay": {"mensagem": "Para 'inlay', recomendamos planos com cobertura estética como o E90, Premium Top ou Master.", "plano_dedicado": "Dental E90", "relacionado": False},
        "onlay": {"mensagem": "Para 'onlay', recomendamos planos com cobertura estética como o E90, Premium Top ou Master.", "plano_dedicado": "Dental E90", "relacionado": False},
        "ponte móvel": {"mensagem": "Para 'ponte móvel', recomendamos o plano E60 ou superiores.", "plano_dedicado": "Dental E60", "relacionado": False},
        "dentadura": {"mensagem": "Para 'dentadura', recomendamos o plano E60 ou superiores.", "plano_dedicado": "Dental E60", "relacionado": False},
        "aparelho": {"cobertura_associada": "tem_ortodontia", "mensagem": "Este plano cobre tratamento ortodôntico tradicional (aparelho fixo).", "relacionado": True},
        "aparelho dental": {"cobertura_associada": "tem_ortodontia", "mensagem": "Este plano cobre tratamento ortodôntico tradicional (aparelho fixo).", "relacionado": True},
        "aparelho ortodontico": {"cobertura_associada": "tem_ortodontia", "mensagem": "Este plano cobre tratamento ortodôntico tradicional (aparelho fixo).", "relacionado": True},
        "aparelho dentário": {"cobertura_associada": "tem_ortodontia", "mensagem": "Este plano cobre tratamento ortodôntico tradicional (aparelho fixo).", "relacionado": True},
    }

    resposta_especial = []
    plano_forcado = None

    for problema in problemas_dores:
        problema_lower = problema.lower()
        for termo, regra in correlacoes.items():
            if comparar_termos(problema, termo):
                if "plano_dedicado" in regra:
                    plano_forcado = regra["plano_dedicado"]
                if "mensagem" in regra:
                    resposta_especial.append({"mensagem": regra["mensagem"]})

    if plano_forcado:
        plano_escolhido = planos[planos["nome"].str.contains(plano_forcado, case=False)].iloc[0]
    else:
        planos_filtrados = planos[planos["tipo_contrato"] == tipo_contrato]
        operadora_filtrada = False
        if operadora_preferida:
            planos_operadora = planos_filtrados[planos_filtrados["operadora"].str.contains(operadora_preferida, case=False, na=False)]
            if not planos_operadora.empty:
                planos_filtrados = planos_operadora
                operadora_filtrada = True

        # 🟢 Agora usa a separação para decidir se aplica os benefícios ou não:
        if dores_especiais:
            planos_com_beneficios = planos_filtrados.merge(beneficios, left_on="id", right_on="plano_id").drop_duplicates(subset=["id"])
        else:
            planos_com_beneficios = planos_filtrados


        planos_com_prioridade = planos_com_beneficios.merge(regras_operadora[["operadora", "prioridade"]], on="operadora").sort_values(by="prioridade")

        if planos_com_prioridade.empty and operadora_preferida:
            planos_com_prioridade = buscar_plano_fallback(planos, tipo_contrato, operadora_preferida, regras_operadora)
            if planos_com_prioridade is None or planos_com_prioridade.empty:
                return [{"mensagem": f"Não encontramos nenhum plano da operadora {operadora_preferida} para o tipo de contrato {tipo_contrato}. 😕"}]


        # Agora finalmente escolhe:
        if planos_com_prioridade.empty:
            return [{"mensagem": f"Não encontramos nenhum plano disponível para o tipo de contrato {tipo_contrato}."}]
        plano_escolhido = planos_com_prioridade.iloc[0]





    # Verificação sensível para coberturas desconhecidas
    cobertura_reconhecida = True

    # Se existem dores especiais, verificar se elas são reconhecidas
    if dores_especiais:
        for problema in dores_especiais:
            cobertura_encontrada = any(comparar_termos(problema, termo) for termo in correlacoes)
            if not cobertura_encontrada:
                cobertura_reconhecida = False
                break
    else:
        # Se só existem dores básicas, consideramos reconhecido
        cobertura_reconhecida = True

    formas = formas_pagamento[formas_pagamento["plano_id"] == plano_escolhido["id"]]

    if tipo_contrato == "pj":
        # Primeiro tenta boleto mensal
        formas_filtradas = formas[
            (formas["forma"].str.contains("boleto", case=False, na=False)) &
            (formas["forma"].str.contains("mensal", case=False, na=False))
        ]

        # Se não encontrar boleto mensal, tenta qualquer boleto
        if formas_filtradas.empty:
            formas_filtradas = formas[
                (formas["forma"].str.contains("boleto", case=False, na=False))
            ]

        if formas_filtradas.empty:
            return [{"mensagem": "Não encontramos opção de boleto para este plano PJ."}]
        forma = formas_filtradas.iloc[0]
        preco = forma["preco"]
        mensagem_whatsapp = (f"🎯 *Plano Recomendado:* {plano_escolhido['nome']}\n\n"
                             f"✅ *Forma de pagamento:* {forma['forma']}\n"
                             f"💰 Preço por pessoa: R$ {preco:.2f}\n"
                             f"💳 Preço total (para {quantidade_vidas} pessoas): R$ {preco * quantidade_vidas:.2f}\n"
                             f"🕑 Carência: {forma['carencia']}")
        
        mensagem_whatsapp = adicionar_mensagem_transbordo(mensagem_whatsapp, cobertura_reconhecida)

        return [{
            "plano_recomendado": plano_escolhido["nome"],
            "preco_por_pessoa": f'R$ {preco:.2f}',
            "preco_total": f'R$ {preco * quantidade_vidas:.2f}',
            "quantidade_vidas": quantidade_vidas,
            "forma_pagamento": forma["forma"],
            "carências": forma["carencia"],
            "mensagem_whatsapp": mensagem_whatsapp.strip()
        }]

    else:
        agrupado = {}
        for _, forma in formas.iterrows():
            preco = forma["preco"]
            carencia = forma["carencia"]
            forma_nome = forma["forma"]
            if carencia not in agrupado:
                agrupado[carencia] = {
                    "formas_pagamento": [],
                    "preco": preco,
                    "carencia_texto": carencia
                }
            agrupado[carencia]["formas_pagamento"].append(forma_nome)

        mensagem_whatsapp = f"🎯 *Plano Recomendado:* {plano_escolhido['nome']}\nO preço e as carências variam de acordo com a forma de pagamento:\n\n"
        for group in agrupado.values():
            formas_texto = " ou ".join(group["formas_pagamento"])
            mensagem_whatsapp += (f"✅ *{formas_texto}:*\n"
                                  f"💰 Preço por pessoa: R$ {group['preco']:.2f}\n"
                                  f"💳 Preço total (para {quantidade_vidas} pessoas): R$ {group['preco'] * quantidade_vidas:.2f}\n"
                                  f"🕑 Carência: {group['carencia_texto']}\n\n")

        mensagem_whatsapp = adicionar_mensagem_transbordo(mensagem_whatsapp, cobertura_reconhecida)

        return [{
            "plano_recomendado": plano_escolhido["nome"],
            "quantidade_vidas": quantidade_vidas,
            "precos_carencias": [{
                "formas_pagamento": group["formas_pagamento"],
                "preco_por_pessoa": f'R$ {group["preco"]:.2f}',
                "preco_total": f'R$ {group["preco"] * quantidade_vidas:.2f}',
                "carencias": group["carencia_texto"]
            } for group in agrupado.values()],
            "mensagem_whatsapp": mensagem_whatsapp.strip()
        }]
