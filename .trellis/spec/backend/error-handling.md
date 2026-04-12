# Error Handling

> How errors are handled in this project.

---

## Overview

当前项目以后端主动抛出 `HTTPException` 为主，没有统一的全局异常包装器。常见做法是：

- 权限、资源不存在、参数不合法：直接抛 `HTTPException`
- 可预期业务错误：在 service 或 router 中转换为具体状态码
- 非预期异常：先 `logger.exception(...)`，再抛 500

对应代码：

- `backend/app/core/dependencies.py:14`
- `backend/app/services/auth_service.py:43`
- `backend/app/services/novel_service.py:137`
- `backend/app/api/routers/novels.py:183`

---

## Error Types

### 1. HTTPException 是事实标准

项目当前没有自定义领域异常体系，`HTTPException` 就是主要边界异常类型。

Good example:

- 认证失败：`backend/app/services/auth_service.py:46`
- 权限不足：`backend/app/core/dependencies.py:33`
- 资源不存在：`backend/app/services/novel_service.py:140`
- 业务前置条件不足：`backend/app/api/routers/novels.py:231`

### 2. ValueError 只在内部短距离使用，随后转换成 HTTPException

Good example:

- `backend/app/api/routers/admin.py:96`
- `backend/app/api/routers/admin.py:123`
- `backend/app/api/routers/admin.py:140`

Bad example:

- 不要把原始 `ValueError` 直接冒到 FastAPI 最外层。

---

## Error Handling Patterns

### 1. 能提前判断的业务错误，直接抛明确状态码

Good example:

- `404`：资源不存在
- `403`：无权限
- `400`：缺少前置数据或格式不满足业务要求
- `401`：认证失败

参考：

- `backend/app/services/novel_service.py:137`
- `backend/app/services/auth_service.py:43`
- `backend/app/api/routers/novels.py:229`

### 2. 对外部系统 / AI 结果 / 复杂解析使用 try/except + logger.exception

Good example:

- `backend/app/api/routers/novels.py:183` 解析 LLM JSON 失败时记录原始上下文，再返回 500
- `backend/app/db/init_db.py:48` 初始化默认管理员失败时记录异常

### 3. 错误信息尽量给用户可操作提示，但不要暴露内部栈

Good example:

- `backend/app/api/routers/novels.py:197`
- `backend/app/services/auth_service.py:98`

Bad example:

- `raise HTTPException(status_code=500, detail=str(e))` 这种模式在部分旧代码里仍然存在，如 `backend/app/api/routers/foreshadowing.py`；新规范不应继续复制。

---

## API Error Responses

项目当前直接依赖 FastAPI 默认错误响应格式：

```json
{
  "detail": "错误说明"
}
```

前后端已经围绕 `detail` 字段工作，因此新增接口也应保持一致。

Good example:

- `backend/app/services/auth_service.py:46`
- `backend/app/core/dependencies.py:23`

Bad example:

- 不要自造 `{ message, error, code }` 这类局部格式，除非整个项目统一升级。

---

## Common Mistakes

### Bad example: 捕获异常后直接 `detail=str(e)`

这会把底层实现细节、第三方报错甚至敏感路径暴露给前端。只有 4xx 的显式业务错误才适合直接展示。

### Bad example: 记录 error 但丢失堆栈

如果进入 `except Exception` 分支，优先使用 `logger.exception(...)`，不要只写 `logger.error(str(e))`。

### Bad example: router 和 service 同时重复校验同一条件

边界校验保留在入口层，业务规则放在 service，避免双重实现导致分叉。
