# initDB.py
initDBsql = """
CREATE TABLE IF NOT EXISTS "project" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "description" TEXT
);

CREATE TABLE IF NOT EXISTS "task_group" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" TEXT NOT NULL,
    "order"	INTEGER DEFAULT 0,
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
    "time" INTEGER NOT NULL,
    FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "version" (
    "version" INTEGER NOT NULL UNIQUE PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS "ruls_typs" (
	"type"	INTEGER NOT NULL,
	"descripion"	TEXT,
	PRIMARY KEY("type" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "rules" (
    "rule_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "id" INTEGER NOT NULL,
    "target"  INTEGER NOT NULL,
    "type"    INTEGER NOT NULL,
    FOREIGN KEY("id") REFERENCES "users"("id") ON DELETE CASCADE,
    FOREIGN KEY("type") REFERENCES "ruls_typs"("type"),
    UNIQUE("id", "target", "type")
);
"""

initDBdata = """
INSERT OR IGNORE INTO ruls_typs (type, descripion) 
VALUES (0, 'root УДОЛИТЬ ИЗ ПРОДА, ТОЛЬКЛ ДЛЯ ТЕСТОВ'),
(1, 'владелец проекта (полный контроль)'),
(2, 'чтение проекта'),
(3, 'запись/редактирование проекта'),
(4, 'чтение группы задач'),
(5, 'запись/редактирование группы задач'),
(6, 'удаление проекта или групп'),
(7, 'управление участниками проекта'),
(8, 'чтение задач (отдельных карточек)'),
(9, 'создание/редактирование задач'),
(10, 'удаление задач');

INSERT OR IGNORE INTO users (id, login, display_name,  password) 
VALUES (1, 'test', 'test/guest', '$argon2id$v=19$m=65536,t=3,p=4$z7M+qxvUhtDoBo5dwRPuJQ$2SHvQxieni6CkiEiUecN/ll085GjS5meU6IVJODgiHk');

INSERT OR IGNORE INTO rules (id, target, type) 
VALUES (1, 1, 0);

-- Добавляем тестовый проект
INSERT OR IGNORE INTO "project" (id, name, description) 
VALUES (1, 'Мой Kanban-проект', 'Основной проект для тестирования бэкенда и интерфейса');

-- Добавляем колонки (группы задач) для Kanban-доски
INSERT OR IGNORE INTO "task_group" (id, name, project_id) 
VALUES 
(1, 'К выполнению', 1),
(2, 'В процессе', 1),
(3, 'Готово', 1);

-- Добавляем пару карточек задач
INSERT OR IGNORE INTO "task" (id, name, text, task_group_id) 
VALUES 
(1, 'Написать бэкенд на FastAPI', 'Реализовать авторизацию, сессии и роутеры', 2),
(2, 'Подключить SQLite', 'Настроить миграции через executescript и внешние ключи', 3);
"""