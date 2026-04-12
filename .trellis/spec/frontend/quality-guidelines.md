# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

当前前端质量基线以 TypeScript 类型检查、Vite 构建通过、现有页面模式一致性为主。`frontend/package.json` 里可以看到 `build`、`type-check`、`format`，但暂时没有独立 test 脚本，因此项目当前更依赖人工回归与编译检查。

参考：

- `frontend/package.json:9`
- `frontend/src/router/index.ts:79`
- `frontend/src/stores/novel.ts:276`
- `frontend/src/components/shared/NovelDetailShell.vue:414`

---

## Forbidden Patterns

### 1. 页面、store、API 重复维护同一份主数据

Bad example:

- 多处各自缓存 `currentProject` 副本并分别修改，容易让章节内容、章节状态、section 数据分叉。

### 2. 在多个位置重复实现相同请求/权限逻辑

Bad example:

- 登录恢复逻辑已集中在路由守卫和 auth store，新增页面不要再自己复制一套 token 检查。

参考：

- `frontend/src/router/index.ts:79`
- `frontend/src/stores/auth.ts:177`

### 3. optimistic update 不回滚

Bad example:

- 先改界面再发请求，但失败后不恢复旧值。

参考：

- `frontend/src/stores/novel.ts:317`

### 4. 用 `as any` 或过度断言绕过错误

这会让现有 TypeScript 基线失效。

---

## Current Baseline Patterns

### 1. 当前仓库中，新增前端改动通常至少通过 type-check / build 之一验证

当前仓库已有明确脚本：

- `npm run type-check`
- `npm run build`

参考：

- `frontend/package.json:11`

### 2. 路由级权限依然走统一守卫

Good example:

- `frontend/src/router/index.ts:91`

### 3. 跨页面业务状态优先进入 Pinia

Good example:

- `frontend/src/stores/auth.ts:81`
- `frontend/src/stores/novel.ts:7`

### 4. 页面局部交互态留在组件内

Good example:

- `frontend/src/views/WritingDesk.vue:131`
- `frontend/src/components/shared/NovelDetailShell.vue:363`

---

## Testing Requirements

项目当前没看到独立单元测试/组件测试脚本，因此真实最低要求应记录为：

1. 前端改动后至少运行 `type-check` 或 `build`
2. 涉及路由、权限、章节生成、编辑回滚、section 加载时做人工回归
3. 如果改动影响 auth / store / API 交互，至少验证一次真实页面流程

重点回归场景：

- 登录 / 恢复登录态
- 管理员路由跳转
- 小说详情页 section 切换
- 写作台章节编辑、版本选择、失败提示

Bad example:

- 只改通过编译，不验证关键交互路径。
- 修改 store / router 后完全不检查实际导航和页面状态。

---

## Code Review Checklist

- [ ] 是否沿用了 `views` / `components` / `stores` / `api` 的现有分层
- [ ] 是否避免把一次性页面状态塞进 Pinia
- [ ] 是否复用了现有请求入口、全局提示、共享壳组件模式
- [ ] 是否保持 props / emits / 类型声明清晰
- [ ] 是否没有扩大 `any`、`as any` 的使用范围
- [ ] 是否检查了权限守卫、错误提示、loading 状态是否仍正确
- [ ] 是否至少通过 `type-check` 或 `build`
