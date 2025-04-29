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
"plano infantil": {"mensagem": "Para crianças, recomendamos planos com cobertura odontopediátrica especializada.","plano_dedicado": "Dental K25 - Linha Kids", "relacionado": False},
"para criança": {"mensagem": "Para crianças, recomendamos planos com cobertura odontopediátrica especializada.","plano_dedicado": "Dental K25 - Linha Kids", "relacionado": False},
}

def cotador_agent(input_usuario, todos_produtos):
    todos_produtos['nome_plano'] = todos_produtos['nome_plano'].str.lower().str.strip()
    todos_produtos['tipo_contrato'] = todos_produtos['tipo_contrato'].str.lower().str.strip()
    todos_produtos['cobertura'] = todos_produtos['cobertura'].str.lower().str.strip()

    tipo_contrato = input_usuario["tipo_contrato"]

    # Se o cliente informar que é MEI, tratamos como PJ para a maioria dos casos
    tipo_contrato_cliente = tipo_contrato.lower()

    # Ajuste interno: MEI se comporta como PJ para Amil e Hapvida
    if tipo_contrato_cliente == "mei":
        tipo_contrato_interno = "pj"
    else:
        tipo_contrato_interno = tipo_contrato_cliente

    problemas_dores = input_usuario["problemas_dores"]
    quantidade_vidas = input_usuario.get("quantidade_vidas", 1)
    operadora_preferida = input_usuario.get("operadora_preferida")

    if isinstance(problemas_dores, str):
        problemas_dores = [p.strip() for p in problemas_dores.split(",") if p.strip()]

    if not problemas_dores:
        raise ValueError("O campo 'problemas_dores' não pode ser vazio.")
    try:
        quantidade_vidas = int(quantidade_vidas)
        if quantidade_vidas < 1:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("O campo 'quantidade_vidas' precisa ser um número inteiro maior que zero.")
        
    # 1. Separar as dores básicas e especiais, como já fazemos:
    dores_basicas = []
    dores_especiais = []

    for problema in problemas_dores:
        problema_normalizado = normalizar_texto(problema)
        if any(comparar_termos(problema, palavra) for palavra in coberturas_basicas):
            dores_basicas.append(problema)
        else:
            dores_especiais.append(problema)

    # Verificar se alguma dor exige plano específico
    plano_forcado = None
    mensagem_especial = None

    for problema in problemas_dores:
        problema_normalizado = normalizar_texto(problema)
        for termo, regra in correlacoes.items():
            if comparar_termos(problema_normalizado, termo):
                # Somente ativa plano forçado se for termo muito específico (infantil, aparelho, prótese estética, clareamento, etc.)
                if "plano_dedicado" in regra:
                    plano_forcado = regra["plano_dedicado"]
                    mensagem_especial = regra.get("mensagem")
                    break  # encontrou plano específico, encerra busca
        if plano_forcado:
            break  # sai também do loop externo assim que achar um plano dedicado

    # Se existe plano forçado via correlacoes
    if plano_forcado:
        produtos_contrato = todos_produtos[
            (todos_produtos['nome_plano'].str.lower().str.strip().str.contains(plano_forcado.lower().strip(), na=False)) &
            (todos_produtos['tipo_contrato'].str.lower().str.strip() == tipo_contrato_cliente)
        ]

        if operadora_preferida:
            preferidos = produtos_contrato[
                produtos_contrato["operadora"].str.lower().str.contains(operadora_preferida.lower().strip(), na=False)
            ]
            if not preferidos.empty:
                produtos_contrato = preferidos  # Usa a operadora preferida, se existir
            # senão, mantém os planos encontrados (de outras operadoras)

        if produtos_contrato.empty:
            return [{"mensagem": f"Não encontramos o plano especial {plano_forcado} para o tipo de contrato {tipo_contrato_cliente}."}]
    else:
        # Se não tem plano forçado, escolhe baseado na prioridade e cobertura das dores especiais
        produtos_contrato = todos_produtos[
            (todos_produtos['tipo_contrato'] == tipo_contrato_cliente) &
            (todos_produtos['cobertura'].apply(lambda cob: any(comparar_termos(cob, dor) for dor in dores_especiais)))
        ]

        # Se não achar nada pela cobertura especial, considera coberturas básicas (padrão Dental 205 ou equivalente)
        if produtos_contrato.empty:
            produtos_contrato = todos_produtos[
                (todos_produtos['tipo_contrato'] == tipo_contrato_cliente) &
                (todos_produtos['cobertura'].apply(lambda cob: any(comparar_termos(cob, dor) for dor in dores_basicas)))
            ]

        # Caso extremo: se ainda vazio, seleciona por tipo contrato apenas (garantir retorno)
        if produtos_contrato.empty:
            produtos_contrato = todos_produtos[todos_produtos['tipo_contrato'] == tipo_contrato_cliente]


    # Ordenar por prioridade e preço SEMPRE
    planos_ordenados = produtos_contrato.sort_values(by=["prioridade_operadora", "preco"])
    plano_escolhido = planos_ordenados.iloc[0]


    # Verificação sensível para coberturas desconhecidas
    cobertura_reconhecida = True

    if dores_especiais:
        dores_reconhecidas = 0
        for dor in dores_especiais:
            encontrou = produtos_contrato['cobertura'].apply(lambda c: comparar_termos(c, dor)).any()
            if encontrou:
                dores_reconhecidas += 1

        if dores_reconhecidas < len(dores_especiais):
            cobertura_reconhecida = False


    # Filtra as formas disponíveis para o plano escolhido
    formas_disponiveis = todos_produtos[
        (todos_produtos['nome_plano'] == plano_escolhido['nome_plano']) &
        (todos_produtos['tipo_contrato'].str.lower() == tipo_contrato_cliente)
    ]

    if tipo_contrato_cliente == "pj":
        formas_filtradas = formas_disponiveis[
            (formas_disponiveis['forma_pagamento'].str.contains("boleto", case=False, na=False)) &
            (formas_disponiveis['forma_pagamento'].str.contains("mensal", case=False, na=False))
        ]

        if formas_filtradas.empty:
            formas_filtradas = formas_disponiveis[
                formas_disponiveis['forma_pagamento'].str.contains("boleto", case=False, na=False)
            ]

        if formas_filtradas.empty:
            return [{"mensagem": "Não encontramos opção de boleto para este plano PJ."}]

        forma = formas_filtradas.iloc[0]
        preco = forma["preco"]
        carencia = forma["carencia"]

        mensagem_whatsapp = (
            f"🎯 *Plano Recomendado:* {plano_escolhido['nome_plano'].title()} – {plano_escolhido['operadora']}\n\n"
            f"✅ *Forma de pagamento:* {forma['forma_pagamento']}\n"
            f"💰 Preço por pessoa: R$ {preco:.2f}\n"
            f"💳 Preço total (para {quantidade_vidas} pessoas): R$ {preco * quantidade_vidas:.2f}\n"
            f"🕑 Carência: {carencia}"
        )

        if mensagem_especial:
            mensagem_whatsapp = f"{mensagem_especial}\n\n{mensagem_whatsapp}"

        mensagem_whatsapp = adicionar_mensagem_transbordo(mensagem_whatsapp, cobertura_reconhecida)

        return [{
            "plano_recomendado": plano_escolhido['nome_plano'].title(),
            "preco_por_pessoa": f'R$ {preco:.2f}',
            "preco_total": f'R$ {preco * quantidade_vidas:.2f}',
            "quantidade_vidas": quantidade_vidas,
            "forma_pagamento": forma["forma_pagamento"],
            "carências": carencia,
            "mensagem_whatsapp": mensagem_whatsapp.strip()
        }]

    elif tipo_contrato_cliente == "pf":
        agrupado = {}
        for _, forma in formas_disponiveis.iterrows():
            preco = forma["preco"]
            carencia = forma["carencia"]
            forma_nome = forma["forma_pagamento"]
            if carencia not in agrupado:
                agrupado[carencia] = {
                    "formas_pagamento": [],
                    "preco": preco,
                    "carencia_texto": carencia
                }
            agrupado[carencia]["formas_pagamento"].append(forma_nome)

        mensagem_whatsapp = (
            f"🎯 *Plano Recomendado:* {plano_escolhido['nome_plano'].title()} – {plano_escolhido['operadora']}\n\n"
            f"O preço e as carências variam de acordo com a forma de pagamento:\n\n"
        )
        for group in agrupado.values():
            formas_texto = " ou ".join(group["formas_pagamento"])
            mensagem_whatsapp += (f"✅ *{formas_texto}:*\n"
                                f"💰 Preço por pessoa: R$ {group['preco']:.2f}\n"
                                f"💳 Preço total (para {quantidade_vidas} pessoas): R$ {group['preco'] * quantidade_vidas:.2f}\n"
                                f"🕑 Carência: {group['carencia_texto']}\n\n")

        if mensagem_especial:
            mensagem_whatsapp = f"{mensagem_especial}\n\n{mensagem_whatsapp}"

        mensagem_whatsapp = adicionar_mensagem_transbordo(mensagem_whatsapp, cobertura_reconhecida)

        return [{
            "plano_recomendado": plano_escolhido['nome_plano'].title(),
            "quantidade_vidas": quantidade_vidas,
            "precos_carencias": [{
                "formas_pagamento": group["formas_pagamento"],
                "preco_por_pessoa": f'R$ {group["preco"]:.2f}',
                "preco_total": f'R$ {group["preco"] * quantidade_vidas:.2f}',
                "carencias": group["carencia_texto"]
            } for group in agrupado.values()],
            "mensagem_whatsapp": mensagem_whatsapp.strip()
        }]

