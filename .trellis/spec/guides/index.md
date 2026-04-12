# Thinking Guides

> **Purpose**: Expand your thinking to catch things you might not have considered.

---

## Why Thinking Guides?

这个项目的主要风险不在语法层，而在：

- 前后端接口字段、状态流和章节结构在多层之间漂移
- 页面、store、API、service 各自维护一份“看起来差不多”的逻辑
- 数据库模型变更后忘记补旧库兼容
- AI 返回格式不稳定，解析和展示边界出错

所以思考指南在本项目里尤其适合用于：

- 跨层功能改动
- 共享逻辑抽取
- schema / API / store 结构调整
- AI 生成链路与章节流转改动

---

## Available Guides

| Guide | Purpose | When to Use |
|-------|---------|-------------|
| [Code Reuse Thinking Guide](./code-reuse-thinking-guide.md) | Identify patterns and reduce duplication | 当你准备新增 helper、复制 store/API/组件逻辑时 |
| [Cross-Layer Thinking Guide](./cross-layer-thinking-guide.md) | Think through data flow across layers | 当改动涉及前后端、store、router、数据库、AI 输出边界时 |

---

## Project-Specific Thinking Triggers

### When to Think About Cross-Layer Issues

- [ ] 改动涉及 `backend schema ↔ frontend api types ↔ store ↔ view`
- [ ] 改了章节、蓝图、伏笔、评估结果等核心数据结构
- [ ] 改了登录态恢复、权限守卫、管理员页面跳转
- [ ] 改了 AI 返回解析、章节版本选择、失败回滚流程
- [ ] 改了数据库字段或 section 接口

→ Read [Cross-Layer Thinking Guide](./cross-layer-thinking-guide.md)

### When to Think About Code Reuse

- [ ] 你准备再写一个类似 `NovelDetailShell` 的页面壳
- [ ] 你准备再包一层新的请求辅助函数 / alert / modal / store helper
- [ ] 你在多个页面复制同一种 loading / error / retry 结构
- [ ] 你要新增常量、路由 meta、API 前缀或配置键

→ Read [Code Reuse Thinking Guide](./code-reuse-thinking-guide.md)

---

## Pre-Modification Rule (CRITICAL)

> **Before changing ANY shared value, shape, or route, ALWAYS search first.**

在本项目里尤其包括：

- API path / prefix
- section key
- Pinia store 字段名
- generation status / chapter status
- system config key
- 数据库列名

因为这些值通常同时出现在：

- 后端 router / service / schema / init_db
- 前端 api / store / view / router

---

## How to Use This Directory

1. 改接口或字段前，先过一遍 cross-layer guide
2. 准备新增 helper、store 包装、共享组件前，先过一遍 code-reuse guide
3. 如果这次 bug 是“有个地方没同步改到”，把经验补进对应 guide

---

## Core Principle

这个项目最常见的错误不是“不会写”，而是“改了一层，忘了另一层”。先想清楚边界，再动手。
