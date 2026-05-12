# ForgeFlow 技术开发文档（TDD）v1.0

## 1. 目标与范围

本技术文档用于把 `PRD_v0.1.md` 与 `PRD_REVIEW_v0.1.md` 转换为可执行研发方案，覆盖架构、接口、数据模型、流程、权限、安全、可观测性、测试与迭代计划。

V1-MVP 范围：
- 任务创建与目标解析
- 多角色协作执行（Planner/Operator/Reviewer）
- Workflow 编排与恢复
- Tool Runtime 与权限控制
- Scheduler 持续调度
- Replay & Audit 可追踪
- Electron Desktop + Web 客户端（C/S 分离）

---

## 2. 系统架构（C/S 分离）

### 2.1 客户端
- Web：Next.js
- Desktop：Electron + WebView
- CLI：开发者调试入口

### 2.2 服务端
- API Gateway（FastAPI）
- Task Center
- Planner Service
- Role Orchestrator
- Workflow Engine
- Tool Runtime
- Scheduler
- Replay & Audit

### 2.3 存储层
- SQLite：任务、流程、审计元数据
- ChromaDB：向量检索
- Local FS：工作区与产物

### 2.4 发布策略
- 客户端与服务端独立打包、独立发布
- 通过 API version + schema contract 做兼容控制

---

## 3. 核心数据模型

## 3.1 tasks
- id (PK)
- title
- goal_text
- status: CREATED/PLANNING/RUNNING/WAITING_HUMAN/SUCCESS/FAILED/CANCELED
- created_by
- created_at
- updated_at

## 3.2 workflow_runs
- id (PK)
- task_id (FK)
- workflow_spec_version
- current_node_id
- status
- started_at
- ended_at

## 3.3 workflow_events
- id (PK)
- workflow_run_id (FK)
- event_type
- payload_json
- trace_id
- created_at

## 3.4 tool_runs
- id (PK)
- workflow_run_id (FK)
- tool_name
- permission_snapshot_json
- input_json
- output_json
- error_json
- duration_ms
- token_cost
- created_at

## 3.5 audit_logs
- id (PK)
- actor
- action
- target
- decision
- reason
- trace_id
- created_at

---

## 4. API 详细设计（MVP）

## 4.1 任务管理

### POST /api/v1/tasks
创建任务。

Request:
```json
{
  "title": "每日AI热点追踪",
  "goal": "每天早上8点生成行业热点与公众号草稿",
  "constraints": {
    "budget_token": 50000,
    "deadline": "2026-05-10T08:00:00Z"
  }
}
```

Response:
```json
{
  "task_id": "tsk_001",
  "status": "CREATED"
}
```

### GET /api/v1/tasks/{task_id}
查询任务详情与当前状态。

### POST /api/v1/tasks/{task_id}/control
控制任务执行（pause/resume/cancel/intervene）。

Request:
```json
{
  "action": "pause",
  "reason": "人工复核"
}
```

## 4.2 执行控制

### POST /api/v1/executions/{task_id}/start
触发任务执行，进入规划与编排。

### GET /api/v1/executions/{task_id}/timeline
获取可视化执行时间线（支持监督）。

### POST /api/v1/executions/{task_id}/checkpoint/{node_id}/approve
人工审批高风险节点。

## 4.3 回放审计

### GET /api/v1/replay/{workflow_run_id}
返回 workflow 节点级事件流。

### GET /api/v1/audit/{task_id}
返回审计日志。

---

## 5. WorkflowSpec v1（建议）

```json
{
  "workflow_id": "wf_daily_news",
  "version": "1.0.0",
  "nodes": [
    {"id": "n1", "type": "TASK", "role": "Planner"},
    {"id": "n2", "type": "PARALLEL", "children": ["n3", "n4"]},
    {"id": "n3", "type": "TOOL_CALL", "tool": "news_search"},
    {"id": "n4", "type": "TOOL_CALL", "tool": "trend_analyze"},
    {"id": "n5", "type": "HUMAN_CHECKPOINT"},
    {"id": "n6", "type": "TASK", "role": "Reviewer"}
  ],
  "edges": [
    {"from": "n1", "to": "n2"},
    {"from": "n2", "to": "n5"},
    {"from": "n5", "to": "n6"}
  ],
  "retry_policy": {"max_retries": 3, "backoff": "exponential"},
  "timeout_sec": 3600
}
```

---

## 6. ToolSpec v1（建议）

```json
{
  "tool_name": "news_search",
  "version": "0.1.0",
  "permissions": ["net.http", "fs.write"],
  "allowed_domains": ["arxiv.org", "techcrunch.com"],
  "input_schema": {"type": "object"},
  "output_schema": {"type": "object"},
  "resource_limit": {
    "timeout_sec": 30,
    "memory_mb": 256,
    "cpu_quota": 0.5
  },
  "risk_level": "medium"
}
```

---

## 7. 权限与治理

- 默认 deny-all
- 基于 Casbin 的策略控制（用户、角色、资源、动作）
- 高风险动作自动 checkpoint：
  - shell.exec
  - 外部写入接口
  - 文件系统写入敏感路径

治理能力要求：
- 可监督：timeline + 状态看板
- 可干预：pause/resume/intervene
- 可控制：预算、权限、白名单策略
- 可交互：自然语言改写目标与约束
- 可无值守：自动重试 + 状态恢复

---

## 8. 调度与恢复

- APScheduler 执行 Cron 与延迟任务
- 服务启动时自动扫描未完成任务并恢复
- 幂等键：`task_id + node_id + attempt`
- 恢复优先级：WAITING_HUMAN > RUNNING > FAILED_RETRYABLE

---

## 9. 可观测性

### 指标
- task_success_rate
- workflow_recovery_rate
- human_intervention_count
- p95_task_startup_latency
- tool_error_rate
- token_cost_per_task

### 日志
- JSON 结构化日志
- 必含 trace_id、task_id、workflow_run_id

### 链路
- OpenTelemetry（可选）

---

## 10. 测试策略

1. 单元测试：状态机、重试逻辑、权限策略
2. 集成测试：task -> workflow -> tool -> audit
3. E2E：
   - 每日热点追踪任务
   - 自动周报生成任务
4. 安全测试：越权/注入/恶意工具调用

验收标准（MVP）：
- 端到端成功率 >= 80%
- 自动恢复成功率 >= 60%
- P95 启动时延 <= 10 秒
- 平均人工介入 <= 1 次/任务

---

## 11. 迭代里程碑（10 周建议）

- W1-W2：架构骨架 + 数据模型 + 任务API
- W3-W4：Planner + Workflow 基础节点
- W5-W6：Tool Runtime + 权限控制 + 审计
- W7-W8：Scheduler + 恢复 + 回放
- W9-W10：E2E、压测、文档与Beta发布

---

## 12. 后续文档建议

建议下一步新增三份配套文档：
1. `OPENAPI_v1.yaml`（接口契约）
2. `SCHEMA_v1.sql`（数据库建表脚本）
3. `RUNBOOK_v1.md`（运维与故障处理手册）
