# Database Guidelines

> Database patterns and conventions for this project.

---

## Overview

当前项目使用 SQLAlchemy 2.x 异步 ORM，数据库会话由 `backend/app/db/session.py` 统一提供，业务代码普遍通过 `AsyncSession` 注入到 service / repository。

现状不是 Alembic 迁移流，而是“启动时自愈初始化”模式：

- `Base.metadata.create_all()` 创建缺失表
- `init_db()` 做默认管理员、系统配置、提示词预载
- `_ensure_schema_updates()` 通过 `inspect + ALTER TABLE` 给旧库补列

对应代码：

- `backend/app/db/session.py:8`
- `backend/app/db/init_db.py:23`
- `backend/app/db/init_db.py:122`

---

## Query Patterns

### 1. 默认使用 AsyncSession + select

Good example:

- `backend/app/repositories/base.py:18`
- `backend/app/repositories/user_repository.py:13`
- `backend/app/services/novel_service.py:166`

模式包括：

- `await session.execute(select(...))`
- `result.scalars().first()` / `.all()` / `scalar_one()`
- 需要关系数据时显式 `.options(selectinload(...))`

### 2. 简单 CRUD 走 repository，复杂聚合可在 service 中直写 SQLAlchemy

这是当前代码的真实做法，不是强制所有查询都经过 repository。

Good example:

- 单表查询：`backend/app/repositories/user_repository.py:13`
- 复杂聚合与批量操作：`backend/app/services/novel_service.py:166`、`backend/app/services/novel_service.py:310`

Bad example:

- 不要为了“形式统一”把复杂业务 SQL 硬塞进通用 BaseRepository。
- 不要在 router 中散落查询语句；应收敛到 service 或 repository。

### 3. 写操作由 service 显式控制事务边界

当前代码习惯是 service 在一个业务动作末尾执行 `commit()`，必要时 `refresh()`。

Good example:

- `backend/app/services/auth_service.py:77`
- `backend/app/services/novel_service.py:132`
- `backend/app/services/novel_service.py:289`
- `backend/app/services/novel_service.py:356`

Bad example:

- 不要在 router 里一边改数据一边 `session.commit()`。
- 不要把 commit 分散到多个 helper 中，导致事务边界不清晰。

### 4. 关系加载要显式

当接口需要章节版本、评审、选中版本等关联数据时，项目使用 `selectinload` 明确声明。

Good example:

- `backend/app/services/novel_service.py:166`

Bad example:

- 不要依赖隐式懒加载来赌异步上下文仍可用。

---

## Migrations

### 当前真实模式

项目目前没有看到独立 migration 目录或 Alembic 工作流，数据库变更主要靠 `init_db()` 在应用启动时完成。

规则：

1. 新表 / 新模型：放到 `models/`，并确保被 metadata 收集
2. 新默认配置：加到 `backend/app/db/system_config_defaults.py`
3. 给旧库补列：在 `backend/app/db/init_db.py:_ensure_schema_updates()` 中添加兼容逻辑
4. 启动时必须幂等，重复执行不能报错

Good example:

- `backend/app/db/init_db.py:129`
- `backend/app/db/init_db.py:147`

Bad example:

- 不要只改模型不补旧库；这会让已有 SQLite / MySQL 库启动时报错。
- 不要写非幂等 DDL。

---

## Naming Conventions

从现有模型可见：

- 表名以复数 snake_case 为主，如 `users`、`chapter_outlines`、`chapters`
- 模型类使用 PascalCase，如 `User`
- 字段名使用 snake_case，如 `hashed_password`、`is_admin`、`updated_at`
- 布尔字段常以 `is_` / `allow_` / `enable_` 开头
- 系统配置键使用点分隔命名，如 `smtp.server`、`linuxdo.client_id`

Good example:

- `backend/app/models/user.py:13`
- `backend/app/db/init_db.py:18`

Bad example:

- 不要在数据库字段中混用 camelCase。
- 不要为系统配置键发明不一致的层级格式。

---

## Common Mistakes

### Bad example: 只改 ORM 不做旧库兼容

如果新增列只改 `models/`，旧数据库不会自动补齐。正确做法是同步更新 `init_db.py` 的 schema backfill。

### Bad example: 在 repository 里提交事务

当前项目把事务边界放在 service。repository 负责数据访问，不负责决定什么时候提交。

### Bad example: 返回未序列化的 ORM 关系对象

前端消费的是 schema 合约，不应直接暴露 ORM 内部结构。
