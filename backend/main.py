# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, Cookie, Response, status
from typing import Optional
from fastapi.responses import JSONResponse
import hashlib
import sqlite3
import platform
import time, secrets
import os

app = FastAPI()

DB_VERSION = 1
PROOF_DIFFICULTY = "0000"
MAX_AGE_SECONDS = 600
SECRET_SALT = "BigfishForCat"

users = []

import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI

DB_VERSION = 1
PROOF_DIFFICULTY = "0000"
MAX_AGE_SECONDS = 600
SECRET_SALT = "BigfishForCat"
Db_PATH = "/app/data/AppData.db"
users = []

if platform.system() == "Windows": 
    Db_PATH = "./../data/AppData.db"

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("ЗАПУСК")
    if not os.path.isfile(Db_PATH):
        print(f"Создание файла БД")

    app.state.db = sqlite3.connect(Db_PATH)
    db = app.state.db
    
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS version (version INT);")
    row = cursor.execute("SELECT version FROM version;").fetchone()

    if row is None:
        print(f"Создание БД")
        cursor.execute("INSERT INTO version VALUES (0)")
        db.commit()
        row = [0]

    db_vers = row[0]
    if DB_VERSION < db_vers:
        print(f"Ошибка: Версия БД ({db_vers}) новее, чем версия программы ({DB_VERSION})")
        raise Exception("DB version mismatch")
    
    elif DB_VERSION > db_vers:
        print(f"Обновление БД ({db_vers}) --> ({DB_VERSION})")

        from initDB import initDBsql
        
        cursor.executescript(initDBsql)

        cursor.execute("UPDATE version SET version=?", (DB_VERSION,))
        db.commit()

    yield

    print("ОСТАНОВКА")
    app.state.db.close()


app = FastAPI(lifespan=lifespan)

@app.get("/api/v1/check-bot")
async def check_bot(
        x_real_ip: Optional[str] = Header(default="", alias="X-Real-IP"),
        pow_token: Optional[str] = Cookie(default=None)
    ):

    print(f"DEBUG: FastAPI получил IP -> {x_real_ip}")

    if not pow_token:
        print(1)
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    try:
        parts = pow_token.split(":")
        if len(parts) != 3:
            print(2)
            return Response(status_code=status.HTTP_403_FORBIDDEN)

        timestamp_str, nonce_str, client_hash = parts
        timestamp = int(timestamp_str)

        current_utc = int(time.time())
        
        if (current_utc - timestamp) > MAX_AGE_SECONDS or (timestamp - current_utc) > 10:
            print(3)
            return Response(status_code=status.HTTP_403_FORBIDDEN)

        raw_payload = f"{x_real_ip}:{timestamp}:{nonce_str}:{SECRET_SALT}"
        calculated_hash = hashlib.sha256(raw_payload.encode('utf-8')).hexdigest()

        if calculated_hash == client_hash and calculated_hash.startswith(PROOF_DIFFICULTY):
            return Response(status_code=status.HTTP_200_OK)

    except (ValueError, TypeError):
        pass
    return Response(status_code=status.HTTP_403_FORBIDDEN)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/v1/login")
async def login():
    token = secrets.token_urlsafe(32)
    content = {"message": "Come to the dark side, we have cookies"}
    response = JSONResponse(content=content)
    response.set_cookie(key="login", value=str(token))
    return response