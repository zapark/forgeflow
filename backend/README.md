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
- `GET /api/v1/replay/{workflow_run_id}`
- `POST /api/v1/workflow-runs/{workflow_run_id}/tools/execute`

## Notes
- `GET /api/v1/executions/{task_id}/timeline` supports `event_type`, `limit`, `offset` query params.
- `POST /api/v1/tasks/{task_id}/control` enforces action whitelist: pause/resume/cancel.
- `POST /api/v1/executions/{task_id}/start` seeds the MVP execution chain with Planner/Operator role runs, a local workspace tool run, audit entry, timeline events, and a human checkpoint.
- `GET /api/v1/replay/{workflow_run_id}` returns the workflow run, workflow events, role runs, and tool runs for replay/debugging.
- `POST /api/v1/workflow-runs/{workflow_run_id}/tools/execute` validates ToolSpec permissions, records audit/timeline traces, and converts configured high-risk tools into checkpoints instead of executing them.

## Config
- 配置统一在 `backend/app/core/config.py`，通过 `.env` 注入。
- 可参考 `backend/.env.example`。
- `GET /api/v1/settings`
- `GET /api/v1/settings/{key}`
- `PUT /api/v1/settings/{key}`

## Runtime Config Priority
- API 运行时参数读取优先级：`SystemSetting(DB)` > `.env` > 代码默认值。
- `PUT /api/v1/settings/{key}` only accepts keys in `EDITABLE_SETTING_KEYS`; successful updates write audit log.
- Runtime tool guard settings: `ALLOWED_TOOL_PERMISSIONS` and `CHECKPOINT_TOOL_RISK_LEVELS`.
- `GET /api/v1/audit` (supports actor/action/decision/start_at/end_at/limit/offset)
- `GET /api/v1/audit/task/{task_id}`
- `GET /api/v1/audit/export.csv?actor=&action=&decision=&start_at=&end_at=&limit=1000`
- `GET /api/v1/audit/stats?start_at=&end_at=`
- `GET /api/v1/audit/stats/task/{task_id}`

## Test
```bash
pytest -q
```

## CI/本地一致测试入口
- 推荐使用 `backend/scripts/run_tests.sh` 作为统一测试入口。

- 当前测试覆盖：`test_services.py`、`test_runtime_config.py`、`test_task_service_success.py`。
