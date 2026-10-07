# initDB.py
initDBsql = """
CREATE TABLE IF NOT EXISTS "project" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL UNIQUE,
    "description" TEXT
);

CREATE TABLE IF NOT EXISTS "task_group" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "project_id" INTEGER NOT NULL,
    FOREIGN KEY("project_id") REFERENCES "project"("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "task" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "text" TEXT,
    "task_group_id" INTEGER NOT NULL,
    FOREIGN KEY("task_group_id") REFERENCES "task_group"("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "login" TEXT NOT NULL UNIQUE,
    "display_name" TEXT,
    "password" TEXT NOT NULL,
    "old_password" TEXT,
    "password_set_time" INTEGER
);

CREATE TABLE IF NOT EXISTS "sessions" (
    "session_key" TEXT PRIMARY KEY,
    "user_id" INTEGER NOT NULL,
    FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "version" (
    "version" INTEGER NOT NULL UNIQUE PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS "rules" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "target" INTEGER NOT NULL,
    "type" INTEGER NOT NULL
);
"""