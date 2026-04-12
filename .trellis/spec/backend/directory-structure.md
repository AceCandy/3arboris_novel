# Directory Structure

> How backend code is organized in this project.

---

## Overview

后端是一个典型的 FastAPI + SQLAlchemy Async 分层应用，代码主入口在 `backend/app/main.py`。

核心分层是：

- `api/routers/`：HTTP 路由层，当前主要处理入参与响应边界
- `core/`：配置、认证、安全、依赖注入
- `db/`：数据库基类、会话工厂、启动初始化
- `models/`：SQLAlchemy ORM 模型
- `repositories/`：单表或单聚合的数据访问
- `services/`：业务编排与跨仓储逻辑
- `schemas/`：Pydantic 请求 / 响应模型

这套结构在 `backend/app/api/routers/__init__.py`、`backend/app/core/dependencies.py`、`backend/app/services/auth_service.py`、`backend/app/services/novel_service.py` 中都能看到一致用法。

---

## Directory Layout

```text
backend/
└── app/
    ├── main.py                  # FastAPI 应用装配、日志配置、CORS、lifespan
    ├── api/
    │   └── routers/             # 按领域拆分路由模块，统一在 __init__.py 注册
    ├── core/                    # settings、security、dependencies
    ├── db/                      # Base、session、init_db、默认系统配置
    ├── models/                  # SQLAlchemy 模型
    ├── repositories/            # Repository 模式封装查询
    ├── schemas/                 # Pydantic schema
    ├── services/                # 业务服务层
    ├── tasks/                   # 异步任务 / 后台任务
    ├── prompts/                 # 默认提示词资源（由 init_db 预载）
    └── utils/                   # 少量工具函数
```

---

## Module Organization

### 1. 当前项目中的路由层主要做这些事

- 依赖注入：`Depends(get_session)`、`Depends(get_current_user)`
- 调用 service
- 记录请求级日志
- 抛出或透传 `HTTPException`

Good example:

- `backend/app/api/routers/auth.py:22`
- `backend/app/api/routers/novels.py:57`
- `backend/app/api/routers/admin.py:67`

Bad example:

- 不要在 router 里直接写大量 SQLAlchemy 查询或跨多表事务。
- 不要把长链路业务编排塞进 endpoint；这类逻辑应放到 `services/`。

### 2. service 层承接业务编排

service 负责：

- 权限 / 业务前置校验
- 聚合多个 repository / model 操作
- 提交事务
- 将 ORM 结果转换为 schema 所需结构

Good example:

- `backend/app/services/auth_service.py:43` 处理认证、注册、邮件发送
- `backend/app/services/novel_service.py:124` 处理项目创建、所有权校验、蓝图替换、章节聚合

Bad example:

- 不要把 service 退化成“每个方法只包一层 repo”；如果没有业务价值，不需要额外抽象。
- 不要在 service 里感知 FastAPI request/response 对象。

### 3. repository 层只处理数据访问

repository 模式已经存在，基类在 `backend/app/repositories/base.py:10`。

Good example:

- `backend/app/repositories/base.py:18` 提供 `get/list/add/delete/update_fields`
- `backend/app/repositories/user_repository.py:13` 用专门方法封装用户查询

Bad example:

- 不要在 repository 中写 HTTPException。
- 不要在 repository 中混入权限判断、提示词拼装、外部 API 调用。

### 4. schema 和 model 分离

- `models/` 对应数据库落库结构
- `schemas/` 对应 API 合约
- 返回给前端时优先返回 schema，而不是裸 ORM 对象

Good example:

- `backend/app/api/routers/auth.py:39`
- `backend/app/api/routers/admin.py:80`

Bad example:

- 不要把数据库内部字段、懒加载关系直接暴露给前端。

---

## Naming Conventions

- 目录按职责命名：`api`, `services`, `repositories`, `schemas`
- router 文件按领域命名：`auth.py`, `novels.py`, `writer.py`, `admin.py`
- repository 文件使用 `<domain>_repository.py`
- service 文件使用 `<domain>_service.py`
- ORM 模型类使用 PascalCase，表名通常显式声明；基类默认会把类名转小写，见 `backend/app/db/base.py:4`

---

## Examples

### 推荐参考

- 应用装配：`backend/app/main.py:17`
- 路由注册：`backend/app/api/routers/__init__.py:4`
- 依赖注入：`backend/app/core/dependencies.py:14`
- 仓储基类：`backend/app/repositories/base.py:10`
- 业务聚合：`backend/app/services/novel_service.py:112`
- 数据库初始化：`backend/app/db/init_db.py:23`

### 新功能落位规则

- 新 HTTP 接口：先加 `schemas/`，再加 `services/`，最后在 `api/routers/` 暴露 endpoint
- 新数据库实体：加到 `models/`，必要时补 repository 和 service
- 新跨领域流程：优先放 `services/`，不要直接堆在 router
