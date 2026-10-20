# main.py

#Abandon hope, all you who enter here

from contextlib import asynccontextmanager
from fastapi import Form, FastAPI, Header, Cookie, Response, status, Depends, Request
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
import hashlib
import ruls_typs
import asyncio
import sqlite3
import platform
import time, secrets
import os, signal

DB_VERSION = 1
PROOF_DIFFICULTY = "0000"
MAX_AGE_SECONDS = 600
SECRET_SALT = "BigfishForCat"
DB_PATH = "/app/data/AppData.db"
if platform.system() == "Windows":
    DB_PATH = "./../data/AppData.db"

class ProjectEventsManager:
    def __init__(self):
        self.list: dict[int, list[asyncio.Queue]] = {}
        self.closing = False

    async def broadcast(self, project_id: int):
        if project_id in self.list:
            for queue in self.list[project_id]:
                queue.put_nowait("update")

    async def event_generator(self, project_id: int):
        if self.closing:
            return
        queue = asyncio.Queue()
        
        if project_id not in self.list:
            self.list[project_id] = []
        self.list[project_id].append(queue)
        
        try:
            yield "data: connected\n\n"
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue
                if message is None:
                    break
                yield f"data: {message}\n\n"
        finally:
            if project_id in self.list and queue in self.list[project_id]:
                self.list[project_id].remove(queue)
                if not self.list[project_id]:
                    del self.list[project_id]
    def disconnect_all(self):
        self.closing = True
        for queues in list(self.list.values()):
            for queue in list(queues):
                queue.put_nowait(None)   # не queue.put(None)


events_manager = ProjectEventsManager()
        
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("ЗАПУСК")
    if not os.path.isfile(DB_PATH):
        print(f"Создание файла БД")

    app.state.db = sqlite3.connect(DB_PATH)
    db = app.state.db
    db.execute("PRAGMA foreign_keys = ON;")

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

    test = cursor.execute("SELECT id FROM users WHERE login=('test');").fetchone()

    if test is None:
        print("initDBdata")
        from initDB import initDBdata
        cursor.executescript(initDBdata)
        db.commit()

    cleanup_task = asyncio.create_task(periodic_session_cleanup())

    app.state.loop = asyncio.get_running_loop()
    loop = app.state.loop
    for sig in (signal.SIGINT, signal.SIGTERM):
        saved = signal.getsignal(sig)

        def handler(signo, frame, saved=saved):
            loop.call_soon_threadsafe(events_manager.disconnect_all)
            if callable(saved):
                saved(signo, frame)

        signal.signal(sig, handler)

    yield

    print("ОСТАНОВКА")
    cleanup_task.cancel()
    app.state.db.close()


app = FastAPI(lifespan=lifespan)

password_hash = PasswordHash((Argon2Hasher(),))

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

async def periodic_session_cleanup():
    print("Привет из фоновой задачи")
    while True:
        await asyncio.sleep(3600)
        expiration_time = int(time.time()) - 604800 # неделя
        cursor = app.state.db.cursor()
        cursor.execute("DELETE FROM sessions WHERE time < ?;", (expiration_time,))
        app.state.db.commit()

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}

class UnauthorizedError(Exception):
    pass

@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError):
    response = Response(status_code=status.HTTP_401_UNAUTHORIZED)
    response.delete_cookie("login")
    return response

async def get_current_user_id(login: str | None = Cookie(default=None)) -> int:
    if not login:
        raise UnauthorizedError()
    
    db = app.state.db
    cursor = db.cursor()
    user = cursor.execute("SELECT user_id FROM sessions WHERE session_key = ?;", (login,)).fetchone()
    
    if user is None:
        raise UnauthorizedError()
        
    return user[0]



