# Type Safety

> Type safety patterns in this project.

---

## Overview

前端使用 TypeScript，核心类型主要分布在组件局部、store 内部以及 `api/` 请求模块中。当前真实模式不是“所有类型集中到一个 types/ 目录”，而是更接近“就近声明 + API 模块导出领域类型”。

参考：

- `frontend/src/views/WritingDesk.vue:111`
- `frontend/src/stores/novel.ts:4`
- `frontend/src/stores/auth.ts:7`
- `frontend/package.json:11`

---

## Type Organization

### 1. API 相关领域类型优先从 `api/` 导入

Good example:

- `frontend/src/stores/novel.ts:4` 从 `@/api/novel` 导入 `NovelProject`、`ChapterOutline` 等类型
- `frontend/src/components/shared/NovelDetailShell.vue:241` 从 `@/api/novel` 导入 section 类型

### 2. 仅本组件使用的 props / 局部结构就近声明 interface

Good example:

- `frontend/src/views/WritingDesk.vue:122`
- `frontend/src/components/CustomAlert.vue:127`
- `frontend/src/stores/auth.ts:7`

Bad example:

- 不要把只在单文件使用的小 interface 提前抽到全局公共类型文件。
- 不要为了“统一”把完全无复用价值的局部类型集中搬运。

---

## Validation

当前前端没有看到 Zod / Yup 之类运行时校验库；真实做法是：

- 依赖后端 API 合约
- 在前端用 TypeScript 约束静态类型
- 在少数地方用显式条件判断处理空值或响应异常

Good example:

- `frontend/src/stores/auth.ts:135` 对登录响应中的 `access_token` 做显式检查
- `frontend/src/stores/novel.ts:68` / `117` / `133` 对缺少 `currentProject` 的情况直接抛错

Bad example:

- 不要假设所有后端返回都完整可用而完全不做边界判断。
- 也不要在每一层重复实现同一份 runtime schema 校验，当前项目没有这套体系。

---

## Common Patterns

### 1. `script setup` 中用 interface 定义 props

Good example:

- `frontend/src/views/WritingDesk.vue:122`
- `frontend/src/components/shared/NovelDetailShell.vue:253`

### 2. store 内使用显式联合或可空类型

Good example:

- `frontend/src/stores/novel.ts:10` `NovelProject | null`
- `frontend/src/stores/novel.ts:13` `string | null`
- `frontend/src/stores/auth.ts:83` `string | null`

### 3. computed / filter 中使用类型守卫式写法

Good example:

- `frontend/src/components/shared/NovelDetailShell.vue:341` `filter((item): item is ChapterVersion => item !== null)`

---

## Forbidden Patterns

### Bad example: 滥用 `any`

当前代码里已有少量 `any`，如 `currentConversationState = ref<any>({})`、某些 section/map 结构，这反映现状，但新代码不应继续扩大 `any` 的使用面。

参考：

- `frontend/src/stores/novel.ts:11`
- `frontend/src/components/shared/NovelDetailShell.vue:281`

### Bad example: 不必要的类型断言覆盖真实问题

像 `as string`、`as Record<string, unknown>` 只应在边界处用于缩窄，不要用来掩盖结构不清的状态设计。

Good example:

- `frontend/src/components/shared/NovelDetailShell.vue:267` 路由参数转字符串
- `frontend/src/components/shared/NovelDetailShell.vue:303` JSON 解析后做受控断言

Bad example:

- 不要用 `as any` 快速绕过编译错误。
- 不要在未验证空值前直接断言非空。
