import pandas as pd

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
        "implante": {"mensagem": "Nenhum plano cobre implante dentário.", "plano_dedicado": "Dental E90"},
    }

    resposta_especial = []
    planos_filtrados = planos[planos["tipo_contrato"] == tipo_contrato]
    planos_com_beneficios = planos_filtrados.merge(beneficios, left_on="id", right_on="plano_id").drop_duplicates(subset=["id"])
    filtro = pd.Series([True] * len(planos_com_beneficios))
    plano_forcado = None

    for problema in problemas_dores:
        problema_lower = problema.lower()
        for termo, regra in correlacoes.items():
            if termo in problema_lower:
                if "plano_dedicado" in regra:
                    plano_forcado = regra["plano_dedicado"]
                if "mensagem" in regra:
                    resposta_especial.append({"mensagem": regra["mensagem"]})

    if plano_forcado:
        plano_escolhido = planos[planos["nome"].str.contains(plano_forcado, case=False)].iloc[0]
    else:
        planos_filtrados = planos[planos["tipo_contrato"] == tipo_contrato]  # ⚠️ Aqui filtra só pelo tipo de contrato
        if operadora_preferida:
            planos_filtrados = planos_filtrados[
                planos_filtrados["operadora"].str.contains(operadora_preferida, case=False, na=False)
            ]
            if planos_filtrados.empty:
                # Se não achou a operadora preferida, volta a olhar todos (sem a preferência)
                planos_filtrados = planos[planos["tipo_contrato"] == tipo_contrato]

        # Só agora aplica os benefícios e prioridades
        planos_com_beneficios = planos_filtrados.merge(beneficios, left_on="id", right_on="plano_id").drop_duplicates(subset=["id"])
        planos_com_prioridade = planos_com_beneficios.merge(regras_operadora[["operadora", "prioridade"]], on="operadora").sort_values(by="prioridade")
        plano_escolhido = planos_com_prioridade.iloc[0]

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
        return [{
            "plano_recomendado": plano_escolhido["nome"],
            "preco_por_pessoa": f'R$ {preco:.2f}',
            "preco_total": f'R$ {preco * quantidade_vidas:.2f}',
            "quantidade_vidas": quantidade_vidas,
            "forma_pagamento": forma["forma"],
            "carências": forma["carencia"],
            "mensagem_whatsapp": mensagem_whatsapp
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
