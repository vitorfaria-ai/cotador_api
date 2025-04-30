import pandas as pd
import unicodedata
import re

def normalizar_texto(texto):
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = texto.lower().strip()
    texto = re.sub(r'\b(s|es|is|os|as)\b', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def comparar_termos(problema, termo):
    return termo in problema or problema in termo

correlacoes = {
    "clareamento": {"plano_dedicado": "E50", "mensagem": "Clareamento exige um plano com cobertura estética."},
    "prótese": {"plano_dedicado": "E60", "mensagem": "Próteses exigem plano com cobertura estética adequada."},
    "resina": {"plano_dedicado": "E90", "mensagem": "Próteses estéticas como resina ou cerâmica precisam de plano estético."},
    "cerâmica": {"plano_dedicado": "E90"},
    "aparelho": {"plano_dedicado": "E80", "mensagem": "Aparelho ortodôntico exige plano com ortodontia."},
    "ortodontia": {"plano_dedicado": "E80"},
    "invisalign": {"plano_dedicado": "E80", "mensagem": "Este plano não cobre Invisalign, mas cobre aparelho tradicional."},
    "implante": {"mensagem": "Nenhum plano cobre implante dentário, mas o plano que mais se aproxima da cobertura é o E90 Estético!", "plano_dedicado": "Dental E90"},
    "criança": {"plano_dedicado": "Dental K25 - Linha Kids", "mensagem": "Plano Kids exclusivo para crianças até 13 anos e 11 meses."}
}

def cotador_agent(input_usuario, produtos):
    tipo_contrato = input_usuario.get("tipo_contrato", "").strip().lower()
    quantidade_vidas = int(input_usuario.get("quantidade_vidas", 1))
    problemas_dores = input_usuario.get("problemas_dores", "")
    operadora_preferida = input_usuario.get("operadora_preferida", "amil").lower()

    dores_lista = [normalizar_texto(p) for p in problemas_dores.split(",") if p.strip()]
    
    plano_forcado = None
    mensagem_especial = None

    for problema in dores_lista:
        for termo, regra in correlacoes.items():
            if comparar_termos(problema, termo):
                plano_forcado = regra.get("plano_dedicado")
                mensagem_especial = regra.get("mensagem")
                break
        if plano_forcado:
            break

    produtos_filtrados = produtos[produtos['tipo_contrato'].str.lower().str.strip() == tipo_contrato]

    if plano_forcado:
        candidatos = produtos_filtrados[
            produtos_filtrados['nome_plano'].str.lower().str.contains(plano_forcado.lower())
        ]
        if candidatos.empty:
            return [{"mensagem": f"Não encontramos o plano especial {plano_forcado} para o tipo de contrato {tipo_contrato}."}]
        plano_escolhido = candidatos.sort_values(by="preco").iloc[0]
    else:
        candidatos = produtos_filtrados[
            produtos_filtrados['nome_plano'].str.contains("205", case=False, na=False)
        ]
        if candidatos.empty:
            return [{"mensagem": "Não encontramos o plano padrão Dental 205."}]
        plano_escolhido = candidatos.sort_values(by="preco").iloc[0]

    plano_nome = plano_escolhido['nome_plano']
    operadora = plano_escolhido['operadora']
    plano_id = plano_escolhido['id']

    formas = produtos[produtos['id'] == plano_id]

    if tipo_contrato == "pj":
        formas_filtradas = formas[
            (formas["forma_pagamento"].str.contains("boleto", case=False, na=False)) &
            (formas["forma_pagamento"].str.contains("mensal", case=False, na=False))
        ]

        if formas_filtradas.empty:
            formas_filtradas = formas[formas["forma_pagamento"].str.contains("boleto", case=False, na=False)]

        if formas_filtradas.empty:
            return [{"mensagem": "Não encontramos opção de boleto para este plano PJ."}]

        forma = formas_filtradas.iloc[0]
        preco = forma["preco"]
        carencia = forma["carencia"]
        forma_nome = forma["forma_pagamento"]

        mensagem_whatsapp = (f"🎯 *Plano Recomendado:* {plano_nome} – {operadora}\n\n"
                             f"✅ *Forma de pagamento:* {forma_nome}\n"
                             f"💰 Preço por pessoa: R$ {preco:.2f}\n"
                             f"💳 Preço total (para {quantidade_vidas} pessoas): R$ {preco * quantidade_vidas:.2f}\n"
                             f"🕑 Carência: {carencia}")

        if mensagem_especial:
            mensagem_whatsapp = f"{mensagem_especial}\n\n{mensagem_whatsapp}"

        return [{
            "plano_recomendado": plano_nome,
            "preco_por_pessoa": f"R$ {preco:.2f}",
            "preco_total": f"R$ {preco * quantidade_vidas:.2f}",
            "quantidade_vidas": quantidade_vidas,
            "forma_pagamento": forma_nome,
            "carências": carencia,
            "mensagem_whatsapp": mensagem_whatsapp.strip()
        }]

    else:
        agrupado = {}
        for _, forma in formas.iterrows():
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

        mensagem_whatsapp = f"🎯 *Plano Recomendado:* {plano_nome} – {operadora}\nO preço e as carências variam de acordo com a forma de pagamento:\n\n"
        for group in agrupado.values():
            formas_texto = " ou ".join(group["formas_pagamento"])
            mensagem_whatsapp += (f"✅ *{formas_texto}:*\n"
                                  f"💰 Preço por pessoa: R$ {group['preco']:.2f}\n"
                                  f"💳 Preço total (para {quantidade_vidas} pessoas): R$ {group['preco'] * quantidade_vidas:.2f}\n"
                                  f"🕑 Carência: {group['carencia_texto']}\n\n")

        if mensagem_especial:
            mensagem_whatsapp = f"{mensagem_especial}\n\n{mensagem_whatsapp}"

        return [{
            "plano_recomendado": plano_nome,
            "quantidade_vidas": quantidade_vidas,
            "precos_carencias": [  # múltiplas opções para PF
                {
                    "formas_pagamento": group["formas_pagamento"],
                    "preco_por_pessoa": f"R$ {group['preco']:.2f}",
                    "preco_total": f"R$ {group['preco'] * quantidade_vidas:.2f}",
                    "carencias": group["carencia_texto"]
                }
                for group in agrupado.values()
            ],
            "mensagem_whatsapp": mensagem_whatsapp.strip()
        }]
