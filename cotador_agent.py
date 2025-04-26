import pandas as pd

def cotador_agent(input_usuario, planos, beneficios, formas_pagamento, regras_operadora):
    tipo_contrato = input_usuario["tipo_contrato"]
    problemas_dores = input_usuario["problemas_dores"]
    quantidade_vidas = input_usuario.get("quantidade_vidas", 1)

    # 🚩 Conversão segura de quantidade_vidas para inteiro e validação de positivo
    try:
        quantidade_vidas = int(quantidade_vidas)
        if quantidade_vidas < 1:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("O campo 'quantidade_vidas' precisa ser um número inteiro maior que zero (ex.: 2). Mesmo que venha como string, ele deve ser numérico.")

    # 🚩 Conversão segura de problemas_dores para lista, mesmo que venha como string
    if isinstance(problemas_dores, str):
        problemas_dores = [p.strip() for p in problemas_dores.split(",") if p.strip()]

    if not problemas_dores:
        raise ValueError("O campo 'problemas_dores' não pode ser vazio. Informe pelo menos um problema ou dor.")

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
    problemas_utilizados = []
    problemas_cobertos = []
    explicacoes_justificativa = []

    planos_filtrados = planos[planos["tipo_contrato"] == tipo_contrato]
    planos_com_beneficios = planos_filtrados.merge(
        beneficios, left_on="id", right_on="plano_id", suffixes=('', '_beneficio')
    ).drop_duplicates(subset=["id"])

    filtro = pd.Series([True] * len(planos_com_beneficios))
    plano_forcado = None

    for problema in problemas_dores:
        problema_lower = problema.lower()
        aplicado = False

        for termo, regra in correlacoes.items():
            if termo in problema_lower:
                if "plano_dedicado" in regra:
                    plano_forcado = regra["plano_dedicado"]
                if "cobertura_associada" in regra:
                    filtro &= planos_com_beneficios[regra["cobertura_associada"]]
                    if regra.get("relacionado", False):
                        problemas_utilizados.append(problema)
                        explicacoes_justificativa.append(f"Para '{problema}', o plano não cobre diretamente, mas é o mais próximo disponível.")
                if "mensagem" in regra:
                    resposta_especial.append({"mensagem": regra["mensagem"]})
                aplicado = True
                break

        if not aplicado:
            problemas_utilizados.append(problema)
            if any(p in problema_lower for p in ["ortodontia", "aparelho", "manutenção"]):
                filtro &= planos_com_beneficios["tem_ortodontia"]
                problemas_cobertos.append(problema)
                explicacoes_justificativa.append(f"Para '{problema}', o plano cobre ortodontia.")
            if any(p in problema_lower for p in ["clareamento", "estética", "estetica", "branco"]):
                filtro &= planos_com_beneficios["tem_clareamento"]
                problemas_cobertos.append(problema)
                explicacoes_justificativa.append(f"Para '{problema}', o plano cobre clareamento.")
            if any(p in problema_lower for p in ["prótese", "protese"]):
                filtro &= planos_com_beneficios["tem_protese_rol"]
                problemas_cobertos.append(problema)
                explicacoes_justificativa.append(f"Para '{problema}', o plano cobre prótese do rol.")
            if any(p in problema_lower for p in ["urgência", "emergência", "dor"]):
                filtro &= planos_com_beneficios["tem_urgencia_24h"]
                problemas_cobertos.append(problema)
                explicacoes_justificativa.append(f"Para '{problema}', o plano cobre urgência 24h.")

    planos_filtrados_por_dor = planos_com_beneficios[filtro]

    if plano_forcado:
        plano_forcado_df = planos[
            planos["nome"].str.contains(plano_forcado, case=False, na=False) &
            (planos["tipo_contrato"] == tipo_contrato)
        ]
        if not plano_forcado_df.empty:
            plano_escolhido = plano_forcado_df.iloc[0]
            formas = formas_pagamento[formas_pagamento["plano_id"] == plano_escolhido["id"]]
        else:
            return [{"mensagem": f"Plano '{plano_forcado}' não encontrado para contrato {tipo_contrato}."}]
    elif planos_filtrados_por_dor.empty:
        plano_dental_205 = planos[
            (planos["nome"].str.contains("Dental 205", case=False, na=False)) &
            (planos["tipo_contrato"] == tipo_contrato)
        ].iloc[0]
        formas = formas_pagamento[formas_pagamento["plano_id"] == plano_dental_205["id"]]
        return [
            {
                "plano_recomendado": plano_dental_205["nome"],
                "preco_por_pessoa": f'R$ {forma["preco"]:.2f}' if "preco" in forma and pd.notnull(forma["preco"]) else "Preço não disponível",
                "preco_total": f'R$ {forma["preco"] * quantidade_vidas:.2f}' if "preco" in forma and pd.notnull(forma["preco"]) else "Preço não disponível",
                "quantidade_vidas": quantidade_vidas,
                "forma_pagamento": forma.get("forma", "Não informado"),
                "carências": forma.get("carencia", "Não informado"),
                "justificativa": "Nenhum plano cobre exatamente o que o cliente buscou, mas o Dental 205 é um plano básico com excelente custo-benefício."
            }
            for _, forma in formas.iterrows()
        ] + resposta_especial
    else:
        planos_com_prioridade = planos_filtrados_por_dor.merge(
            regras_operadora[["operadora", "prioridade"]],
            on="operadora",
            how="left"
        ).sort_values(by="prioridade")
        plano_escolhido = planos_com_prioridade.iloc[0]
        formas = formas_pagamento[formas_pagamento["plano_id"] == plano_escolhido["id"]]

    agrupado = {}
    for _, forma in formas.iterrows():
        preco = forma["preco"] if "preco" in forma and pd.notnull(forma["preco"]) else 0
        carencia = forma.get("carencia", "Não informado")
        forma_nome = forma.get("forma", "Não informado")

        if carencia not in agrupado:
            agrupado[carencia] = {
                "formas_pagamento": [],
                "carencia_texto": carencia
            }
        agrupado[carencia]["formas_pagamento"].append(forma_nome)

    saida_final = [{
        "plano_recomendado": plano_escolhido["nome"],
        "preco_por_pessoa": f'R$ {preco:.2f}' if preco else "Preço não disponível",
        "preco_total": f'R$ {preco * quantidade_vidas:.2f}' if preco else "Preço não disponível",
        "quantidade_vidas": quantidade_vidas,
        "carencias_por_forma_pagamento": [
            {
                "formas_pagamento": formas_group["formas_pagamento"],
                "carencias": formas_group["carencia_texto"]
            } for formas_group in agrupado.values()
        ],
        "justificativa": " ".join(explicacoes_justificativa) or "Este plano é recomendado com base nas necessidades informadas."
    }]

    return saida_final + resposta_especial
