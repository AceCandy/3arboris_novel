# State Management

> How state is managed in this project.

---

## Overview

项目当前使用 Pinia 作为全局状态管理，配合组件本地 `ref/computed` 处理页面交互态。

真实模式：

- 跨页面认证、项目实体状态放进 store
- 短生命周期 UI 状态留在组件本地
- 服务端数据没有单独引入 React Query / Vue Query，主要靠 store action 和页面级加载逻辑维护
- 某些更新采用 optimistic update + rollback

参考：

- `frontend/src/main.ts:17`
- `frontend/src/stores/auth.ts:81`
- `frontend/src/stores/novel.ts:7`
- `frontend/src/views/WritingDesk.vue:131`

---

## State Categories

### 1. Global state

适合放 Pinia：

- token / 当前用户
- 认证开关
- 当前项目、项目列表
- 当前会话上下文
- 全局业务错误

Good example:

- `frontend/src/stores/auth.ts:82`
- `frontend/src/stores/novel.ts:8`

### 2. Local page state

适合留在组件：

- modal 开关
- 当前选中的章节
- sidebar 是否展开
- 局部 loading
- 当前 section / 当前 tab

Good example:

- `frontend/src/views/WritingDesk.vue:131`
- `frontend/src/components/shared/NovelDetailShell.vue:363`

### 3. Global UI utility state

少量跨页面 UI 状态可由 composable 的模块级变量持有。

Good example:

- `frontend/src/composables/useAlert.ts:18`

---

## When to Use Global State

满足以下条件时再放进 store：

- 多个页面都要读写
- 刷新路由后仍需保留或恢复
- 与认证/项目主实体强相关
- 请求结果会被多个组件消费

Good example:

- `frontend/src/stores/auth.ts:83` token 从 `localStorage` 恢复
- `frontend/src/stores/novel.ts:55` 当前项目加载后供页面多个区域共享

Bad example:

- 不要把 `showModal`、`selectedVersionIndex` 这类页面瞬时状态提升到全局。

---

## Server State

项目当前没有独立缓存层，服务端数据同步主要依赖以下模式：

1. store action 发请求并写回状态
2. 页面级请求按 section 懒加载
3. 局部更新时直接补丁当前 store 数据
4. 失败时回滚 optimistic update

Good example:

- `frontend/src/stores/novel.ts:21` 加载项目列表
- `frontend/src/stores/novel.ts:49` 加载单个项目
- `frontend/src/components/shared/NovelDetailShell.vue:414` section 懒加载
- `frontend/src/stores/novel.ts:276` 编辑章节内容时先本地更新，再失败回滚

Bad example:

- 不要同一接口一会儿写回 store，一会儿只改本地副本，导致状态分叉。
- 不要在多个组件各自重复请求同一份主数据而不共享结果。

---

## Common Mistakes

### Bad example: 全局 loading 与局部 loading 不分

当前代码已经区分：有些操作不占用全局 `isLoading`，而由页面自己维护局部加载态。新增逻辑时应沿用这个边界。

Good example:

- `frontend/src/stores/novel.ts:148`
- `frontend/src/stores/novel.ts:179`

### Bad example: optimistic update 不做失败回滚

如果先改本地再发请求，失败时必须恢复之前内容。

Good example:

- `frontend/src/stores/novel.ts:317`

### Bad example: 在 store 外再维护另一份主实体真相

`currentProject` 这类核心实体应尽量单点更新，避免页面缓存旧副本导致 UI 不一致。
