"""Export Manager - Enhanced export capabilities.

Supports export to various formats and platforms:
- Markdown reports
- Email notifications
- Notion/飞书 integration (prepared)
- JSON data export
"""

import json
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from loguru import logger


@dataclass
class EmailConfig:
    """Email configuration for notifications."""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_address: str
    to_addresses: List[str]
    use_tls: bool = True


class ExportManager:
    """Manager for exporting work logger data.

    Supports multiple export formats and destinations.

    Usage:
        manager = ExportManager("~/.claude/work_logs")

        # Export markdown report
        report = manager.export_daily_markdown()

        # Send email
        manager.send_daily_email(config)

        # Export JSON
        data = manager.export_json(days=7)
    """

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path).expanduser()
        self.exports_dir = self.workspace_path / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def export_daily_markdown(self, date: Optional[datetime] = None) -> str:
        """Export daily report as Markdown.

        Args:
            date: Date to export (default: today)

        Returns:
            Markdown formatted report
        """
        if date is None:
            date = datetime.now()

        # Load data
        from open_notebook.skills.work_logger.work_logger import WorkLoggerSkill
        from open_notebook.skills.work_logger.mood_tracker import MoodTracker

        # Get daily summary
        sessions = self._load_day_sessions(date)
        mood_tracker = MoodTracker(str(self.workspace_path))
        mood_entries = mood_tracker.get_entries(
            start_date=date.replace(hour=0, minute=0),
            end_date=date.replace(hour=23, minute=59)
        )

        # Generate report
        report = f"""# Daily Work Report - {date.strftime('%Y-%m-%d %A')}

## Summary
- **Date**: {date.strftime('%Y-%m-%d')}
- **Work Sessions**: {len(sessions)}
- **Mood Entries**: {len(mood_entries)}

## Work Sessions
"""

        total_duration = 0
        for session in sessions:
            duration = session.duration_minutes or 0
            total_duration += duration
            report += f"""
### {session.title}
- **Type**: {session.session_type.value}
- **Duration**: {duration:.0f} minutes
- **Project**: {session.project or 'N/A'}
- **Tags**: {', '.join(session.tags) or 'N/A'}

{session.description or ''}

"""

        report += f"\n**Total Time**: {total_duration / 60:.1f} hours\n"

        # Mood section
        if mood_entries:
            report += "\n## Mood Tracking\n"
            for entry in mood_entries:
                report += f"""
- **{entry.timestamp.strftime('%H:%M')}**: {entry.mood.value}
  - Energy: {entry.energy.value}/5
  - Focus: {entry.focus.value}/5
  - Stress: {entry.stress}/10
  - Satisfaction: {entry.satisfaction}/10
"""

        # Save to file
        filename = self.exports_dir / f"daily-{date.strftime('%Y%m%d')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"Exported daily report: {filename}")
        return report

    def export_weekly_markdown(self, week_id: Optional[str] = None) -> str:
        """Export weekly report as Markdown."""
        if week_id is None:
            now = datetime.now()
            week_id = f"{now.year}-{now.isocalendar()[1]:02d}"

        from open_notebook.skills.work_logger.ai_insights import AIInsightsEngine

        engine = AIInsightsEngine(str(self.workspace_path))
        report = engine.generate_weekly_ai_report()

        # Save to file
        filename = self.exports_dir / f"weekly-{week_id}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"Exported weekly report: {filename}")
        return report

    def export_json(self, days: int = 7) -> Dict[str, Any]:
        """Export all data as JSON.

        Args:
            days: Number of days to include

        Returns:
            Complete data export
        """
        end = datetime.now()
        start = end - timedelta(days=days)

        # Load all data
        from open_notebook.skills.work_logger.work_logger import WorkLoggerSkill
        from open_notebook.skills.work_logger.mood_tracker import MoodTracker

        sessions = self._load_sessions(start, end)
        mood_tracker = MoodTracker(str(self.workspace_path))
        mood_entries = mood_tracker.get_entries(start, end)

        data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "period_days": days,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
            "summary": {
                "total_sessions": len(sessions),
                "total_duration_minutes": sum(s.duration_minutes or 0 for s in sessions),
                "mood_entries": len(mood_entries),
            },
            "sessions": [self._session_to_dict(s) for s in sessions],
            "mood_entries": [e.to_dict() for e in mood_entries],
        }

        # Save to file
        filename = self.exports_dir / f"export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported JSON data: {filename}")
        return data

    def send_daily_email(self, config: EmailConfig, date: Optional[datetime] = None) -> bool:
        """Send daily report via email.

        Args:
            config: Email configuration
            date: Date to report (default: today)

        Returns:
            True if sent successfully
        """
        try:
            # Generate report
            report_md = self.export_daily_markdown(date)

            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Daily Work Report - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = config.from_address
            msg['To'] = ', '.join(config.to_addresses)

            # Convert markdown to HTML (simple version)
            html_content = self._markdown_to_html(report_md)

            msg.attach(MIMEText(report_md, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))

            # Send email
            with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                if config.use_tls:
                    server.starttls()
                server.login(config.username, config.password)
                server.send_message(msg)

            logger.info(f"Sent daily email to {config.to_addresses}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_weekly_email(self, config: EmailConfig, week_id: Optional[str] = None) -> bool:
        """Send weekly report via email."""
        try:
            report_md = self.export_weekly_markdown(week_id)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Weekly Work Report - Week {week_id or datetime.now().strftime('%Y-%W')}"
            msg['From'] = config.from_address
            msg['To'] = ', '.join(config.to_addresses)

            html_content = self._markdown_to_html(report_md)

            msg.attach(MIMEText(report_md, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                if config.use_tls:
                    server.starttls()
                server.login(config.username, config.password)
                server.send_message(msg)

            logger.info(f"Sent weekly email to {config.to_addresses}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _load_day_sessions(self, date: datetime) -> List:
        """Load sessions for a specific day."""
        from open_notebook.skills.work_logger.models import SessionType, SessionStatus, WorkSession

        sessions_dir = self.workspace_path / "sessions" / date.strftime("%Y/%m/%d")
        sessions = []

        if not sessions_dir.exists():
            return sessions

        for session_file in sessions_dir.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                session = WorkSession(
                    session_id=data["session_id"],
                    start_time=datetime.fromisoformat(data["start_time"]),
                    session_type=SessionType(data.get("session_type", "other")),
                    title=data["title"],
                    description=data.get("description", ""),
                    project=data.get("project"),
                    tags=data.get("tags", []),
                    status=SessionStatus(data.get("status", "completed")),
                    end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
                    related_files=data.get("related_files", []),
                    context_notes=data.get("context_notes", ""),
                )
                sessions.append(session)
            except Exception:
                continue

        return sorted(sessions, key=lambda s: s.start_time)

    def _load_sessions(self, start: datetime, end: datetime) -> List:
        """Load sessions within date range."""
        sessions = []
        current = start

        while current <= end:
            sessions.extend(self._load_day_sessions(current))
            current += timedelta(days=1)

        return sessions

    def _session_to_dict(self, session) -> Dict:
        """Convert session to dictionary."""
        return {
            "session_id": session.session_id,
            "title": session.title,
            "description": session.description,
            "session_type": session.session_type.value if hasattr(session.session_type, 'value') else str(session.session_type),
            "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "duration_minutes": session.duration_minutes,
            "project": session.project,
            "tags": session.tags,
        }

    def _markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion."""
        html = markdown

        # Headers
        for i in range(6, 0, -1):
            html = html.replace(f"{'#' * i} ", f"<h{i}>")
            html = html.replace(f"\n{'#' * i} ", f"\n<h{i}>")

        # Bold
        html = html.replace("**", "<strong>", 1)
        while "**" in html:
            html = html.replace("**", "</strong>", 1)
            if "**" in html:
                html = html.replace("**", "<strong>", 1)

        # Lists
        lines = html.split("\n")
        in_list = False
        result = []
        for line in lines:
            if line.strip().startswith("- "):
                if not in_list:
                    result.append("<ul>")
                    in_list = True
                result.append(f"<li>{line.strip()[2:]}</li>")
            else:
                if in_list:
                    result.append("</ul>")
                    in_list = False
                result.append(line)

        if in_list:
            result.append("</ul>")

        html = "\n".join(result)

        # Wrap in HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Work Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #eee; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #666; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
{html}
</body>
</html>"""

        return html

    def prepare_notion_export(self, days: int = 7) -> Dict[str, Any]:
        """Prepare data for Notion export.

        Returns data in format ready for Notion API.
        (Actual API call would require integration token)
        """
        data = self.export_json(days)

        # Transform to Notion-friendly format
        notion_data = {
            "object": "page",
            "properties": {
                "title": {
                    "title": [{"text": {"content": f"Work Report {datetime.now().strftime('%Y-%m-%d')}"}}]
                }
            },
            "children": []
        }

        # Add sessions as content
        for session in data.get("sessions", []):
            notion_data["children"].append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": session["title"]}}]
                }
            })

        logger.info("Prepared Notion export data")
        return notion_data

    def prepare_feishu_export(self, days: int = 7) -> Dict[str, Any]:
        """Prepare data for Feishu/Lark export."""
        data = self.export_json(days)

        # Format for Feishu document
        feishu_content = {
            "title": f"工作日报 {datetime.now().strftime('%Y-%m-%d')}",
            "content": []
        }

        # Summary
        feishu_content["content"].append({
            "type": "text",
            "text": f"本周共 {data['summary']['total_sessions']} 个工作会话，总计 {data['summary']['total_duration_minutes']/60:.1f} 小时"
        })

        logger.info("Prepared Feishu export data")
        return feishu_content
