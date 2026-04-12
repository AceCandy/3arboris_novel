# Code Reuse Thinking Guide

> **Purpose**: Stop and think before creating new code - does it already exist?

---

## The Problem

这个项目已经有明显的共享模式：

- 前端用共享页面壳、领域组件、Pinia store、全局 alert
- 后端用 service / repository / schema 分层
- API 前缀、section key、generation status 等值会跨多层重复出现

一旦你复制一份而不是复用，最容易出现的不是立刻报错，而是后续某一层悄悄漂移。

---

## Before Writing New Code

### Step 1: Search First

优先检查是否已经存在：

- 类似组件壳（如详情页、写作台模块）
- 类似 store action / API 方法
- 现成的 alert、modal、router 守卫、权限判断
- 后端已有的 repository / service 方法

### Step 2: Ask These Questions

| Question | If Yes... |
|----------|-----------|
| 是否已有类似页面骨架或 section 容器？ | 复用或扩展现有组件 |
| 是否已有类似 API / store action？ | 不要重复包一层 |
| 是否只是另一种展示同一份数据？ | 保持同一个数据源 |
| 是否多个地方都依赖同一个常量或状态值？ | 设为单一来源 |

---

## Common Duplication Patterns In This Project

### Pattern 1: 相似页面壳重复实现

**Bad**: 再写一个和 `NovelDetailShell` 结构接近、但数据流略有不同的新壳组件

**Good**: 先判断能否在现有壳组件上用 props / section 配置扩展

参考：

- `frontend/src/components/shared/NovelDetailShell.vue:1`
- `frontend/src/views/NovelDetail.vue:2`

### Pattern 2: 重复请求封装

**Bad**: 页面里再次拼接 token、超时、日志逻辑

**Good**: 复用 auth store 里的请求辅助流程，或沿用当前 API 模块模式

参考：

- `frontend/src/stores/auth.ts:20`

### Pattern 3: 重复错误提示/弹窗逻辑

**Bad**: 每个页面自己维护一套 toast / confirm UI

**Good**: 先看 `useAlert.ts` 和 `CustomAlert.vue`

参考：

- `frontend/src/composables/useAlert.ts:18`
- `frontend/src/components/CustomAlert.vue:1`

### Pattern 4: 后端同类查询/事务逻辑重复分叉

**Bad**: router、service、repository 各写一份近似查询

**Good**: 数据访问收敛到 repository 或 service，事务边界保留在 service

参考：

- `backend/app/repositories/user_repository.py:13`
- `backend/app/services/novel_service.py:124`

---

## When to Abstract

**适合抽象当**：

- 同类结构已出现 3 次以上
- 状态流、权限判断、错误提示容易分叉
- 共享值需要跨前后端或跨多个页面保持一致

**不适合抽象当**：

- 只在一个页面或一个接口用一次
- 抽象后名字会比原逻辑更模糊
- 只是为了“看起来更通用”而增加跳转层级

---

## Project-Specific Checklist

- [ ] 先搜索是否已有相同 section / route / status / config key
- [ ] 先确认是否已有同类 store action / API 方法
- [ ] 先确认这段 UI 是否属于已有页面域组件
- [ ] 如果要新增 helper，确认不是把现有逻辑又包了一层
- [ ] 如果复制的是跨层值，检查前后端是否都要同步

---

## Core Reminder

在这个项目里，“复制一份差不多的逻辑”往往不会马上坏，但会在下一次字段变更、状态新增或接口调整时制造隐蔽分叉。
