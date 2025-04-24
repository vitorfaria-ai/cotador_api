import os

print("=== DEBUG START ===")
print("Arquivos disponíveis na pasta:", os.listdir('.'))
print("PORT recebida do ambiente:", os.getenv("PORT"))
print("=== DEBUG END ===")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from cotador_agent import cotador_agent

# Carregar os arquivos CSV
planos = pd.read_csv("planos.csv")
beneficios = pd.read_csv("beneficios_planos.csv")
formas_pagamento = pd.read_csv("formas_pagamento.csv")
regras_operadora = pd.read_csv("regras_operadora.csv")

# Iniciar o app FastAPI
app = FastAPI()

# Definição do modelo de input
class InputUsuario(BaseModel):
    tipo_contrato: str
    problemas_dores: list[str]
    quantidade_vidas: str  # Agora como string para receber "2", "3", etc.

@app.post("/cotar")
async def cotar(input_usuario: InputUsuario):
    # Tentar converter quantidade_vidas para int
    try:
        quantidade_vidas = int(input_usuario.quantidade_vidas)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="O campo 'quantidade_vidas' deve ser um número (ex.: 2), mesmo que venha como string."
        )

    # Montar o input ajustado com a quantidade convertida
    input_dict = input_usuario.dict()
    input_dict["quantidade_vidas"] = quantidade_vidas  # Sobrescreve no dicionário

    # Chamar o cotador
    resultado = cotador_agent(
        input_dict,
        planos,
        beneficios,
        formas_pagamento,
        regras_operadora
    )
    return {"resultado": resultado}
