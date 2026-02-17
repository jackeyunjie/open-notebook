"""Yuanbao Content Converter Skill - 元宝文稿转Markdown.

将元宝转来的文稿转换为标准Markdown文档，包含AI生成的总结。
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.domain.notebook import Note, Source
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class YuanbaoConverterSkill(Skill):
    """Convert Yuanbao content to Markdown with AI-generated summary.

    接收元宝转来的文稿，生成AI总结，保存为标准Markdown文档。
    文档结构：标题 → 总结 → 正文 → 元信息

    Parameters:
        - content: 元宝文稿内容（直接文本）
        - title: 文章标题（可选，自动提取）
        - output_folder: 保存文件夹路径（默认：项目根目录/yuanbao）
        - filename: 文件名（可选，自动生成）
        - add_summary: 是否添加AI总结（默认：true）
        - summary_length: 总结字数（默认：200）
        - source_id: 从Source读取内容（与content二选一）
        - note_id: 从Note读取内容（与content二选一）

    Output:
        - file_path: 保存的MD文件绝对路径
        - title: 文章标题
        - summary: AI生成的总结
        - content_length: 正文长度
        - word_count: 字数统计

    Example:
        config = SkillConfig(
            skill_type="yuanbao_converter",
            name="元宝文稿转换",
            parameters={
                "content": "元宝转来的文稿内容...",
                "title": "文章标题",
                "add_summary": True
            }
        )
    """

    skill_type = "yuanbao_converter"
    name = "元宝文稿转MD"
    description = "将元宝转来的文稿转换为带AI总结的Markdown文档"

    # 默认输出文件夹
    DEFAULT_OUTPUT_FOLDER = r"d:\Antigravity\opc\open-notebook\yuanbao"

    parameters_schema = {
        "content": {
            "type": "string",
            "default": "",
            "description": "元宝文稿内容（直接粘贴）"
        },
        "title": {
            "type": "string",
            "default": "",
            "description": "文章标题（可选，自动提取）"
        },
        "output_folder": {
            "type": "string",
            "default": r"d:\Antigravity\opc\open-notebook\yuanbao",
            "description": "MD文件保存文件夹路径"
        },
        "filename": {
            "type": "string",
            "default": "",
            "description": "文件名（可选，自动生成）"
        },
        "add_summary": {
            "type": "boolean",
            "default": True,
            "description": "是否添加AI生成的总结"
        },
        "summary_length": {
            "type": "integer",
            "default": 200,
            "minimum": 50,
            "maximum": 1000,
            "description": "总结字数"
        },
        "source_id": {
            "type": "string",
            "default": "",
            "description": "从Source读取内容（与content二选一）"
        },
        "note_id": {
            "type": "string",
            "default": "",
            "description": "从Note读取内容（与content二选一）"
        }
    }

    def __init__(self, config: SkillConfig):
        self.content: str = config.parameters.get("content", "")
        self.title: str = config.parameters.get("title", "")
        self.output_folder: str = config.parameters.get(
            "output_folder", self.DEFAULT_OUTPUT_FOLDER
        )
        self.filename: str = config.parameters.get("filename", "")
        self.add_summary: bool = config.parameters.get("add_summary", True)
        self.summary_length: int = config.parameters.get("summary_length", 200)
        self.source_id: str = config.parameters.get("source_id", "")
        self.note_id: str = config.parameters.get("note_id", "")
        super().__init__(config)

    def _validate_config(self) -> None:
        """验证配置参数."""
        super()._validate_config()

        # 检查至少有一个内容来源
        if not self.content and not self.source_id and not self.note_id:
            raise ValueError("必须提供 content、source_id 或 note_id 之一作为内容来源")

    async def _get_content_from_source(self) -> tuple[str, str]:
        """从Source或Note获取内容.

        Returns:
            tuple: (内容, 标题)
        """
        content = self.content
        title = self.title

        # 优先从Source获取
        if self.source_id:
            try:
                source = await Source.get(self.source_id)
                if source:
                    content = source.full_text or ""
                    if not title and source.title:
                        title = source.title
                    logger.info(f"从Source {self.source_id} 读取内容")
            except Exception as e:
                logger.error(f"读取Source失败: {e}")
                raise

        # 从Note获取
        elif self.note_id:
            try:
                note = await Note.get(self.note_id)
                if note:
                    content = note.content or ""
                    if not title and note.title:
                        title = note.title
                    logger.info(f"从Note {self.note_id} 读取内容")
            except Exception as e:
                logger.error(f"读取Note失败: {e}")
                raise

        return content, title

    def _extract_title_from_content(self, content: str) -> str:
        """从内容中提取标题."""
        lines = content.strip().split('\n')
        for line in lines[:5]:  # 检查前5行
            line = line.strip()
            # 匹配 # 标题 或 纯文本标题
            if line.startswith('# '):
                return line[2:].strip()
            elif line and len(line) < 100 and not line.startswith('```'):
                return line
        return f"元宝文稿_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _sanitize_filename(self, title: str) -> str:
        """生成安全的文件名."""
        # 移除非法字符
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        # 限制长度
        safe_title = safe_title[:50].strip()
        # 添加时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{safe_title}_{timestamp}.md"

    async def _generate_summary(self, content: str) -> str:
        """使用AI生成内容总结.

        Args:
            content: 正文内容

        Returns:
            AI生成的总结
        """
        if not self.add_summary:
            return ""

        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from open_notebook.ai.provision import provision_langchain_model

            prompt = f"""请为以下内容生成一个简洁的总结。

