ForgeFlow 技术开发文档（TDD）v1.0
1. 文档目标与范围
1.1 目标
将 PRD_v0.1 的产品目标转化为可实施、可验收、可迭代的工程方案，指导研发团队完成 V1-MVP 交付。

1.2 范围（V1-MVP）
包含：

需求到任务的自动化创建

数字化团队（多角色）协作执行

Workflow 编排与持续执行

Tool Runtime 安全执行

Scheduler 调度与自动恢复

Replay & Audit 可观测可追溯

Desktop（Electron）与 Web 客户端接入

不包含：

Skill Marketplace 开放市场

多组织复杂协同

大规模分布式 GPU 调度

高自治长期项目管理

2. 总体架构设计
2.1 架构原则
C/S 分离：客户端（Desktop/Web）与服务端独立部署、独立发布。

能力复用优先：优先采用成熟开源组件，避免重复造轮子。

全智化可治理：自动执行必须可监督、可干预、可控制。

Local-First：支持本地优先存储与执行，兼容私有化部署。

可审计性优先：所有关键动作可回放、可追踪、可归责。

2.2 逻辑架构分层
Client Layer
Web（Next.js）

Desktop（Electron + WebView）

CLI（开发者模式）

API & Orchestration Layer
API Gateway（FastAPI）

Task Center（任务生命周期管理）

Planner Service（目标解析与计划生成）

Workflow Engine（流程执行引擎）

Role Orchestrator（角色协作协调）

Scheduler Service（定时与重试）

Replay/Audit Service（回放与审计）

Runtime Layer
Tool Runtime（工具统一执行）

Permission Guard（权限策略执行）

Worker Manager（执行 worker 池）

Env Manager（Python/uv 环境隔离）

Storage Layer
SQLite（元数据）

ChromaDB（向量索引）

Local FS（工作区与产物）

可选 Redis（队列/缓存，后续可加）

3. 技术选型与职责
层	组件	选型	说明
前端	Web	Next.js	主交互界面
前端	Desktop	Electron + WebView	承载 Web 能力并扩展桌面能力
后端	API	FastAPI	高效接口开发
编排	Workflow	LangGraph	节点编排与状态图
调度	Scheduler	APScheduler	Cron/重试/延时
模型网关	LLM Gateway	LiteLLM	多模型统一调用
权限	RBAC/ABAC	Casbin	策略管理
数据	Metadata	SQLite	MVP 轻量化
向量	Vector DB	ChromaDB	检索与语义记忆
环境	Runtime	uv + subprocess	工具隔离执行
4. 核心模块详细设计
4.1 Task Center（任务中心）
职责
创建任务、更新状态、跟踪生命周期

关联 workflow_run / role_run / tool_run

提供任务级查询与统计接口

状态机
CREATED -> PLANNING -> RUNNING -> WAITING_HUMAN -> SUCCESS | FAILED | CANCELED

核心接口
POST /tasks 创建任务

GET /tasks/{id} 任务详情

POST /tasks/{id}/pause 暂停

POST /tasks/{id}/resume 恢复

POST /tasks/{id}/cancel 取消

4.2 Planner Service（规划服务）
输入
用户目标（自然语言）

约束（预算/时限/权限/质量目标）

业务上下文（可选）

输出
结构化执行计划（PlanSpec）

Workflow 草图（WorkflowSpec）

角色分工（RoleAssignments）

KPI 与验收标准（AcceptanceSpec）

关键能力
Goal Clarification（目标澄清）

Task Decomposition（任务拆解）

Risk Flagging（风险提示）

Human Checkpoint 注入

4.3 Role Orchestrator（角色协作器）
V1 角色
Planner

Operator

Reviewer
（Researcher/Reporter 可在 V1.1 扩展）

协作协议（Role Contract）
输入契约：角色可消费的结构化上下文

输出契约：角色输出必须结构化（result + confidence + evidence）

交接契约：handoff reason + next action

升级契约：异常时升级到 human checkpoint

4.4 Workflow Engine
支持节点类型
Start / End

TaskNode

ParallelNode

ConditionNode

RetryNode

DelayNode

HumanCheckpointNode

ToolCallNode

执行策略
幂等键：task_id + node_id + attempt

重试：指数退避（默认 3 次）

超时：节点级 timeout（默认 30s，可覆盖）

失败补偿：可选 compensation handler

恢复：从最近持久化节点恢复

4.5 Tool Runtime
ToolSpec v1（建议）
{
  "tool_name": "string",
  "version": "string",
  "permissions": ["fs.read", "net.http", "shell.exec"],
  "input_schema": {},
  "output_schema": {},
  "resource_limit": {
    "timeout_sec": 30,
    "cpu_quota": 0.5,
    "memory_mb": 256
  },
  "allowed_domains": [],
  "risk_level": "low|medium|high"
}
安全策略
默认 deny-all

按 tool 声明最小权限授权

高风险操作自动插入 checkpoint

全量 trace（入参/出参/错误/耗时/资源/token）

4.6 Scheduler Service
功能
Cron 调度

失败重试调度

恢复任务调度

条件触发（V1 可简化）

恢复策略
服务重启时扫描未完成任务

对 RUNNING 任务执行健康检查并恢复

重复触发通过幂等键去重

4.7 Replay & Audit
回放粒度
Task 级

Workflow 节点级

Tool 调用级

审计字段（最小集合）
who（触发主体）

when（时间）

what（动作）

