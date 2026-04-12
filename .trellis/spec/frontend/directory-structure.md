# Directory Structure

> How frontend code is organized in this project.

---

## Overview

前端是 Vue 3 + TypeScript + Pinia + Vue Router + Vite 的单页应用，入口在 `frontend/src/main.ts`。

当前真实组织方式是：

- `views/`：路由级页面组件
- `components/`：可复用 UI 组件，按领域子目录拆分
- `stores/`：Pinia 全局状态
- `api/`：前端请求封装与类型定义
- `composables/`：少量跨组件状态逻辑
- `router/`：集中式路由与导航守卫
- `utils/`：纯工具函数
- `assets/`：全局样式与静态资源

参考：

- `frontend/src/main.ts:16`
- `frontend/src/router/index.ts:12`
- `frontend/src/stores/novel.ts:7`
- `frontend/src/components/shared/NovelDetailShell.vue:235`

---

## Directory Layout

```text
frontend/
└── src/
    ├── main.ts                 # 应用入口，注册 Pinia / Router
    ├── router/                 # 路由表与 beforeEach 守卫
    ├── api/                    # API 调用与请求/响应类型
    ├── stores/                 # Pinia stores
    ├── composables/            # useAlert 等组合式逻辑
    ├── components/             # 共享组件与领域组件
    │   ├── shared/             # 跨页面共享容器/壳组件
    │   ├── novel-detail/       # 小说详情页 section 组件
    │   └── writing-desk/       # 写作台拆分组件
    ├── views/                  # 路由页面
    ├── utils/                  # 日期等工具函数
    └── assets/                 # 全局 CSS 与资源
```

---

## Module Organization

### 1. views 是路由入口，不是所有逻辑都堆在这里

页面组件通常负责：

- 读取 route params
- 组合 store / API / composable
- 管理页面级 loading、modal、section 切换
- 把具体展示拆给 `components/`

Good example:

- `frontend/src/views/NovelDetail.vue:2` 只包装共享壳组件
- `frontend/src/views/WritingDesk.vue:107` 作为页面编排层，组合多个 `WD*` 子组件

Bad example:

- 不要为每个小块 UI 都新建一个 `views/*` 页面文件。
- 不要把可复用 section 直接硬编码在多个页面里。

### 2. components 按共享范围和领域拆分

当前代码不是按“原子设计”分层，而是按功能域和复用边界拆：

- 通用弹窗/提示：根级 `components/`
- 页面壳与共享容器：`components/shared/`
- 详情页子模块：`components/novel-detail/`
- 写作台子模块：`components/writing-desk/`

Good example:

- `frontend/src/components/shared/NovelDetailShell.vue:1`
- `frontend/src/components/CustomAlert.vue:1`

Bad example:

- 不要把只服务于写作台的组件塞到 `shared/`。
- 不要在多个页面复制 sidebar / modal 结构而不抽成组件。

### 3. store 负责跨页面业务状态

`stores/` 里保存项目、认证等跨页面状态；页面内部 modal 开关、当前 tab、局部 loading 仍留在组件本地。

Good example:

- `frontend/src/stores/auth.ts:81`
- `frontend/src/stores/novel.ts:7`

Bad example:

- 不要把一次性弹窗开关、hover 状态塞进 Pinia。

### 4. 路由集中在单一入口维护

项目当前所有主路由都收敛在 `frontend/src/router/index.ts`，守卫也在同一文件。

Good example:

- `frontend/src/router/index.ts:14`
- `frontend/src/router/index.ts:79`

Bad example:

- 不要把权限判断散落到每个页面的 `onMounted`。
- 不要为单个页面单独维护一套路由配置副本。

---

## Naming Conventions

- 页面文件使用 PascalCase：`WritingDesk.vue`、`SettingsView.vue`
- 组件文件使用 PascalCase
- 同一页面下的子组件会带领域前缀：`WDHeader.vue`、`WDWorkspace.vue`
- composable 使用 `use*` 命名：`useAlert.ts`
- store 文件用领域名：`auth.ts`、`novel.ts`
- 共享容器组件常用语义化命名：`NovelDetailShell.vue`

Bad example:

- 不要在组件文件名中混用 snake_case。
- 不要给只在单页面使用的组件起过度泛化名称如 `CommonPanel.vue`。

---

## Examples

### 推荐参考

- 应用入口：`frontend/src/main.ts:16`
- 路由守卫：`frontend/src/router/index.ts:79`
- 页面编排：`frontend/src/views/WritingDesk.vue:107`
- 共享页面壳：`frontend/src/components/shared/NovelDetailShell.vue:235`
- 全局状态：`frontend/src/stores/novel.ts:7`
- 全局提示：`frontend/src/composables/useAlert.ts:18`

### 新功能落位规则

- 新路由页面：加到 `views/`，并在 `router/index.ts` 注册
- 新共享业务组件：优先放 `components/<domain>/`
- 新全局业务状态：放 `stores/`
- 新请求封装：放 `api/`
- 新跨组件状态逻辑：仅在复用明确时放 `composables/`