@app.get("/api/v1/projects/{project_id}/events")
async def project_events(project_id: int | None = None, user: int = Depends(get_current_user_id)):
    if not project_id:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    cursor = app.state.db.cursor()
    r = ruls_typs

    query = """
        SELECT 1 
        FROM rules 
        WHERE id = ? AND (
            target = ? 
            OR target IN (SELECT id FROM task_group WHERE project_id = ?)
        )
        LIMIT 1;
    """

    permision = cursor.execute(query, (user, project_id, project_id)).fetchall()

    if not permision:
        return Response(status_code=403, content="Forbidden")

    return StreamingResponse(events_manager.event_generator(project_id), 
                                media_type="text/event-stream",
                                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
                             )

    

@app.post("/api/v1/login")
async def login(redirect_to: str = "/",
                username = Form(""),
                password = Form("")):

    if password == "" or username == "":
        return Response(status_code=status.HTTP_400_BAD_REQUEST)
    
    cursor = app.state.db.cursor()

    row = cursor.execute("SELECT password, id FROM users WHERE login=(?);", (username,)).fetchone()
    if not row is None:
        werif = verify_password(password, row[0])
        if not werif:
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    else:
        cursor.execute("INSERT INTO users (login, password) VALUES (?, ?);", (username, get_password_hash(password)))
        row = ("", cursor.lastrowid)

    sesion = secrets.token_urlsafe(32)
    cursor.execute("INSERT INTO sessions VALUES (?, ?, ?);", (sesion, row[1], int(time.time())))
    app.state.db.commit()

    if not redirect_to.startswith("/") or redirect_to.startswith("//"):
        redirect_to = "/"

    response = RedirectResponse(redirect_to, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="login", value=str(sesion), httponly=True)
    return response

# @app.post("/api/v1/login_guest")
# async def login():
#     cursor = app.state.db.cursor()

#     sesion = secrets.token_urlsafe(32)
#     cursor.execute("INSERT INTO sessions VALUES (?, ?, ?);", (sesion, 1, int(time.time())))
#     app.state.db.commit()

#     response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
#     response.set_cookie(key="login", value=str(sesion), httponly=True)
#     return response



@app.post("/api/v1/logout")
async def logout(login: str | None = Cookie(default=None)):

    if not login:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    cursor = app.state.db.cursor()
    cursor.execute("DELETE FROM sessions WHERE session_key=(?);", (login,))
    app.state.db.commit()

    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("login")
    return response

@app.get("/api/v1/user/display_name")
async def get_display_name(user : int = Depends(get_current_user_id)):
    cursor = app.state.db.cursor()

    display_name = cursor.execute("SELECT display_name FROM users WHERE id=(?);", (user,)).fetchone()[0]

    return JSONResponse(content={"display_name":display_name})

@app.get("/api/v1/user/permisions")
async def get_permisions(user : int = Depends(get_current_user_id)):

    cursor = app.state.db.cursor()

    permisions = cursor.execute("SELECT target, type FROM rules WHERE id=(?);", (user,)).fetchall()
    ruls_typs_db = cursor.execute("SELECT * FROM ruls_typs;").fetchall()

    return JSONResponse(content={"ruls_typs":ruls_typs_db,"list":permisions})

@app.get("/api/v1/user/projects")
async def get_proj_list(user: int = Depends(get_current_user_id)):
    cursor = app.state.db.cursor()
    r = ruls_typs

    query = f"""
        SELECT id, name, description 
        FROM project 
        WHERE id IN (
            SELECT target 
            FROM rules 
            WHERE id = ? AND type IN ({r.ROOT}, {r.PROJ_OWN}, {r.READ_PROJ}, {r.WRITE_PROJ}, {r.DELETE_PROJ_GROUP}, {r.MANAGE_MEMBERS})
        );
    """

    permisions = cursor.execute(query, (user,)).fetchall()
    return JSONResponse(content=permisions)

