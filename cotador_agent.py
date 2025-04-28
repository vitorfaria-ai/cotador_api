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

def cotador_agent(input_usuario, planos, beneficios, formas_pagamento, regras_operadora):
    tipo_contrato = input_usuario["tipo_contrato"]
    problemas_dores = input_usuario["problemas_dores"]
    quantidade_vidas = input_usuario.get("quantidade_vidas", 1)
    operadora_preferida = input_usuario.get("operadora_preferida")

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
        # Primeiro filtra tipo_contrato e operadora preferida
        planos_filtrados = planos[planos["tipo_contrato"] == tipo_contrato]
        if operadora_preferida:
            planos_operadora = planos_filtrados[planos_filtrados["operadora"].str.contains(operadora_preferida, case=False, na=False)]
            if not planos_operadora.empty:
                planos_filtrados = planos_operadora

        # Depois aplica os benefícios e prioridades
        planos_com_beneficios = planos_filtrados.merge(beneficios, left_on="id", right_on="plano_id").drop_duplicates(subset=["id"])
        planos_com_prioridade = planos_com_beneficios.merge(regras_operadora[["operadora", "prioridade"]], on="operadora").sort_values(by="prioridade")
        plano_escolhido = planos_com_prioridade.iloc[0]

    # Verificação sensível para coberturas desconhecidas
    cobertura_reconhecida = True
    for problema in problemas_dores:
        cobertura_encontrada = any(comparar_termos(problema, termo) for termo in correlacoes)
        if not cobertura_encontrada:
            cobertura_reconhecida = False
            break  # ✅ Para o loop assim que encontrar a primeira dor desconhecida

    formas = formas_pagamento[formas_pagamento["plano_id"] == plano_escolhido["id"]]

    if tipo_contrato == "pj":
        formas_filtradas = formas[formas["forma"].str.contains("boleto", case=False, na=False)]
        if formas_filtradas.empty:
            return [{"mensagem": "Não encontramos opção de boleto para este plano PJ."}]
        forma = formas_filtradas.iloc[0]
        preco = forma["preco"]
        mensagem_whatsapp = (f"🎯 *Plano Recomendado:* {plano_escolhido['nome']}\n\n"
                             f"✅ *Forma de pagamento:* {forma['forma']}\n"
                             f"💰 Preço por pessoa: R$ {preco:.2f}\n"
                             f"💳 Preço total (para {quantidade_vidas} pessoas): R$ {preco * quantidade_vidas:.2f}\n"
                             f"🕑 Carência: {forma['carencia']}")

        # ADICIONE AQUI também a verificação sensível:
        if not cobertura_reconhecida:
            mensagem_whatsapp = (f"O plano básico da operadora que pediu é o que segue abaixo, "
                                f"mas é ideal que eu te conecte com um especialista para ele te passar todos os detalhes "
                                f"se este plano cobre sua necessidade específica. Assim você pode ter a melhor experiência. O que você acha? 😊\n\n"
                                f"{mensagem_whatsapp}")
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

        # Se cobertura não reconhecida, monta mensagem especial:
        if not cobertura_reconhecida:
            mensagem_whatsapp = (f"O plano básico da operadora que pediu é o que segue abaixo, "
                                f"mas é ideal que eu te conecte com um especialista para ele te passar todos os detalhes "
                                f"se este plano cobre sua necessidade específica. Assim você pode ter a melhor experiência. O que você acha? 😊\n\n"
                                f"{mensagem_whatsapp}")  # Mensagem padrão já montada anteriormente

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
