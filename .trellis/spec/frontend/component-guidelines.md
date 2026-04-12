# Component Guidelines

> How components are built in this project.

---

## Overview

项目当前以 Vue 3 SFC 为主，普遍使用 `<script setup lang="ts">`、组合式 API、显式 props / emits，以及按页面域拆分组件。

真实模式包括：

- 页面层负责编排，复杂 UI 继续拆成子组件
- 组件通过 `defineProps` / `withDefaults` / `defineEmits` 定义接口
- 样式主要依赖全局 class 与 Material 3 / Tailwind 风格 class 组合
- 弹窗类组件常配合 `Teleport`、transition、显式事件回传

参考：

- `frontend/src/components/CustomAlert.vue:124`
- `frontend/src/components/shared/NovelDetailShell.vue:253`
- `frontend/src/views/WritingDesk.vue:122`

---

## Component Structure

### 1. 默认使用 SFC + script setup + TypeScript

Good example:

- `frontend/src/components/CustomAlert.vue:124`
- `frontend/src/components/shared/NovelDetailShell.vue:235`
- `frontend/src/views/NovelDetail.vue:6`

当前常见结构：

1. `<template>`
2. `<script setup lang="ts">`
3. 局部 interface / computed / methods
4. 需要时再加 `<style>`，很多组件直接复用全局样式类

Bad example:

- 不要为新组件回退到 Options API，除非周边文件已经都是该模式。
- 不要把大量模板内联逻辑塞在 `template` 表达式里而不提到 computed / method。

### 2. 页面组件负责编排，子组件负责块级展示

Good example:

- `frontend/src/views/WritingDesk.vue:113` 页面直接组合 `WDHeader`、`WDSidebar`、`WDWorkspace`、多个 modal
- `frontend/src/components/shared/NovelDetailShell.vue:243` 壳组件统一装配各个 section 组件

Bad example:

- 不要把所有章节区块、弹窗、工具栏都写在一个超大共享组件里。
- 不要在多个页面复制相同结构而不抽组件。

---

## Props Conventions

### 1. props 用 TypeScript interface 明确声明

Good example:

- `frontend/src/views/WritingDesk.vue:122`
- `frontend/src/components/CustomAlert.vue:127`
- `frontend/src/components/shared/NovelDetailShell.vue:253`

### 2. 有默认值时使用 withDefaults

Good example:

- `frontend/src/components/CustomAlert.vue:137`
- `frontend/src/components/shared/NovelDetailShell.vue:259`

### 3. 组件事件通过 defineEmits 显式列出

Good example:

- `frontend/src/components/CustomAlert.vue:145`

Bad example:

- 不要用隐式约定事件名而不声明。
- 不要把过多无语义布尔 props 堆给组件，优先保持接口直接可读。

---

## Styling Patterns

当前项目不是 CSS Modules，也不是 scoped-first 风格，真实模式是：

- 大量复用全局 class，如 `md-btn`、`md-card`、`md-dialog`
- 同时搭配 Tailwind 风格 utility class，如 `flex`, `w-full`, `px-4`
- 少量场景使用 `:style` 绑定 CSS 变量

Good example:

- `frontend/src/components/CustomAlert.vue:21`
- `frontend/src/components/shared/NovelDetailShell.vue:121`
- `frontend/src/views/WritingDesk.vue:3`

Bad example:

- 不要在新组件里随意引入另一套完全不同的样式范式。
- 不要把重复出现的视觉结构全写成长串内联 `style` 而不复用现有 class。

---

## Accessibility

当前代码已有一些基础可访问性模式，但不是全量严格体系。

推荐沿用已有做法：

- 交互元素优先用 `<button>` 而不是可点击 `<div>`
- modal / overlay 组件为关闭行为提供明确点击区
- 图标按钮补 `aria-label`

Good example:

- `frontend/src/components/shared/NovelDetailShell.vue:8` 菜单按钮带 `aria-label`
- `frontend/src/components/CustomAlert.vue:12` overlay 通过 `@click.self` 关闭

Bad example:

- 不要用纯 `div` 模拟按钮。
- 不要新增只有图标、没有文本也没有 `aria-label` 的点击控件。

---

## Common Mistakes

### Bad example: 页面和组件同时管理同一份业务状态

项目当前把项目数据收敛在 Pinia store，本地组件只维护页面交互态。不要再复制一份业务实体到多个组件里各自修改。

### Bad example: 组件接口不显式声明

`defineProps` / `defineEmits` 已经是当前主流模式，新组件不应靠注释或调用方猜测接口。

### Bad example: 为一次性逻辑抽过度通用组件

如果 UI 只在一个页面里使用，优先按该页面域命名和放置，不要提前抽成模糊的“万能组件”。
