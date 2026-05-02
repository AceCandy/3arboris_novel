# AIMETA P=评审上下文构建器_智能组织评审上下文|R=伏笔检索_相关章节检索_上下文组织|NR=不含评审逻辑|E=ReviewContextBuilder|X=internal|A=服务类|D=sqlalchemy|S=db|RD=./README.ai
"""
ReviewContextBuilder: 评审上下文构建服务

核心职责：
1. 查询待回收的伏笔
2. 检索相关的历史章节
3. 提取活跃的情节线索
4. 组织成结构化的评审上下文
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.foreshadowing import Foreshadowing
from ..models.novel import Chapter, ChapterOutline
from .foreshadowing_service import ForeshadowingService
from .llm_service import LLMService
from .vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


class ReviewContextBuilder:
    """评审上下文构建服务"""

    def __init__(
        self,
        session: AsyncSession,
        vector_store: Optional[VectorStoreService] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.session = session
        self.vector_store = vector_store
        self.llm_service = llm_service or LLMService(session)
        self.foreshadowing_service = ForeshadowingService(session)

    async def build_review_context(
        self,
        project_id: str,
        chapter_number: int,
        user_id: Optional[int] = None,
        chapter_content: Optional[str] = None,
        base_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        构建完整的评审上下文

        Args:
            project_id: 项目 ID
            chapter_number: 当前章节号
            chapter_content: 章节内容（用于向量检索）
            base_context: 基础上下文（蓝图、大纲等）

        Returns:
            包含扩展上下文的字典
        """
        context = base_context or {}

        # 1. 查询待回收伏笔
        pending_foreshadows = await self._get_pending_foreshadows(
            project_id, chapter_number
        )
        if pending_foreshadows:
            context["pending_foreshadows"] = pending_foreshadows
            logger.info(
                f"找到 {len(pending_foreshadows)} 个待回收伏笔 (project={project_id}, chapter={chapter_number})"
            )

        # 2. 检索相关章节
        if chapter_content:
            related_chapters = await self._get_related_chapters(
                project_id, chapter_number, chapter_content, user_id=user_id
            )
            if related_chapters:
                context["related_chapters"] = related_chapters
                logger.info(
                    f"检索到 {len(related_chapters)} 个相关章节 (project={project_id})"
                )

        # 3. 提取活跃情节线索
        plot_threads = await self._get_active_plot_threads(
            project_id, chapter_number
        )
        if plot_threads:
            context["active_plot_threads"] = plot_threads
            logger.info(
                f"提取 {len(plot_threads)} 个活跃情节线索 (project={project_id})"
            )

        return context

    async def _get_pending_foreshadows(
        self,
        project_id: str,
        current_chapter: int,
    ) -> List[Dict[str, Any]]:
        """查询待回收的伏笔"""
        try:
            # 查询状态为 planted 或 developing 的伏笔，且章节号小于当前章节
            query = (
                select(Foreshadowing)
                .where(Foreshadowing.project_id == project_id)
                .where(Foreshadowing.chapter_number < current_chapter)
                .where(Foreshadowing.status.in_(["planted", "developing", "partial"]))
                .order_by(Foreshadowing.chapter_number)
                .limit(20)  # 限制数量，避免上下文过长
            )

            result = await self.session.execute(query)
            foreshadows = result.scalars().all()

            return [
                {
                    "id": f.id,
                    "chapter_number": f.chapter_number,
                    "content": f.content,
                    "type": f.type,
                    "keywords": f.keywords or [],
                    "status": f.status,
                    "importance": f.importance,
                    "target_reveal_chapter": f.target_reveal_chapter,
                }
                for f in foreshadows
            ]
        except Exception:
            logger.exception("查询待回收伏笔失败")
            return []

    async def _get_related_chapters(
        self,
        project_id: str,
        current_chapter: int,
        chapter_content: str,
        top_k: int = 5,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """检索相关的历史章节"""
        try:
            if not self.vector_store or not chapter_content:
                logger.info("向量库未启用或章节内容为空，跳过相关章节检索")
                return []
            if not user_id:
                logger.warning("缺少 user_id，跳过相关章节向量检索")
                return []

            # 1. 生成查询向量
            embedding = await self.llm_service.get_embedding(
                chapter_content[:2000],  # 截取前2000字作为查询文本
                user_id=user_id,
            )
            if not embedding:
                logger.warning("生成查询向量失败，跳过相关章节检索")
                return []

            # 2. 检索相关章节片段
            chunks = await self.vector_store.query_chunks(
                project_id=project_id,
                embedding=embedding,
                top_k=top_k,
            )

            # 3. 检索相关章节摘要
            summaries = await self.vector_store.query_summaries(
                project_id=project_id,
                embedding=embedding,
                top_k=top_k,
            )

            # 4. 合并结果，去重并按相似度排序
            chapter_map: Dict[int, Dict[str, Any]] = {}

            # 从 chunks 中提取章节信息
            for chunk in chunks:
                if chunk.chapter_number >= current_chapter:
                    continue  # 只保留历史章节

                if chunk.chapter_number not in chapter_map:
                    chapter_map[chunk.chapter_number] = {
                        "chapter_number": chunk.chapter_number,
                        "title": chunk.chapter_title or f"第{chunk.chapter_number}章",
                        "summary": "",
                        "relevance_score": chunk.score,
                        "matched_content": chunk.content[:200],  # 保留匹配片段的前200字
                    }
                else:
                    # 更新最高相似度分数
                    chapter_map[chunk.chapter_number]["relevance_score"] = max(
                        chapter_map[chunk.chapter_number]["relevance_score"],
                        chunk.score,
                    )

            # 从 summaries 中补充摘要信息
            for summary in summaries:
                if summary.chapter_number >= current_chapter:
                    continue

                if summary.chapter_number in chapter_map:
                    chapter_map[summary.chapter_number]["summary"] = summary.summary
                    # 如果摘要的相似度更高，更新分数
                    chapter_map[summary.chapter_number]["relevance_score"] = max(
                        chapter_map[summary.chapter_number]["relevance_score"],
                        summary.score,
                    )
                else:
                    chapter_map[summary.chapter_number] = {
                        "chapter_number": summary.chapter_number,
                        "title": summary.title,
                        "summary": summary.summary,
                        "relevance_score": summary.score,
                        "matched_content": "",
                    }

            # 5. 按相似度排序并返回
            related_chapters = sorted(
                chapter_map.values(),
                key=lambda x: x["relevance_score"],
                reverse=True,
            )[:top_k]

            logger.info(
                f"检索到 {len(related_chapters)} 个相关章节 (project={project_id}, current_chapter={current_chapter})"
            )
            return related_chapters

        except Exception:
            logger.exception("检索相关章节失败")
            return []

    async def _get_active_plot_threads(
        self,
        project_id: str,
        current_chapter: int,
    ) -> List[Dict[str, Any]]:
        """提取活跃的情节线索"""
        try:
            # 基于伏笔的 related_plots 字段提取情节线索
            query = (
                select(Foreshadowing)
                .where(Foreshadowing.project_id == project_id)
                .where(Foreshadowing.chapter_number <= current_chapter)
                .where(Foreshadowing.status.in_(["planted", "developing", "partial"]))
                .where(Foreshadowing.related_plots.isnot(None))
            )

            result = await self.session.execute(query)
            foreshadows = result.scalars().all()

            # 聚合情节线索
            plot_threads_map: Dict[str, Dict[str, Any]] = {}
            for f in foreshadows:
                if not f.related_plots:
                    continue
                for plot_name in f.related_plots:
                    if plot_name not in plot_threads_map:
                        plot_threads_map[plot_name] = {
                            "thread_name": plot_name,
                            "status": "ongoing",
                            "last_mentioned_chapter": f.chapter_number,
                            "foreshadow_count": 0,
                        }
                    thread = plot_threads_map[plot_name]
                    thread["last_mentioned_chapter"] = max(
                        thread["last_mentioned_chapter"], f.chapter_number
                    )
                    thread["foreshadow_count"] += 1

            return list(plot_threads_map.values())
        except Exception:
            logger.exception("提取活跃情节线索失败")
            return []
