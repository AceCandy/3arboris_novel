# Hook Guidelines

> How hooks are used in this project.

---

## Overview

当前前端并不是 React hooks 体系，而是 Vue composables。项目里 `composables/` 使用量不多，只有在逻辑确实需要跨组件复用时才抽出来。

真实模式：

- 组合式 API 是默认写法
- 全局共享交互逻辑可以放到 composable
- 数据获取多数仍在 store 或页面中完成，而不是统一塞进 composable

参考：

- `frontend/src/composables/useAlert.ts:18`
- `frontend/src/views/WritingDesk.vue:112`
- `frontend/src/stores/auth.ts:95`

---

## Custom Hook Patterns

### 1. composable 用于复用状态型 UI 逻辑

Good example:

- `frontend/src/composables/useAlert.ts:18` 用模块级 `alerts` 维护全局提示队列
- `frontend/src/composables/useAlert.ts:85` 对外暴露 `useAlert()` 简化调用

### 2. 全局能力可同时暴露对象和 composable

当前 `useAlert.ts` 同时导出：

- `globalAlert`：给页面直接调用完整能力
- `useAlert()`：给组件按 composable 方式取用

Good example:

- `frontend/src/composables/useAlert.ts:76`
- `frontend/src/composables/useAlert.ts:85`

Bad example:

- 不要为了单个页面私有逻辑就新建 composable 文件。
- 不要把一次性按钮点击逻辑抽到 `composables/` 里增加跳转成本。

---

## Data Fetching

当前项目的数据获取主力不在 composable，而是：

- 认证与会话恢复：`stores/auth.ts`
- 小说项目与章节数据：`stores/novel.ts`
- 页面级 section 拉取：`views/` 内直接调 API

Good example:

- `frontend/src/stores/auth.ts:177` `fetchUser` 放在 auth store
- `frontend/src/stores/novel.ts:21` `loadProjects` 放在 novel store
- `frontend/src/components/shared/NovelDetailShell.vue:414` 页面壳按 section 懒加载

Bad example:

- 不要默认把所有 fetch 都改造成 composable。
- 不要在 composable、store、页面三处重复实现同一请求流程。

---

## Naming Conventions

- composable 文件使用 `use*.ts`
- 导出函数名与文件名保持一致：`useAlert`
- 若同时提供全局对象，名称应体现用途：`globalAlert`

Good example:

- `frontend/src/composables/useAlert.ts:76`
- `frontend/src/composables/useAlert.ts:85`

Bad example:

- 不要创建没有 `use` 前缀的组合式状态文件。
- 不要把纯常量文件、纯 API 文件放进 `composables/`。

---

## Common Mistakes

### Bad example: 把 store 能解决的问题再包一层 composable

当前项目已经有 Pinia；跨页面业务状态优先进 store，不要重复抽一层 `useNovelData` 之类包装。

### Bad example: composable 中混入过多页面专属 DOM 细节

只有明确复用的 DOM 交互逻辑才适合抽离，否则应留在页面组件内。
