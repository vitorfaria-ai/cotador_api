import os

print("=== DEBUG START ===")
print("Arquivos disponíveis na pasta:", os.listdir('.'))
print("PORT recebida do ambiente:", os.getenv("PORT"))
print("=== DEBUG END ===")

from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from cotador_agent import cotador_agent

planos = pd.read_csv("planos.csv")
beneficios = pd.read_csv("beneficios_planos.csv")
formas_pagamento = pd.read_csv("formas_pagamento.csv")
regras_operadora = pd.read_csv("regras_operadora.csv")

app = FastAPI()

class InputUsuario(BaseModel):
    tipo_contrato: str
    problemas_dores: list[str]
    quantidade_vidas: int

@app.post("/cotar")
async def cotar(input_usuario: InputUsuario):
    resultado = cotador_agent(
        input_usuario.dict(),
        planos,
        beneficios,
        formas_pagamento,
        regras_operadora
    )
    return {"resultado": resultado}
