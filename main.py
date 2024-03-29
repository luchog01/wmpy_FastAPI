from fastapi import FastAPI, Request, WebSocket,BackgroundTasks
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


import asyncio
from time import sleep
import numpy as np
from numpy import random
import uvicorn
from typing import List
import time
from fastapi import FastAPI
from fastapi_mail import FastMail, MessageSchema
from uuid import uuid4
import sqlalchemy
from sqlalchemy import text

from Curvas import crearCsvBadlar, crearCsvCer, crearCsvHardDolar, crearCsvOn
from Curvas import onlineBadlar, onlineCer, onlineDolar, onlineOn
from Models import ValidationIn, Validation, EmailSchema, User
from settings import confMail, host_url
import myDatabase

# Instancias
#-------------------------------------------------------------------

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

database, validation_table, user_table = myDatabase.main()

#--------------------------------------------------------------------
#Configuraciones y Servicios
#--------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


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


@app.get("/signup", response_class=HTMLResponse)
def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup", response_class=HTMLResponse)
async def signup(request: Request, emailSCH: EmailSchema) -> HTMLResponse:

    token = str(uuid4())
    fileHtml = open('templates/acc_active_email.html', 'r')

    message = MessageSchema(
        subject="Fastapi-Mail module",
        recipients=emailSCH.dict().get("email"),  # List of recipients, as many as you can pass 
        body=fileHtml.read().format(
            username=emailSCH.dict().get("user"),
            domain=host_url,
            tokenDomain=token
        ),
        subtype="html"
        )

    query = validation_table.select()
    data = await database.fetch_all(query)

    print(data)
    aux=0

    if data!=[]:
        for item in data:
            if emailSCH.dict().get("email")[0] in item:  #Si el email ingresado ya existe actualiza el token
                aux=0
                # Actualiza el item TOKEN del usuario al que se desea re-signear
                query = validation_table.update().where(sqlalchemy.sql.column('email') == emailSCH.dict().get("email")[0]).values(token=str(token), timestamp=time.ctime())                                                                                   
                break
            elif emailSCH.dict().get("email")[0] not in item:
                aux=1

    # Si no existe el mail o la DB esta vacía, agrega el nuevo usuario con toda su data + token + timestamp
    if aux==1 or data==[]:
        query = validation_table.insert().values(email=emailSCH.dict().get("email")[0],
                                                    token=str(token),
                                                    timestamp=time.ctime(),
                                                    username=emailSCH.dict().get("user"),
                                                    password=emailSCH.dict().get("password"))
            

    await database.execute(query)

    fm = FastMail(confMail)
    await fm.send_message(message)
    return templates.TemplateResponse("message.html", {"request": request})


@app.get("/validar/{tokenDomain}")
async def validar(request: Request, tokenDomain: str):
    print(tokenDomain)

    if tokenDomain == validation_table.select(sqlalchemy.sql.column('token')):
        print("TE LOGEASTE PETE BIEN AHI")

        query = user_table.insert().values(email=validation_table.select(sqlalchemy.sql.column('email')).where(sqlalchemy.sql.column('token')==tokenDomain),
                                            username=validation_table.select(sqlalchemy.sql.column('username')).where(sqlalchemy.sql.column('token')==tokenDomain),
                                            password=validation_table.select(sqlalchemy.sql.column('password')).where(sqlalchemy.sql.column('token')==tokenDomain))


    # query = validation_table.select()
    # data = await database.fetch_all(query)
    # for item in data[::-1]:
    #     if item[2] == tokenDomain:
    #         print("Mail aceptado",item[1])
    #         break



    #borrar de la tabla de validar al final de la funcion y añadir a users
    return {"TOKEN":tokenDomain}


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


@app.get("/notes/", response_model=List[Validation])
async def read_notes():
    query = validation_table.select()
    return await database.fetch_all(query)


@app.post("/notes/", response_model=Validation)
async def create_note(validate: ValidationIn):
    query = validation_table.insert().values(email=validate.email, token=validate.token)
    last_record_id = await database.execute(query)
    return {**validate.dict(), "id": last_record_id}


@app.post("/login", )
async def login():
    pass


# EJEMPLO DE TEMPLATES Y STATICS

@app.get("/test/{msg}")
async def test(request: Request, msg: str):
    return {"msg":msg}

#--------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)