@app.get("/api/v1/projects/{project_id}/groups")
async def get_project_groups(project_id: int, user: int = Depends(get_current_user_id)):
    cursor = app.state.db.cursor()
    r = ruls_typs

    access_query = f"""
        SELECT 1 FROM rules 
        WHERE id = ? AND target = ? AND type IN (
            {r.ROOT}, {r.PROJ_OWN}, {r.READ_PROJ}, {r.WRITE_PROJ}, 
            {r.DELETE_PROJ_GROUP}, {r.READ_GROUP}, {r.WRITE_GROUP}
        )
    """
    has_access = cursor.execute(access_query, (user, project_id)).fetchone()

    if not has_access:
        return Response(status_code=404, content=":(")

    groups_query = """
        SELECT id, name, project_id, "order"
        FROM task_group 
        WHERE project_id = ?;
    """
    
    groups = cursor.execute(groups_query, (project_id,)).fetchall()
    return JSONResponse(content=groups)

@app.get("/api/v1/projects/{project_id}/tasks")
async def get_project_tasks(project_id: int, user: int = Depends(get_current_user_id)):
    cursor = app.state.db.cursor()
    r = ruls_typs

    access_query = f"""
        SELECT 1 FROM rules 
        WHERE id = ? AND target = ? AND type IN (
            {r.ROOT}, {r.PROJ_OWN}, {r.READ_PROJ}, {r.WRITE_PROJ}, {r.DELETE_PROJ_GROUP}, {r.MANAGE_MEMBERS}
        )
    """
    has_access = cursor.execute(access_query, (user, project_id)).fetchone()

    if not has_access:
        return Response(status_code=404, content=":(")

    tasks_query = """
        SELECT t.id, t.name, t.text, t.task_group_id 
        FROM task t
        JOIN task_group tg ON t.task_group_id = tg.id
        WHERE tg.project_id = ?;
    """
    
    tasks = cursor.execute(tasks_query, (project_id,)).fetchall()
    return JSONResponse(content=tasks)

@app.post("/api/v1/projects/{selectedProject}/add_group")
async def add_group(selectedProject: int, request: Request, user: int = Depends(get_current_user_id)):
    body = await request.json()
    group_name = body.get("name")

    if not group_name:
        return Response(status_code=400, content="Name is required")

    cursor = app.state.db.cursor()
    
    r = ruls_typs
    
    access_query = f"""
        SELECT 1 FROM rules 
        WHERE id = ? AND target = ? AND type IN (
            {r.ROOT}, {r.PROJ_OWN}, {r.WRITE_GROUP}, {r.WRITE_PROJ}, {r.DELETE_PROJ_GROUP}, {r.MANAGE_MEMBERS}
        )
    """
    has_access = cursor.execute(access_query, (user, selectedProject)).fetchone()

    if not has_access:
        return Response(status_code=403, content="Forbidden")
    
    cursor.execute(
        "INSERT INTO task_group (name, project_id) VALUES (?, ?);",
        (group_name, selectedProject)
    )
    app.state.db.commit()

    await events_manager.broadcast(selectedProject)
    
    return {"status": "success"}

@app.post("/api/v1/groups/{group_id}/add_task")
async def add_task(group_id: int, request: Request, user: int = Depends(get_current_user_id)):
    body = await request.json()
    task_name = body.get("name")
    task_text = body.get("text", "")

    if not task_name:
        return Response(status_code=400, content="Task name is required")

    cursor = app.state.db.cursor()

    group_row = cursor.execute("SELECT project_id FROM task_group WHERE id = ?;", (group_id,)).fetchone()
    if not group_row:
        return Response(status_code=404, content="Group not found")
    
    project_id = group_row[0]
    r = ruls_typs

    access_query = f"""
        SELECT 1 FROM rules 
        WHERE id = ? AND target = ? AND type IN (
            {r.ROOT}, {r.PROJ_OWN}, {r.WRITE_GROUP}, {r.WRITE_TASK}, {r.WRITE_PROJ}, {r.MANAGE_MEMBERS}
        )
    """
    has_access = cursor.execute(access_query, (user, project_id)).fetchone()

    if not has_access:
        return Response(status_code=403, content="Forbidden")

    cursor.execute(
        "INSERT INTO task (name, text, task_group_id) VALUES (?, ?, ?);",
        (task_name, task_text, group_id)
    )
    app.state.db.commit()

    await events_manager.broadcast(project_id)

    return {"status": "success"}

