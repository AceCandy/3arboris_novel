# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

当前后端质量基线以分层边界清晰、`HTTPException` / logging 模式一致、数据库改动兼容旧库、以及基础启动可用性为主。项目已存在较多真实代码模式，但暂未看到成熟的测试目录与统一异常中间件，因此规范应忠实反映当前做法，而不是假设理想体系已经存在。

参考：

- `backend/app/api/routers/novels.py:57`
- `backend/app/services/novel_service.py:124`
- `backend/app/db/init_db.py:122`
- `backend/app/main.py:17`

---

## Forbidden Patterns

### 1. 在 router 中直接写复杂数据库操作或事务提交

Bad example:

- 在 endpoint 中直接 `session.execute(...)`、`session.commit()`，把业务编排散落到路由层。

### 2. 只改 ORM 模型，不补旧库兼容

Bad example:

- 新增列只改 `models/`，却不更新 `backend/app/db/init_db.py:_ensure_schema_updates()`。

### 3. 捕获异常后把底层错误原文直接暴露给前端

Bad example:

- `raise HTTPException(status_code=500, detail=str(e))`

参考：

- `.trellis/spec/backend/error-handling.md:84`

### 4. 日志里记录敏感信息或无上下文失败信息

Bad example:

- 打印 token、密码、完整章节正文，或只写“失败了”。

---

## Current Baseline Patterns

### 1. router / service / repository 职责边界清晰

Good example:

- router 做依赖注入与响应边界：`backend/app/api/routers/auth.py:22`
- service 做业务编排与事务提交：`backend/app/services/novel_service.py:124`
- repository 做数据访问：`backend/app/repositories/user_repository.py:13`

### 2. 非预期异常优先 `logger.exception(...)`

Good example:

- `backend/app/api/routers/novels.py:183`
- `backend/app/db/init_db.py:48`

### 3. 数据库变更保持幂等并兼容旧库

Good example:

- `backend/app/db/init_db.py:129`
- `backend/app/db/init_db.py:147`

### 4. 新日志保持稳定文案并带关键实体 ID

Good example:

- `backend/app/api/routers/novels.py:67`
- `backend/app/api/routers/novels.py:159`

---

## Testing Requirements

当前项目未体现出成熟自动化测试基线，因此真实最低验证通常是：

1. 改动后至少验证应用仍能启动
2. 涉及路由 / service / schema 变更时，至少手动走一遍对应 API 或页面流程
3. 涉及数据库字段或模型修改时，必须验证新库创建与旧库兼容逻辑
4. 涉及 AI / 外部系统调用异常分支时，检查日志和错误响应是否仍符合规范

重点检查：

- `init_db()` 是否仍可重复执行
- 主要接口是否仍返回 `{ "detail": ... }` 错误格式
- service 事务提交后响应数据是否完整

Bad example:

- 只改代码不验证启动
- 改数据库结构但不检查旧库升级路径

---

## Code Review Checklist

- [ ] 是否遵守 router / service / repository 分层边界
- [ ] 是否没有在 router 中散落事务提交与复杂查询
- [ ] 是否没有继续复制 `detail=str(e)` 这类旧错误模式
- [ ] 是否使用了正确日志级别，并避免敏感信息泄露
- [ ] 是否在消息中保留了足够上下文（user_id / project_id / chapter_number 等）
- [ ] 如果涉及模型变更，是否同步补了旧库 schema backfill
- [ ] 是否保持 API 错误响应仍围绕 `detail` 字段
- [ ] 是否至少完成了启动验证或对应链路的手动回归
