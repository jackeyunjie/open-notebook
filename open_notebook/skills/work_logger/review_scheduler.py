"""Review Scheduler - Manages periodic review prompts and templates.

Handles scheduling of daily, weekly, and monthly reviews with
conversation-driven question flows.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from open_notebook.skills.work_logger.models import ReviewTemplate


class ReviewScheduler:
    """Scheduler for work reviews.

    Manages review schedules, templates, and generates prompts
    for conversation-driven retrospectives.

    Usage:
        scheduler = ReviewScheduler(workspace_path="~/work_logs")

        # Check if review is due
        if scheduler.is_review_due("daily"):
            questions = scheduler.get_review_questions("daily")
            # Ask user these questions...
    """

    def __init__(self, workspace_path: str):
        """Initialize review scheduler.

        Args:
            workspace_path: Path to work logger workspace
        """
        self.workspace_path = Path(workspace_path).expanduser()
        self.scheduler_file = self.workspace_path / ".scheduler_state.json"
        self._state = self._load_state()
        self._templates = {
            "daily": ReviewTemplate.DAILY,
            "weekly": ReviewTemplate.WEEKLY,
            "monthly": ReviewTemplate.MONTHLY,
        }

    def _load_state(self) -> Dict:
        """Load scheduler state from disk."""
        if self.scheduler_file.exists():
            try:
                with open(self.scheduler_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load scheduler state: {e}")
        return {
            "last_daily": None,
            "last_weekly": None,
            "last_monthly": None,
            "review_history": [],
        }

    def _save_state(self) -> None:
        """Save scheduler state to disk."""
        try:
            self.scheduler_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.scheduler_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save scheduler state: {e}")

    def is_review_due(self, review_type: str) -> bool:
        """Check if a review is due.

        Args:
            review_type: Type of review (daily, weekly, monthly)

        Returns:
            True if review should be prompted
        """
        now = datetime.now()
        last_key = f"last_{review_type}"
        last_str = self._state.get(last_key)

        if not last_str:
            return True

        try:
            last = datetime.fromisoformat(last_str)
        except ValueError:
            return True

        if review_type == "daily":
            # Due if last review was before today
            return last.date() < now.date()
        elif review_type == "weekly":
            # Due if last review was more than 6 days ago
            return (now - last).days >= 6
        elif review_type == "monthly":
            # Due if last review was before this month
            return (last.year, last.month) < (now.year, now.month)

        return False

    def get_review_questions(self, review_type: str) -> List[str]:
        """Get questions for a review type.

        Args:
            review_type: Type of review

        Returns:
            List of questions to ask
        """
        template = self._templates.get(review_type)
        if template:
            return template.questions
        return ["What did you accomplish?", "What are your next steps?"]

    def mark_review_completed(self, review_type: str, summary: Optional[str] = None) -> None:
        """Mark a review as completed.

        Args:
            review_type: Type of review completed
            summary: Optional summary of the review
        """
        now = datetime.now()
        self._state[f"last_{review_type}"] = now.isoformat()

        # Add to history
        if "review_history" not in self._state:
            self._state["review_history"] = []

        self._state["review_history"].append({
            "type": review_type,
            "completed_at": now.isoformat(),
            "summary": summary,
        })

        # Keep only last 100 entries
        self._state["review_history"] = self._state["review_history"][-100:]

        self._save_state()

    def get_next_review_info(self) -> Dict[str, any]:
        """Get information about upcoming reviews.

        Returns:
            Dictionary with review status
        """
        now = datetime.now()

        def get_due_date(review_type: str) -> Optional[datetime]:
            last_key = f"last_{review_type}"
            last_str = self._state.get(last_key)
            if not last_str:
                return now

            try:
                last = datetime.fromisoformat(last_str)
            except ValueError:
                return now

            if review_type == "daily":
                return last + timedelta(days=1)
            elif review_type == "weekly":
                return last + timedelta(weeks=1)
            elif review_type == "monthly":
                # Approximate: add 30 days
                return last + timedelta(days=30)

            return None

        return {
            "daily": {
                "due": self.is_review_due("daily"),
                "next_due": get_due_date("daily"),
            },
            "weekly": {
                "due": self.is_review_due("weekly"),
                "next_due": get_due_date("weekly"),
            },
            "monthly": {
                "due": self.is_review_due("monthly"),
                "next_due": get_due_date("monthly"),
            },
        }

    def generate_review_prompt(self, review_type: str, context: Dict) -> str:
        """Generate a conversational review prompt.

        Args:
            review_type: Type of review
            context: Context data (sessions, git activity, etc.)

        Returns:
            Formatted prompt string
        """
        questions = self.get_review_questions(review_type)

        if review_type == "daily":
            return self._generate_daily_prompt(questions, context)
        elif review_type == "weekly":
            return self._generate_weekly_prompt(questions, context)
        elif review_type == "monthly":
            return self._generate_monthly_prompt(questions, context)

        return "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))

    def _generate_daily_prompt(self, questions: List[str], context: Dict) -> str:
        """Generate daily review prompt."""
        sessions = context.get("sessions", [])
        git_count = sum(len(s.git_activities) for s in sessions)

        prompt = f"""# 每日复盘

