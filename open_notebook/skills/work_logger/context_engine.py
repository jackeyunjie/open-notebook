"""Context Engine - Tracks git activity, file changes, and builds work context.

This module monitors:
- Git commits and branch changes
- File modifications
- Project activity
- Time-based context windows
"""

import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from loguru import logger

from open_notebook.skills.work_logger.models import GitActivity, FileActivity, SessionType


class ContextEngine:
    """Engine for tracking work context automatically.

    Monitors git repositories and file system to build a comprehensive
    picture of development activity without manual input.

    Usage:
        engine = ContextEngine(project_path="/path/to/project")
        git_activities = engine.get_git_activity(since_hours=2)
        file_activities = engine.get_file_activity(since_hours=2)
    """

    # File patterns to track/exclude
    TRACKED_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
        ".md", ".txt", ".yaml", ".yml", ".json", ".sql",
        ".java", ".go", ".rs", ".c", ".cpp", ".h",
    }

    EXCLUDED_PATTERNS = {
        "node_modules", ".git", "__pycache__", ".venv",
        "venv", "dist", "build", ".next", ".cache",
    }

    def __init__(self, project_path: str):
        """Initialize context engine.

        Args:
            project_path: Path to the git repository to monitor
        """
        self.project_path = Path(project_path).resolve()
        self._last_check: Optional[datetime] = None

    def get_git_activity(self, since_hours: int = 24) -> List[GitActivity]:
        """Get git commit activity.

        Args:
            since_hours: How many hours back to check

        Returns:
            List of GitActivity records
        """
        try:
            since_time = datetime.now() - timedelta(hours=since_hours)
            since_str = since_time.strftime("%Y-%m-%d %H:%M:%S")

            # Get commits since the time
            result = subprocess.run(
                ["git", "log", f"--since={since_str}", "--pretty=format:%H|%s|%ci|%D"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.warning(f"Git log failed: {result.stderr}")
                return []

            activities = []
            for line in result.stdout.strip().split("\n"):
                if not line or "|" not in line:
                    continue

                parts = line.split("|", 3)
                if len(parts) < 3:
                    continue

                commit_hash = parts[0]
                message = parts[1]
                timestamp_str = parts[2]
                branch_info = parts[3] if len(parts) > 3 else ""

                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace(" ", "T"))
                except ValueError:
                    timestamp = datetime.now()

                # Get current branch
                branch = self._get_current_branch()

                # Get file stats for this commit
                files_changed, insertions, deletions = self._get_commit_stats(commit_hash)

                activities.append(GitActivity(
                    commit_hash=commit_hash[:8],
                    message=message,
                    files_changed=files_changed,
                    insertions=insertions,
                    deletions=deletions,
                    timestamp=timestamp,
                    branch=branch,
                ))

            return activities

        except Exception as e:
            logger.error(f"Error getting git activity: {e}")
            return []

    def _get_current_branch(self) -> str:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _get_commit_stats(self, commit_hash: str) -> tuple[List[str], int, int]:
        """Get statistics for a specific commit.

        Returns:
            Tuple of (files_changed, insertions, deletions)
        """
        try:
            # Get files changed
            result = subprocess.run(
                ["git", "show", "--name-only", "--format=", commit_hash],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )
            files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

            # Get line stats
            stats_result = subprocess.run(
                ["git", "show", "--stat", "--format=", commit_hash],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )

            # Parse insertions/deletions from stats
            insertions, deletions = 0, 0
            for line in stats_result.stdout.split("\n"):
                if "insertion" in line or "deletion" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "insertion" in part:
                            try:
                                insertions = int(part.strip().split()[0])
                            except (ValueError, IndexError):
                                pass
                        elif "deletion" in part:
                            try:
                                deletions = int(part.strip().split()[0])
                            except (ValueError, IndexError):
                                pass

            return files, insertions, deletions

        except Exception as e:
            logger.error(f"Error getting commit stats: {e}")
            return [], 0, 0

    def get_file_activity(self, since_hours: int = 24) -> List[FileActivity]:
        """Get recently modified files.

        Args:
            since_hours: How many hours back to check

        Returns:
            List of FileActivity records
        """
        try:
            since_time = datetime.now() - timedelta(hours=since_hours)
            activities = []

            for file_path in self.project_path.rglob("*"):
                # Skip excluded patterns
                if any(pattern in str(file_path) for pattern in self.EXCLUDED_PATTERNS):
                    continue

                # Only track files with tracked extensions
                if file_path.suffix not in self.TRACKED_EXTENSIONS:
                    continue

                # Check modification time
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime >= since_time:
                        # Determine change type
                        change_type = "modified"
                        ctime = datetime.fromtimestamp(file_path.stat().st_ctime)
                        if abs((ctime - mtime).total_seconds()) < 60:
                            change_type = "created"

                        # Count lines
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                line_count = len(f.readlines())
                        except Exception:
                            line_count = 0

                        activities.append(FileActivity(
                            file_path=str(file_path.relative_to(self.project_path)),
                            change_type=change_type,
                            line_count=line_count,
                            timestamp=mtime,
                            project=self.project_path.name,
                        ))
                except (OSError, PermissionError):
                    continue

            return sorted(activities, key=lambda x: x.timestamp, reverse=True)

        except Exception as e:
            logger.error(f"Error getting file activity: {e}")
            return []

    def infer_session_type(self, git_activities: List[GitActivity],
                           file_activities: List[FileActivity]) -> SessionType:
        """Infer the type of work session from activity patterns.

        Args:
            git_activities: List of git activities
            file_activities: List of file activities

        Returns:
            Inferred SessionType
        """
        all_files = []
        for ga in git_activities:
            all_files.extend(ga.files_changed)
        for fa in file_activities:
            all_files.append(fa.file_path)

        if not all_files:
            return SessionType.OTHER

        # Count by extension
        md_count = sum(1 for f in all_files if f.endswith(".md"))
        code_count = sum(1 for f in all_files if any(
            f.endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".go"]
        ))
        doc_count = sum(1 for f in all_files if f.endswith((".txt", ".rst")))

        # Infer type
        if md_count > code_count and md_count > 0:
            return SessionType.WRITING
        elif doc_count > code_count:
            return SessionType.RESEARCH
        elif code_count > 0:
            return SessionType.CODING

        return SessionType.OTHER

    def build_context_snapshot(self) -> Dict:
        """Build a comprehensive context snapshot.

        Returns:
            Dictionary with current project context
        """
        git_activities = self.get_git_activity(since_hours=4)
        file_activities = self.get_file_activity(since_hours=4)

        # Get current branch and status
        branch = self._get_current_branch()
        uncommitted = self._get_uncommitted_files()

        return {
            "timestamp": datetime.now().isoformat(),
            "project": self.project_path.name,
            "branch": branch,
            "git_activities": [g.to_dict() for g in git_activities],
            "file_activities": [f.to_dict() for f in file_activities],
            "uncommitted_files": uncommitted,
            "inferred_session_type": self.infer_session_type(
                git_activities, file_activities
            ).value,
        }

    def _get_uncommitted_files(self) -> List[str]:
        """Get list of uncommitted changes."""
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
            return []
        except Exception:
            return []

    def detect_project_from_path(self, file_path: str) -> Optional[str]:
        """Detect which project a file belongs to.

        Args:
            file_path: Path to the file

        Returns:
            Project name or None
        """
        try:
            path = Path(file_path).resolve()

            # Check if under project path
            if self.project_path in path.parents or path == self.project_path:
                return self.project_path.name

            return None
        except Exception:
            return None