# Cross-Layer Thinking Guide

> **Purpose**: Think through data flow across layers before implementing.

---

## The Problem

这个项目有很多典型的跨层链路：

- `backend router → service → db/schema → frontend api → store → view`
- `router guard → auth store → /api/auth/users/me → 页面跳转`
- `AI 响应 → 后端解析/清洗 → schema 返回 → 前端版本选择与展示`
- `模型/字段变更 → init_db schema backfill → 旧库启动`

大多数隐蔽 bug 都发生在这些边界之间，而不是单个函数内部。

---

## Before Implementing Cross-Layer Features

### Step 1: Map the Full Flow

至少画清楚：

```text
Input → Router/View → Service/Store → API/DB → Response → Store/View
```

对本项目尤其要问：

- 字段名是否在前后端都一致？
- 这个状态值是否被 router、store、component 同时依赖？
- 错误是以 `detail` 返回，还是被某层吞掉了？
- 旧数据库是否还能启动？

### Step 2: Identify Boundaries

| Boundary | 本项目常见问题 |
|----------|---------------|
| Backend Router ↔ Service | 业务校验重复、错误码分叉 |
| Service ↔ DB | 只改 ORM 不补 schema backfill |
| Backend ↔ Frontend API | 字段名、section key、状态值不一致 |
| Store ↔ View | 一处 optimistic update，另一处仍用旧数据 |
| Router Guard ↔ Auth Store | token 有了但 user 未恢复，跳转逻辑异常 |

### Step 3: Define the Contract

在动手前至少明确：

- 输入输出字段
- 空值和失败分支
- 谁负责校验
- 谁负责日志
- 谁负责回滚或兜底

---

## High-Risk Cross-Layer Changes In This Project

### 1. 章节 / 蓝图 / section 结构调整

这类改动往往同时影响：

- 后端 schema / service / router
- 前端 `api/novel` 类型
- Pinia store
- 详情页与写作台组件

### 2. 认证与权限流调整

这类改动会同时影响：

- `/api/auth/*`
- `stores/auth.ts`
- `router/index.ts`
- 登录页 / 管理员页跳转

### 3. 数据库字段调整

这类改动不能只停留在模型；旧库兼容必须一起想。

参考：

- `backend/app/db/init_db.py:122`

### 4. AI 输出解析与展示调整

这类改动会跨越：

- 后端 JSON 清洗/解析
- HTTP 错误返回
- 前端章节版本展示与选择

参考：

- `backend/app/api/routers/novels.py:183`
- `frontend/src/components/shared/NovelDetailShell.vue:318`
- `frontend/src/views/WritingDesk.vue:200`

---

## Common Cross-Layer Mistakes

### Mistake 1: 只改一侧类型，不改另一侧消费方

**Bad**: 后端改了字段，前端 store / view 继续按旧结构读取。

### Mistake 2: 同一规则多层重复实现

**Bad**: router、service、frontend 页面各写一套权限或前置校验。

**Good**: 边界校验留在入口，业务规则收敛在 service/store 主入口。

### Mistake 3: 忘记考虑旧数据 / 旧库

**Bad**: 新字段在新库能跑，旧库启动直接报错。

### Mistake 4: 错误链路只验证 happy path

**Bad**: 只看成功返回，不检查解析失败、超时、权限失败、空数据时页面如何表现。

---

## Project-Specific Checklist

Before implementation:

- [ ] 明确这次改动影响哪些层
- [ ] 列出会受影响的字段 / 状态值 / section key / route
- [ ] 确认错误返回和日志策略是否一致
- [ ] 如果碰数据库，确认旧库 backfill 怎么做
- [ ] 如果碰 auth / router，确认恢复登录态和重定向是否仍成立

After implementation:

- [ ] 验证成功路径
- [ ] 验证失败路径
- [ ] 验证页面展示是否与 store 数据一致
- [ ] 验证是否漏改前端或后端任一侧
- [ ] 验证旧库或已有数据是否仍可工作

---

## Core Reminder

这个项目最危险的改动不是“函数写错”，而是“链路只改了一半”。凡是跨 router/store/service/schema 的改动，都先按链路检查一遍。
