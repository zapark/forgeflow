# ForgeFlow Backend (MVP Scaffold)

## Run

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## APIs
- `GET /health`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `POST /api/v1/tasks/{task_id}/control`
- `POST /api/v1/executions/{task_id}/start`
- `GET /api/v1/executions/{task_id}/timeline`
- `POST /api/v1/executions/{task_id}/checkpoint/{node_id}/approve`

## Notes
- `GET /api/v1/executions/{task_id}/timeline` supports `event_type`, `limit`, `offset` query params.
- `POST /api/v1/tasks/{task_id}/control` enforces action whitelist: pause/resume/cancel.

## Config
- 配置统一在 `backend/app/core/config.py`，通过 `.env` 注入。
- 可参考 `backend/.env.example`。