@app.delete("/api/v1/tasks/{task_id}")
async def delete_task(task_id: int, user: int = Depends(get_current_user_id)):
    cursor = app.state.db.cursor()
    
    task_row = cursor.execute("SELECT task_group_id FROM task WHERE id = ?;", (task_id,)).fetchone()
    if not task_row:
        return Response(status_code=404, content="task not found")
    
    task_group_id = task_row[0]

    r = ruls_typs

    access_query = f"""
        SELECT 1 FROM rules 
        WHERE id = ? AND target = ? AND type IN (
            {r.ROOT}, {r.PROJ_OWN}, {r.WRITE_GROUP}, {r.WRITE_TASK}, {r.WRITE_PROJ}, {r.MANAGE_MEMBERS}
        )
        """
    
    has_access = cursor.execute(access_query, (user, task_group_id)).fetchone()
    
    project_access_query = f"""
        SELECT 1 FROM rules 
        WHERE id = ? AND target = (SELECT project_id FROM task_group WHERE id = ?) AND type IN (
            {r.ROOT}, {r.PROJ_OWN}, {r.WRITE_PROJ}, {r.MANAGE_MEMBERS}
        )
    """

    if not has_access:
        has_access = cursor.execute(project_access_query, (user, task_group_id)).fetchone()
        if not has_access:
            return Response(status_code=403, content="Forbidden")

    cursor.execute(
        "DELETE FROM task WHERE id = ?;",
        (task_id,)
    )

    app.state.db.commit()

    project_id = cursor.execute("SELECT project_id FROM task_group WHERE id = ?;", (task_id,)).fetchone()
    if project_id:
        await events_manager.broadcast(project_id[0])

    return {"status": "success"}


@app.delete("/api/v1/groups/{group_id}")
async def delete_group(group_id: int, user: int = Depends(get_current_user_id)):
    cursor = app.state.db.cursor()
    
    # Находим проект, к которому принадлежит группа
    group_row = cursor.execute("SELECT project_id FROM task_group WHERE id = ?;", (group_id,)).fetchone()
    if not group_row:
        return Response(status_code=404, content="group not found")
    
    project_id = group_row[0]
    r = ruls_typs

    # Проверяем права на уровне группы
    access_query = f"""
        SELECT 1 FROM rules 
        WHERE id = ? AND target = ? AND type IN (
            {r.ROOT}, {r.PROJ_OWN}, {r.WRITE_GROUP}, {r.DELETE_PROJ_GROUP}, {r.WRITE_PROJ}, {r.MANAGE_MEMBERS}
        )
    """
    has_access = cursor.execute(access_query, (user, group_id)).fetchone()
    
    # Проверяем права на уровне проекта, если на группе нет явного правила
    project_access_query = f"""
        SELECT 1 FROM rules 
        WHERE id = ? AND target = ? AND type IN (
            {r.ROOT}, {r.PROJ_OWN}, {r.DELETE_PROJ_GROUP}, {r.WRITE_PROJ}, {r.MANAGE_MEMBERS}
        )
    """

    if not has_access:
        has_access = cursor.execute(project_access_query, (user, project_id)).fetchone()
        if not has_access:
            return Response(status_code=403, content="Forbidden")

    # Удаляем группу (благодаря ON DELETE CASCADE в БД задачи внутри тоже удалятся)
    cursor.execute(
        "DELETE FROM task_group WHERE id = ?;",
        (group_id,)
    )
    app.state.db.commit()

    await events_manager.broadcast(project_id)

    return {"status": "success"}