要求：
- 字数控制在 {self.summary_length} 字左右
- 概括核心观点和关键信息
- 语言流畅，便于快速阅读

内容：
---
{content[:3000]}  # 限制输入长度，避免token过多
---

总结："""

            messages = [
                SystemMessage(content="你是一位专业的内容总结专家，擅长提取文章核心要点。"),
                HumanMessage(content=prompt)
            ]

            chain = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,  # 使用默认模型
                feature_type="summarization"
            )

            response = await chain.ainvoke(messages)
            summary = response.content if hasattr(response, 'content') else str(response)
            return summary.strip()

        except Exception as e:
            logger.error(f"生成总结失败: {e}")
            return f"[总结生成失败: {e}]"

    def _build_markdown(self, title: str, summary: str, content: str) -> str:
        """构建完整的Markdown文档.

        Args:
            title: 文章标题
            summary: AI总结
            content: 正文内容

        Returns:
            完整的Markdown文本
        """
        md_parts = [f"# {title}", ""]

        # 添加总结部分
        if summary and self.add_summary:
            md_parts.extend([
                "## 总结",
                "",
                f"> {summary}",
                ""
            ])

        # 添加正文部分
        md_parts.extend([
            "## 正文",
            "",
            content,
            ""
        ])

        # 添加元信息
        md_parts.extend([
            "---",
            "",
            f"*转换时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 来源：元宝*"
        ])

        return "\n".join(md_parts)

    async def _save_markdown(self, markdown: str, filename: str) -> str:
        """保存Markdown文件.

        Args:
            markdown: Markdown内容
            filename: 文件名

        Returns:
            保存的文件绝对路径
        """
        # 确保输出文件夹存在
        output_path = Path(self.output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        # 构建完整文件路径
        file_path = output_path / filename

        # 写入文件
        file_path.write_text(markdown, encoding='utf-8')
        logger.info(f"Markdown文件已保存: {file_path}")

        return str(file_path.absolute())

    async def execute(self, context: SkillContext) -> SkillResult:
        """执行元宝文稿转换.

        Args:
            context: 执行上下文

        Returns:
            SkillResult 包含执行结果
        """
        started_at = datetime.utcnow()
        logger.info("开始元宝文稿转换")

        try:
            # 1. 获取内容
            content, title = await self._get_content_from_source()

            if not content.strip():
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                    error_message="内容为空，无法转换"
                )

            # 2. 提取/确定标题
            if not title:
                title = self._extract_title_from_content(content)
            logger.info(f"文章标题: {title}")

            # 3. 生成AI总结
            summary = ""
            if self.add_summary:
                logger.info("生成AI总结...")
                summary = await self._generate_summary(content)

            # 4. 构建Markdown
            markdown = self._build_markdown(title, summary, content)
            word_count = len(content)

            # 5. 确定文件名
            if self.filename:
                filename = self.filename if self.filename.endswith('.md') else f"{self.filename}.md"
            else:
                filename = self._sanitize_filename(title)

            # 6. 保存文件
            file_path = await self._save_markdown(markdown, filename)

            # 7. 返回结果
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                output={
                    "file_path": file_path,
                    "title": title,
                    "summary": summary,
                    "content_length": len(content),
                    "word_count": word_count,
                    "filename": filename,
                    "output_folder": self.output_folder
                }
            )

        except Exception as e:
            logger.exception(f"元宝文稿转换失败: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )


# 注册Skill
register_skill(YuanbaoConverterSkill)
