from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import pandas as pd
from cotador_agent import cotador_agent

app = FastAPI()

# Carrega a base de produtos da Amil
produtos_amil = pd.read_csv("produtos_amil.csv", sep=";", encoding="utf-8")

@app.post("/cotar")
async def cotar(request: Request):
    input_usuario = await request.json()

    try:
        resultado = cotador_agent(input_usuario, produtos_amil)
        return JSONResponse(content={"resultado": resultado})
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)