@app.post("/api/v1/projects")
async def create_project(request: Request, user: int = Depends(get_current_user_id)):
    body = await request.json()
    name = body.get("name")
    description = body.get("description", "")

    if not name:
        return Response(status_code=400, content="Project name is required")

    cursor = app.state.db.cursor()
    cursor.execute(
        "INSERT INTO project (name, description) VALUES (?, ?);",
        (name, description)
    )
    project_id = cursor.lastrowid

    r = ruls_typs
    cursor.execute(
        "INSERT INTO rules (id, target, type) VALUES (?, ?, ?);",
        (user, project_id, r.PROJ_OWN)
    )

    app.state.db.commit()
    return JSONResponse(content={"status": "success", "project_id": project_id})

@app.delete("/api/v1/projects/{project_id}")
async def delete_project(project_id: int, user: int = Depends(get_current_user_id)):
    cursor = app.state.db.cursor()
    r = ruls_typs
    access_query = f"""
        SELECT 1 FROM rules 
        WHERE id = ? AND target = ? AND type IN (
            {r.ROOT}, {r.PROJ_OWN}, {r.DELETE_PROJ_GROUP}, {r.WRITE_PROJ}, {r.MANAGE_MEMBERS}
        )
    """
    has_access = cursor.execute(access_query, (user, project_id)).fetchone()

    if not has_access:
        return Response(status_code=403, content="Forbidden")

    cursor.execute(
        "DELETE FROM project WHERE id = ?;",
        (project_id,)
    )
    app.state.db.commit()

    await events_manager.broadcast(project_id)

    return {"status": "success"}

@app.post("/api/v1/tasks/{task_id}/move/{group_id}")
async def move_task(task_id: int, group_id: int, user: int = Depends(get_current_user_id)):
    cursor = app.state.db.cursor()
    
    task_row = cursor.execute("""
        SELECT t.id, tg.project_id 
        FROM task t 
        JOIN task_group tg ON t.task_group_id = tg.id 
        WHERE t.id = ?;
    """, (task_id,)).fetchone()
    
    if not task_row:
        return Response(status_code=404, content="Task not found")
    
    current_project_id = task_row[1]

    target_group_row = cursor.execute("""
        SELECT project_id FROM task_group WHERE id = ?;
    """, (group_id,)).fetchone()
    
    if not target_group_row:
        return Response(status_code=404, content="Target group not found")
    
    target_project_id = target_group_row[0]

    if current_project_id != target_project_id:
        return Response(status_code=400, content="Cannot move task to another project")

    r = ruls_typs
    access_query = f"""
        SELECT 1 FROM rules 
        WHERE id = ? AND target = ? AND type IN (
            {r.ROOT}, {r.PROJ_OWN}, {r.WRITE_GROUP}, {r.WRITE_TASK}, {r.WRITE_PROJ}, {r.MANAGE_MEMBERS}
        )
    """
    has_access = cursor.execute(access_query, (user, current_project_id)).fetchone()

    if not has_access:
        return Response(status_code=403, content="Forbidden")

    # 4. Выполняем перемещение
    cursor.execute(
        "UPDATE task SET task_group_id = ? WHERE id = ?;",
        (group_id, task_id)
    )
    app.state.db.commit()

    await events_manager.broadcast(current_project_id)

    return {"status": "success"}

def debug_console(local_vars):
    import code
    from time import sleep
    sleep(3)
    code.interact(local=local_vars)

if __name__ == "__main__":
    import uvicorn
    import threading
    print("Запуск в режиме разработки/отладки :)")

    def debugBroadcast(project_id: int):
        """Отправить 'update' подписчикам проекта из консоли."""
        return asyncio.run_coroutine_threadsafe(
            events_manager.broadcast(project_id), app.state.loop
        ).result(timeout=5)

    debug_locals = {
        "app": app,
        "events_manager": events_manager,
        "debugBroadcast": debugBroadcast,
    }

    threading.Thread(target=debug_console, args=(debug_locals,), daemon=True).start()

    print("Запуск FastAPI сервера...")
    uvicorn.run(app, host="127.0.0.1", port=9254)