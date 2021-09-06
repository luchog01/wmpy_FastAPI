from fastapi import FastAPI, Request, WebSocket,BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse


import asyncio
from time import sleep
import numpy as np
from numpy import random
import uvicorn

from Curvas import crearCsvBadlar, crearCsvCer, crearCsvHardDolar, crearCsvOn
from Curvas import onlineBadlar, onlineCer, onlineDolar, onlineOn
from funciones import api_curva_online as api_curva

# Instancias
#-------------------------------------------------------------------

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


#--------------------------------------------------------------------

#Configuraciones y Servicios
#--------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


# @app.on_event("startup")
# def startup():
#     api_curva.main()

def add_log(log):
    with open('log.txt', 'a') as f:
        f.write("{}\n".format(log))
        f.close()

@app.get("/status")
async def status():
    json ={}
    json["Server Operating"] = True
    return json
#--------------------------------------------------------------------

# Views
#--------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/panel", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("panel.html", {"request": request})


@app.get("/contador")
async def contador():
    i=0
    while i < 30:
        await asyncio.sleep(1)
        print(i)
        i+=1
    return {"message": "Termino Contador"}
    

@app.get("/pyhomebroker")
def api_curvas():
    while True:
        print("ACTIALIZA CURVA EN MAIN")
        #api_curva.main()
        sleep(5)


@app.post("/getDatosCurvas")
def curvas():
    dic={}
    lista=[]
    lista.append(onlineBadlar.iniciarTabla())
    lista.append(onlineCer.iniciarTabla())
    lista.append(onlineDolar.iniciarTabla())
    lista.append(onlineOn.iniciarTabla())
    dic["Graficos"] = lista
    return dic


@app.get("/actualizar")
def actualizar():
    dic={}
    dic["Status Badlar"] = crearCsvBadlar.main()
    dic["Status Cer"] = crearCsvCer.main()
    dic["Status Dolar"] = crearCsvHardDolar.main()
    dic["Status On"] = crearCsvOn.main()
    return dic

#--------------------------------------------------------------------
# ZONA DE PRUEBAS
#--------------------------------------------------------------------
# async def fake_video_streamer():
#     for i in range(10):
#         aux = random.randint(1, 100)
#         aux = str(aux)
#         yield aux+"\n"


# @app.get("/test")
# async def test():
#     return StreamingResponse(fake_video_streamer())


# EJEMPLO DE TEMPLATES Y STATICS

@app.get("/test/{msg}")
async def test(request: Request, msg: str):
    return {"msg":msg}

#--------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)