target（目标资源）

input_digest / output_digest

decision（allow/deny/checkpoint）

trace_id / span_id

5. 数据模型设计（MVP）
5.1 关键表
tasks
id

title

goal_text

status

priority

created_by

created_at / updated_at

workflow_runs
id

task_id

workflow_spec_version

status

current_node

started_at / ended_at

workflow_events
id

workflow_run_id

event_type

payload_json

trace_id

created_at

role_runs
id

workflow_run_id

role_name

input_json

output_json

status

started_at / ended_at

tool_runs
id

workflow_run_id

tool_name

permission_snapshot

input_json

output_json

error_json

duration_ms

token_cost

created_at

audit_logs
id

actor

action

target

decision

reason

trace_id

created_at

6. API 设计（示例）
6.1 任务接口
POST /api/v1/tasks

GET /api/v1/tasks/{task_id}

GET /api/v1/tasks?status=RUNNING

POST /api/v1/tasks/{task_id}/control（pause/resume/cancel/intervene）

6.2 执行接口
POST /api/v1/executions/{task_id}/start

GET /api/v1/executions/{task_id}/timeline

POST /api/v1/executions/{task_id}/checkpoint/{node_id}/approve

6.3 观测接口
GET /api/v1/audit/{task_id}

GET /api/v1/replay/{workflow_run_id}

7. 全智化执行控制面设计
7.1 可监督
实时执行时间线

节点状态与风险提示

成本与token看板

7.2 可干预
暂停/继续

改写后续计划

人工接管单节点执行

7.3 可控制
权限策略模板（个人/团队/企业）

预算上限（任务级）

域名白名单与工具黑名单

7.4 可交互
“现在进展到哪一步？”

“为什么失败？”

“把输出改成企业汇报格式”
（系统应支持上下文对话式调控）

7.5 无值守
自动重试

自动恢复

定时运行

异常告警（邮件/IM，V1 可选）

8. Desktop 架构（Electron）
8.1 结构
main 进程：窗口管理、系统托盘、IPC

renderer：WebView 承载前端页面

preload：安全桥接 API

8.2 与服务端关系
C/S 分离，HTTP/WebSocket 通信

客户端仅负责交互与少量本地能力

服务端负责编排、执行、存储、治理

8.3 发布策略
Electron 客户端独立版本

Backend 服务独立版本

通过 API version 与 schema version 保证兼容

9. 安全与合规
9.1 基线
默认拒绝（deny-all）

最小权限

数据最小化持久化

敏感字段脱敏日志

9.2 风险分级
Low：只读查询

Medium：网络写操作

High：Shell/文件写/外部系统变更（必须 checkpoint）

9.3 合规能力（企业向）
审计导出

操作留痕不可篡改（append-only）

权限审批链

10. 可观测性设计
10.1 日志
structured logging（json）

级别：DEBUG/INFO/WARN/ERROR

关键链路强制 trace_id

10.2 指标
task_success_rate

workflow_recovery_rate

human_intervention_count

p95_task_startup_latency

tool_error_rate

token_cost_per_task

10.3 链路追踪
OpenTelemetry（推荐）

task -> workflow -> role -> tool 全链路 span

11. 开发计划与里程碑（建议）
Phase 0（第1-2周）
项目骨架、数据库 schema、任务中心、基础 API

Electron 壳 + Web 接入

Phase 1（第3-5周）
Planner + Workflow 基础节点

Operator/Reviewer 协作

Tool Runtime 初版 + 权限控制

Phase 2（第6-8周）
Scheduler + 自动恢复

Replay + Audit

干预控制面（pause/resume/checkpoint）

Phase 3（第9-10周）
稳定性强化、压测、验收指标验证

文档完善与 Beta 发布

12. 测试策略
12.1 测试分层
单元测试：节点执行、策略判断、状态机

集成测试：Task→Workflow→Tool 全链路

E2E 测试：真实场景任务跑通

安全测试：越权、注入、恶意工具调用

12.2 核心验收用例
每日行业追踪任务 7 天稳定运行

失败节点可自动恢复并成功继续

高风险操作触发 checkpoint 且可人工批准

全链路回放可还原关键决策点

13. 性能与容量目标（MVP）
并发任务数：20（单机）

P95 任务启动时延：≤10s

单任务平均恢复时长：≤60s

审计查询响应：P95 ≤1s（最近7天数据）

14. 部署方案
14.1 开发环境
docker-compose（api + db + vector）

electron dev + web dev 分离调试

14.2 生产（企业私有化）
后端容器化部署（K8s 可选）

SQLite 可升级到 PostgreSQL（V1.1 建议）

客户端通过 HTTPS/WSS 接入

15. 风险与应对
模型不稳定导致计划质量波动

应对：模板化计划 + Reviewer 校验 + fallback

工具执行安全风险

应对：最小权限 + 风险分级 + checkpoint

长任务中断

应对：状态持久化 + 自动恢复 + 幂等策略

范围膨胀

应对：MVP 冻结 + 变更评审机制

16. 附录：三大自研契约（建议）
WorkflowSpec v1：定义流程结构与执行语义

Governance Contract v1：定义监督/干预/控制接口与规则

Delivery Contract v1：定义交付物格式、质量标准、验收逻辑

如果你愿意，我下一步可以继续给你第 2 份文档：
《ForgeFlow API 详细设计文档（OpenAPI 风格，含请求/响应示例）》，这样后端可以直接开工。
