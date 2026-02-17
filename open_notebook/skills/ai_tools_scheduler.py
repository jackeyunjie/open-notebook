"""AI Tools Daily Report Scheduler.

Automatically schedules and runs daily AI tools research tasks.
"""

import asyncio
from datetime import datetime, time
from typing import Optional

from loguru import logger

from .multi_platform_ai_researcher import MultiPlatformAIResearcher


class DailyReportScheduler:
    """Scheduler for daily AI tools research reports."""

    def __init__(self):
        self.is_running = False
        self.next_run_time: Optional[datetime] = None

    async def run_daily_report(
        self,
        platforms: Optional[list] = None,
        keywords: Optional[list] = None,
        max_results: int = 20,
        save_to_notebook: bool = True
    ) -> dict:
        """Execute a single daily report generation.
        
        Args:
            platforms: Platforms to search
            keywords: Keywords to use
            max_results: Max results per platform
            save_to_notebook: Whether to save to notebook
            
        Returns:
            Report results dictionary
        """
        logger.info("Running scheduled daily AI tools report...")
        
        researcher = MultiPlatformAIResearcher()
        
        params = {
            'platforms': platforms or [
                'xiaohongshu',  # Start with Xiaohongshu
                # Add more platforms as they're implemented
            ],
            'keywords': keywords or [
                '一人公司 AI 工具',
                'solo 创业 AI',
                '独立开发者 AI 工具集',
                'AI 效率工具',
                'AIGC 工具'
            ],
            'max_results_per_platform': max_results,
            'generate_report': True,
            'save_to_notebook': save_to_notebook
        }
        
        try:
            result = await researcher.execute(params)
            logger.info(f"Daily report completed: {result['ai_tools_related']} AI tools found")
            return result
            
        except Exception as e:
            logger.error(f"Daily report failed: {e}")
            raise

    async def start_scheduler(
        self,
        run_time: time = time(9, 0),  # Default: 9:00 AM
        timezone: str = 'Asia/Shanghai'
    ):
        """Start the scheduler for automatic daily execution.
        
        Args:
            run_time: Time to run daily report
            timezone: Timezone for scheduling
        """
        logger.info(f"Starting daily report scheduler at {run_time}")
        self.is_running = True
        
        while self.is_running:
            now = datetime.now()
            scheduled_time = now.replace(
                hour=run_time.hour,
                minute=run_time.minute,
                second=0,
                microsecond=0
            )
            
            # If already passed today, schedule for tomorrow
            if now > scheduled_time:
                scheduled_time = scheduled_time + timedelta(days=1)
            
            self.next_run_time = scheduled_time
            
            sleep_seconds = (scheduled_time - now).total_seconds()
            logger.info(f"Next run in {sleep_seconds/3600:.1f} hours at {scheduled_time}")
            
            await asyncio.sleep(sleep_seconds)
            
            # Run the report
            await self.run_daily_report()


# Global scheduler instance
daily_scheduler = DailyReportScheduler()


async def setup_daily_schedule(run_hour: int = 9, run_minute: int = 0):
    """Convenience function to set up daily schedule.
    
    Args:
        run_hour: Hour to run (0-23)
        run_minute: Minute to run (0-59)
    """
    run_time = time(run_hour, run_minute)
    await daily_scheduler.start_scheduler(run_time=run_time)


if __name__ == "__main__":
    # Example: Run immediately
    asyncio.run(daily_scheduler.run_daily_report())