## 今日概览
- 工作会话: {len(sessions)} 个
- Git提交: {git_count} 次
- 主要项目: {', '.join(set(s.project for s in sessions if s.project)) or 'N/A'}

## 复盘问题
"""

        for i, q in enumerate(questions, 1):
            prompt += f"\n{i}. {q}"

        prompt += """

---
提示: 可以直接回复每个问题的答案，我会帮你整理成结构化日志。
"""
        return prompt

    def _generate_weekly_prompt(self, questions: List[str], context: Dict) -> str:
        """Generate weekly review prompt."""
        # Calculate weekly stats
        daily_summaries = context.get("daily_summaries", [])
        total_commits = sum(d.get("total_commits", 0) for d in daily_summaries)
        total_sessions = sum(len(d.get("sessions", [])) for d in daily_summaries)

        prompt = f"""# 周复盘

## 本周统计
- 工作日: {len(daily_summaries)} 天
- 总会话: {total_sessions} 个
- Git提交: {total_commits} 次

## 复盘问题
"""

        for i, q in enumerate(questions, 1):
            prompt += f"\n{i}. {q}"

        return prompt

    def _generate_monthly_prompt(self, questions: List[str], context: Dict) -> str:
        """Generate monthly review prompt."""
        prompt = "# 月度复盘\n\n"
        prompt += "## 本月亮点\n（基于已记录的数据）\n"

        for i, q in enumerate(questions, 1):
            prompt += f"\n{i}. {q}"

        return prompt

    def create_review_template_file(self, review_type: str, output_path: Path) -> None:
        """Create a review template markdown file.

        Args:
            review_type: Type of review
            output_path: Where to save the template
        """
        questions = self.get_review_questions(review_type)
        now = datetime.now()

        if review_type == "daily":
            filename = output_path / f"daily-review-{now.strftime('%Y%m%d')}.md"
            content = f"""# Daily Review - {now.strftime('%Y-%m-%d %A')}

## 今日完成
<!-- 列出今天完成的主要工作 -->

## 关键成果
<!-- 最重要的1-3个成果 -->

## 遇到的挑战
<!-- 遇到的困难和如何解决的 -->

## 学到的东西
<!-- 新技能、新知识、新洞察 -->

## 明日计划
<!-- 明天的优先事项 -->

## 经验记录
<!-- 值得记录的经验教训 -->

---
*Logged at: {now.strftime('%H:%M')}*
"""
        elif review_type == "weekly":
            filename = output_path / f"weekly-review-{now.strftime('%Y%W')}.md"
            content = f"""# Weekly Review - Week {now.strftime('%W')}, {now.year}

## 本周概览

### 目标达成情况
| 目标 | 状态 | 备注 |
|------|------|------|
|      |      |      |

### 时间分配
<!-- 大致时间分配 -->

## 主要成果

## 模式与趋势
<!-- 观察到的规律 -->

## 下周优先事项
1.
2.
3.

## 🆘 需要的支持

---
*Reviewed on: {now.strftime('%Y-%m-%d')}*
"""
        else:
            filename = output_path / f"monthly-review-{now.strftime('%Y%m')}.md"
            content = f"""# Monthly Review - {now.strftime('%B %Y')}

## 本月成就

## 技能成长

## 项目进展

## 流程改进

## 下月战略

---
*Reviewed on: {now.strftime('%Y-%m-%d')}*
"""

        filename.parent.mkdir(parents=True, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Created review template: {filename}")