# PRD: Context-Aware Chapter Review

**Created**: 2026-04-14  
**Assignee**: AceCandy  
**Priority**: P1

---

## Background

当前的章节评审系统 (`AIReviewService`) 已经支持传入基础上下文（小说蓝图、章节大纲、前一章节等），但在实际使用中存在以下问题：

1. **伏笔信息缺失**：评审时无法感知当前章节应该回收哪些伏笔，或是否埋下了新伏笔
2. **历史章节关联弱**：只传入前一章节，无法检查与更早章节的连贯性
3. **上下文组织简单**：直接传入原始数据，缺少针对评审场景的智能筛选和组织

## Goals

增强章节评审的上下文感知能力，让 AI 评审能够：

1. 识别章节是否正确回收了待处理的伏笔
2. 发现章节中新埋下的伏笔线索
3. 检查与相关历史章节的连贯性
4. 基于项目记忆和创作宪法进行更精准的评审

## Solution

### 1. 扩展评审上下文

在 `review_context` 中新增以下字段：

```python
{
    # 现有字段
    "novel_blueprint": {...},
    "chapter_outline": {...},
    "previous_chapter": {...},
    
    # 新增字段
    "pending_foreshadows": [
        {
            "id": 1,
            "chapter_number": 3,
            "content": "主角发现神秘信件",
            "type": "mystery",
            "keywords": ["信件", "秘密"]
        }
    ],
    "related_chapters": [
        {
            "chapter_number": 5,
            "title": "...",
            "summary": "...",
            "relevance_score": 0.85
        }
    ],
    "active_plot_threads": [
        {
            "thread_name": "寻找真相",
            "status": "ongoing",
            "last_mentioned_chapter": 7
        }
    ]
}
```

### 2. 实现上下文构建服务

创建 `ReviewContextBuilder` 服务，负责：

- 查询当前章节应回收的伏笔（status=pending, chapter_number < current）
- 基于向量检索找到相关的历史章节
- 提取活跃的情节线索
- 组织成结构化的评审上下文

### 3. 更新评审提示词

修改 `editor_review` 和 `evaluation` 提示词，增加对新上下文字段的使用说明：

- 检查是否回收了待处理伏笔
- 识别新埋下的伏笔
- 评估与相关章节的连贯性

## Technical Design

### 文件变更

1. **新增文件**
   - `backend/app/services/review_context_builder.py` - 上下文构建服务

2. **修改文件**
   - `backend/app/services/ai_review_service.py` - 集成上下文构建
   - `backend/app/api/routers/review.py` - 调用上下文构建
   - `backend/app/services/chapter_review_service.py` - 传递完整上下文

### 核心逻辑

```python
class ReviewContextBuilder:
    async def build_review_context(
        self,
        project_id: str,
        chapter_number: int,
        session: AsyncSession
    ) -> Dict[str, Any]:
        # 1. 获取基础上下文（现有逻辑）
        base_context = await self._get_base_context(...)
        
        # 2. 查询待回收伏笔
        pending_foreshadows = await self._get_pending_foreshadows(
            project_id, chapter_number, session
        )
        
        # 3. 检索相关章节（向量检索）
        related_chapters = await self._get_related_chapters(
            project_id, chapter_number, session
        )
        
        # 4. 提取活跃情节线索
        plot_threads = await self._get_active_plot_threads(
            project_id, chapter_number, session
        )
        
        return {
            **base_context,
            "pending_foreshadows": pending_foreshadows,
            "related_chapters": related_chapters,
            "active_plot_threads": plot_threads
        }
```

## Acceptance Criteria

- [ ] `ReviewContextBuilder` 服务实现并通过单元测试
- [ ] 评审接口能够传递扩展的上下文信息
- [ ] AI 评审结果中能够体现对伏笔和连贯性的评价
- [ ] 现有评审功能不受影响（向后兼容）
- [ ] 代码通过 type-check 和 lint 检查

## Out of Scope

- 自动伏笔提取（仍需人工标注）
- 情节线索的自动追踪（本期仅传递已有数据）
- 前端 UI 改动（本期仅后端增强）

## Notes

- 向量检索依赖现有的 embedding_service
- 伏笔数据来自 foreshadowing 表
- 如果某些上下文数据缺失，应优雅降级，不影响基础评审功能
