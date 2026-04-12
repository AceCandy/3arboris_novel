# Logging Guidelines

> How logging is done in this project.

---

## Overview

项目使用 Python `logging` 标准库，入口在 `backend/app/main.py` 通过 `dictConfig(...)` 配置控制台日志。

当前真实模式：

- 统一 console handler
- 日志格式：`%(asctime)s [%(levelname)s] %(name)s - %(message)s`
- 模块内普遍使用 `logger = logging.getLogger(__name__)`
- 路由层和初始化逻辑日志覆盖较多，service 层按关键节点记录

参考：

- `backend/app/main.py:17`
- `backend/app/api/routers/auth.py:17`
- `backend/app/api/routers/novels.py:29`
- `backend/app/db/init_db.py:17`

---

## Log Levels

### info

用于记录正常业务动作和关键状态切换。

Good example:

- `backend/app/api/routers/auth.py:52` 用户登录成功
- `backend/app/api/routers/novels.py:67` 用户创建项目
- `backend/app/db/init_db.py:32` 数据库初始化完成

### warning

用于记录可恢复但值得关注的问题。

Good example:

- `backend/app/api/routers/auth.py:65` 未启用 Linux.do 登录
- `backend/app/api/routers/novels.py:230` 缺少对话历史
- `backend/app/db/init_db.py:39` 未检测到管理员账号

### error

用于记录已知失败，但不一定需要堆栈。

Good example:

- `backend/app/api/routers/auth.py:71` 配置缺失

### exception

用于 `except` 分支，需要保留堆栈时。

Good example:

- `backend/app/api/routers/novels.py:188`
- `backend/app/db/init_db.py:53`
- `backend/app/tasks/foreshadowing_tasks.py:193`

---

## Structured Logging

当前项目不是严格 JSON structured logging，但已经有一些“半结构化”约定：

- message 中带关键实体 ID / user_id / project_id / chapter_number
- 少量地方使用 `extra={...}` 补充上下文

Good example:

- `backend/app/api/routers/novels.py:159` 在消息中包含 `project_id`、`user_id`
- `backend/app/services/auth_service.py:149` 用 `extra` 记录原始发件地址
- `backend/app/services/auth_service.py:248` 用 `extra` 记录邮件目标与服务端口

推荐沿用：

- 日志正文至少包含操作对象和主键
- 同一类操作使用稳定文案，便于 grep

Bad example:

- 只写“失败了”“出错了”而不带上下文
- 同一动作在不同模块用完全不同措辞，难以检索

---

## What to Log

应记录：

- 认证、授权、管理员操作
- 资源创建 / 更新 / 删除
- 启动初始化、自愈迁移、默认数据写入
- AI / 外部系统调用失败
- 长链路关键阶段开始 / 完成 / 失败

Good example:

- `backend/app/api/routers/admin.py:76`
- `backend/app/api/routers/novels.py:205`
- `backend/app/db/init_db.py:58`

---

## What NOT to Log

不要记录：

- 明文密码、token、API key
- 完整邮箱验证码
- 大段模型响应全文（必要时最多截断）
- 用户私密正文的完整内容

Good example:

- `backend/app/api/routers/novels.py:193` 对 LLM 原始响应做了 `[:1000]` 截断

Bad example:

- 在 `info` 日志里打印完整请求体、完整邮件内容、完整章节正文
- 把 `Authorization`、`smtp.password`、`client_secret` 写进日志
