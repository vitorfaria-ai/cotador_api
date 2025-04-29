import pandas as pd

# Carrega o CSV uma única vez no início
todos_produtos = pd.read_csv('todos_produtos_em_tabela.csv', sep=';')

# Coberturas básicas garantidas em todos os planos
coberturas_basicas = [
    "urgência", "emergência", "consulta", "limpeza", "profilaxia", "flúor",
    "raio x", "radiografia", "panorâmico", "periapical", 
    "gengiva", "periodontia",
    "canal", "endodontia",
    "odontopediatria",
    "restauração", "dentística",
    "cirurgia", "extração", "siso", 
    "prótese rol",  
    "documentação ortodôntica básica"
]

# Prioridade das operadoras
prioridade_operadoras = ["Amil", "Hapvida", "Bradesco", "Odontoprev"]

# Correlações específicas de dores
correlacoes = {
    "implante": {"mensagem": "Nenhum plano cobre implante dentário. Mas muitos clientes nessa situação optam pelo Dental E90, que é o plano de próteses mais completo do Brasil.", "plano_dedicado": "Dental E90"},
    "protocolo": {"mensagem": "Nenhum plano cobre protocolo dentário. Mas muitos clientes nessa situação optam pelo Dental E90, que é o plano de próteses mais completo do Brasil.", "plano_dedicado": "Dental E90"},
    "coroa de cerâmica": {"mensagem": "Para 'coroa de cerâmica', recomendamos planos com cobertura estética como o E90, Premium Top ou Master.", "plano_dedicado": "Dental E90"},
    "inlay": {"mensagem": "Para 'inlay', recomendamos planos com cobertura estética como o E90, Premium Top ou Master.", "plano_dedicado": "Dental E90"},
    "onlay": {"mensagem": "Para 'onlay', recomendamos planos com cobertura estética como o E90, Premium Top ou Master.", "plano_dedicado": "Dental E90"},
    "ponte móvel": {"mensagem": "Para 'ponte móvel', recomendamos o plano E60 ou superiores.", "plano_dedicado": "Dental E60"},
    "dentadura": {"mensagem": "Para 'dentadura', recomendamos o plano E60 ou superiores.", "plano_dedicado": "Dental E60"},
    "clareamento": {"mensagem": "Para clareamento, recomendamos o plano Dental E50 Clareamento.", "plano_dedicado": "Dental E50 Clareamento"},
    "aparelho": {"mensagem": "Para aparelho ortodôntico, recomendamos o plano Dental E80 Ortodontia.", "plano_dedicado": "Dental E80 Ortodontia"},
    "plano infantil": {"mensagem": "Para crianças, recomendamos o plano Dental K25 Linha Kids.", "plano_dedicado": "Dental K25 Linha Kids"}
}

# Função principal do agente cotador
def cotador_agent(input_usuario, todos_produtos):
    tipo_contrato = input_usuario["tipo_contrato"]
    problemas_dores = input_usuario["problemas_dores"]
    operadora_preferida = input_usuario.get("operadora_preferida")

    # Tratamento especial para MEI como PJ
    if tipo_contrato == "mei":
        tipo_contrato = "pj"

    # Primeiro verifica se há alguma dor específica nas correlações
    for dor in problemas_dores:
        dor_lower = dor.lower()
        if dor_lower in correlacoes:
            correlacao = correlacoes[dor_lower]
            df_plano = todos_produtos[todos_produtos["nome_plano"].str.contains(correlacao["plano_dedicado"], case=False)]
            if not df_plano.empty:
                melhor_plano = df_plano.iloc[0]
                return montar_resposta(melhor_plano, correlacao["mensagem"])

    # Verifica se o cliente mencionou operadora preferida
    operadoras_busca = [operadora_preferida] if operadora_preferida else prioridade_operadoras

    for operadora in operadoras_busca:
        df_operadora = todos_produtos[todos_produtos["operadora"] == operadora]
        if not df_operadora.empty:
            if operadora == "Amil":
                df_205 = df_operadora[df_operadora["nome_plano"].str.contains("205", case=False)]
                if not df_205.empty:
                    melhor_plano = df_205.iloc[0]
                    return montar_resposta(melhor_plano)
            melhor_plano = df_operadora.iloc[0]
            return montar_resposta(melhor_plano)

    # Caso nenhuma opção sólida encontrada, sugere especialista humano
    return "Sugiro falar com um especialista humano para mais detalhes e melhor atendimento."

# Função auxiliar para montar resposta
def montar_resposta(plano, mensagem_extra=""):
    resposta = {
        "operadora": plano["operadora"],
        "plano": plano["nome_plano"],
        "preco": plano["preco"],
        "detalhes": plano["descricao"],
        "mensagem_extra": mensagem_extra
    }
    return resposta
