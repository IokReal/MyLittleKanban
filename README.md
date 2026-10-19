# MyLittleKanban
THIS THING WILL EAT YOUR CAT AND DESTROY SOMETHING

это маленький проектик требуемый по учебе
# install
`git clone git@github.com:IokReal/MyLittleKanban.git`

`docker compose -f compose.yaml up -d --build`

## Commands
- Build: `docker compose -f compose.yaml up -d --build`
- Test: `uv run uvicorn main:app --host 0.0.0.0 --port 9254`

## Architecture & Structure
- `/backend/` — весь бэк
- `/frontend/` — фронт, webroot
- `/rustBotCheck/` — проверка куки для защиты от ботов