import os
from typing import Optional

print("=== DEBUG START ===")
print("Arquivos disponíveis na pasta:", os.listdir('.'))
print("PORT recebida do ambiente:", os.getenv("PORT"))
print("=== DEBUG END ===")

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from cotador_agent import cotador_agent

# Carregar os arquivos CSV
todos_produtos = pd.read_csv('todos_produtos_em_tabela.csv', sep=';')

# Iniciar o app FastAPI
app = FastAPI()

# Definição do modelo de input
class InputUsuario(BaseModel):
    tipo_contrato: str
    problemas_dores: str               # Agora como string!
    quantidade_vidas: str              # Continua string!
    operadora_preferida: Optional[str] = None  # ✅ Campo novo

@app.post("/cotar")
async def cotar(input_usuario: InputUsuario):
    # Conversão segura de quantidade_vidas para inteiro
    try:
        quantidade_vidas = int(input_usuario.quantidade_vidas)
        if quantidade_vidas < 1:
            raise ValueError
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="O campo 'quantidade_vidas' deve ser um número inteiro maior que zero (ex.: 2)."
        )

    # Conversão de problemas_dores (string separada por vírgula) para lista
    problemas_dores_list = [
        p.strip() for p in input_usuario.problemas_dores.split(",") if p.strip()
    ]

    if not problemas_dores_list:
        raise HTTPException(
            status_code=400,
            detail="O campo 'problemas_dores' não pode ser vazio. Informe pelo menos um problema ou dor."
        )

    # Montar o input ajustado com os dados convertidos
    input_dict = {
        "tipo_contrato": input_usuario.tipo_contrato,
        "problemas_dores": problemas_dores_list,
        "quantidade_vidas": quantidade_vidas,
        "operadora_preferida": input_usuario.operadora_preferida
    }

    # Chamar o cotador
    resultado = cotador_agent(
        input_dict,
        todos_produtos
    )
    return {"resultado": resultado}
