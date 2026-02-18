"""
Weekly Evolution Scheduler - 每周自动执行 IP 进化策略

功能:
1. 每周一 9:00 自动执行
2. 收集上周数据 (阅读量、涨粉数、互动率)
3. 调用 WeeklyEvolutionAnalyzer 生成分析报告
4. 更新本周策略配置
5. 发送通知到飞书/微信
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from open_notebook.skills.weekly_evolution_analyzer import WeeklyEvolutionAnalyzer
from open_notebook.database.unified_repository import UnifiedRepositoryImpl

logger = logging.getLogger(__name__)


class WeeklyEvolutionScheduler:
    """每周进化调度器"""
    
    def __init__(self, notebook_id: Optional[str] = None):
        self.repo = UnifiedRepositoryImpl()
        self.notebook_id = notebook_id
        self.analyzer = WeeklyEvolutionAnalyzer(notebook_id=notebook_id)
        self.is_running = False
        self.notification_webhook = None  # 飞书/微信 webhook
        
    async def initialize(self):
        """初始化（加载必要的配置）"""
        logger.info("Initializing WeeklyEvolutionScheduler...")
        await self.analyzer.initialize()
        
    async def collect_last_week_data(self) -> dict:
        """收集上周数据"""
        logger.info("Collecting last week's data...")
        
        # 计算上周时间范围
        today = datetime.now()
        last_week_start = today - timedelta(days=today.weekday() + 7)
        last_week_end = today - timedelta(days=today.weekday())
        
        # 从数据库查询数据
        # TODO: 实现具体的数据查询逻辑
        data = {
            'period': f"{last_week_start.strftime('%Y-%m-%d')} to {last_week_end.strftime('%Y-%m-%d')}",
            'total_views': 0,
            'total_followers': 0,
            'total_engagement': 0,
            'content_count': 0,
            'platforms': {}
        }
        
        logger.info(f"Data collected: {data}")
        return data
    
    async def send_notification(self, message: str):
        """发送通知到飞书/微信"""
        if not self.notification_webhook:
            logger.warning("No notification webhook configured")
            return
            
        # TODO: 实现飞书/微信通知发送
        logger.info(f"Sending notification: {message}")
        
    async def run_weekly_evolution(self):
        """执行一次完整的周度进化流程"""
        try:
            logger.info("=" * 60)
            logger.info("🚀 Starting Weekly Evolution Process...")
            logger.info("=" * 60)
            
            # Step 1: 收集数据
            data = await self.collect_last_week_data()
            
            # Step 2: 生成分析报告
            logger.info("Generating weekly evolution analysis...")
            report = await self.analyzer.analyze_weekly_evolution(data)
            
            # Step 3: 保存报告
            if self.notebook_id:
                await self._save_report_to_notebook(report)
            
            # Step 4: 提取行动项
            action_items = report.get('action_items', [])
            logger.info(f"Identified {len(action_items)} action items:")
            for item in action_items:
                logger.info(f"  - {item}")
            
            # Step 5: 发送通知
            notification_msg = f"""
📊 周度进化报告已生成

时间周期：{report.get('period', 'N/A')}
综合得分：{report.get('evolution_score', 0)}/100
核心洞察：{len(report.get('insights', []))} 条
行动项：{len(action_items)} 项

关键发现:
{chr(10).join(['  • ' + i for i in report.get('key_insights', [])[:3]])}

建议优先执行:
{chr(10).join(['  ✓ ' + item for item in action_items[:2]])}
            """.strip()
            
            await self.send_notification(notification_msg)
            
            # Step 6: 打印摘要
            print("\n" + "=" * 60)
            print("📊 WEEKLY EVOLUTION SUMMARY")
            print("=" * 60)
            print(f"Period: {report.get('period')}")
            print(f"Evolution Score: {report.get('evolution_score')}/100")
            print(f"Key Insights: {len(report.get('insights', []))}")
            print(f"Action Items: {len(action_items)}")
            print("\nTop 3 Insights:")
            for i, insight in enumerate(report.get('key_insights', [])[:3], 1):
                print(f"  {i}. {insight}")
            print("\nPriority Actions:")
            for i, item in enumerate(action_items[:3], 1):
                print(f"  {i}. {item}")
            print("=" * 60 + "\n")
            
            logger.info("✅ Weekly Evolution completed successfully!")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Weekly evolution failed: {e}", exc_info=True)
            await self.send_notification(f"❌ 周度进化执行失败：{e}")
            raise
    
    async def _save_report_to_notebook(self, report: dict):
        """保存报告到 Notebook"""
        try:
            from open_notebook.domain.models import Note
            
            note_title = f"Weekly Evolution Report - {report.get('period', 'Unknown')}"
            note_content = f"""# 周度进化报告

## 基本信息
- **周期**: {report.get('period')}
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **综合得分**: {report.get('evolution_score', 0)}/100

## 核心指标
- 总阅读量：{report.get('metrics', {}).get('total_views', 0)}
- 总涨粉数：{report.get('metrics', {}).get('total_followers_gain', 0)}
- 平均互动率：{report.get('metrics', {}).get('avg_engagement_rate', 0)}%
- 内容数量：{report.get('metrics', {}).get('content_count', 0)}

## 关键洞察
{chr(10).join(['- ' + i for i in report.get('key_insights', [])])}

## 深度分析
{report.get('analysis', '')}

## 行动项
{chr(10).join(['- [ ] ' + item for item in report.get('action_items', [])])}

## 趋势预测
{report.get('trend_prediction', '')}
"""
            
            # TODO: 实际保存到数据库
            logger.info(f"Report saved to notebook: {note_title}")
            
        except Exception as e:
            logger.error(f"Failed to save report to notebook: {e}")
    
    async def start_scheduler(self, run_hour: int = 9, run_minute: int = 0):
        """启动定时调度器（每周一指定时间运行）"""
        logger.info(f"Starting weekly scheduler at {run_hour}:{run_minute:02d} every Monday")
        self.is_running = True
        
        while self.is_running:
            now = datetime.now()
            
            # 计算下一个周一的运行时间
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0 and now.hour >= run_hour:
                days_until_monday = 7
            
            next_run = now.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
            next_run += timedelta(days=days_until_monday)
            
            sleep_seconds = (next_run - now).total_seconds()
            
            logger.info(f"Next weekly evolution scheduled in {sleep_seconds/3600:.1f} hours at {next_run.strftime('%Y-%m-%d %H:%M')}")
            
            await asyncio.sleep(sleep_seconds)
            
            if self.is_running:
                await self.run_weekly_evolution()
    
    async def stop(self):
        """停止调度器"""
        logger.info("Stopping weekly evolution scheduler...")
        self.is_running = False
        await self.analyzer.close()
    
    async def close(self):
        """关闭调度器（别名）"""
        await self.stop()


# ============================================================================
# Convenience Functions
# ============================================================================

async def run_weekly_evolution(notebook_id: Optional[str] = None):
    """手动执行一次周度进化"""
    scheduler = WeeklyEvolutionScheduler(notebook_id=notebook_id)
    await scheduler.initialize()
    try:
        return await scheduler.run_weekly_evolution()
    finally:
        await scheduler.close()


async def start_weekly_scheduler(
    notebook_id: Optional[str] = None,
    run_hour: int = 9,
    run_minute: int = 0
):
    """启动每周自动调度器"""
    scheduler = WeeklyEvolutionScheduler(notebook_id=notebook_id)
    await scheduler.initialize()
    
    try:
        await scheduler.start_scheduler(run_hour=run_hour, run_minute=run_minute)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    finally:
        await scheduler.stop()


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Weekly Evolution Scheduler")
    parser.add_argument("--notebook-id", type=str, help="Notebook ID to save reports")
    parser.add_argument("--run-now", action="store_true", help="Run immediately instead of scheduling")
    parser.add_argument("--hour", type=int, default=9, help="Hour to run (default: 9)")
    parser.add_argument("--minute", type=int, default=0, help="Minute to run (default: 0)")
    
    args = parser.parse_args()
    
    if args.run_now:
        # 立即执行一次
        asyncio.run(run_weekly_evolution(notebook_id=args.notebook_id))
    else:
        # 启动定时调度器
        try:
            asyncio.run(start_weekly_scheduler(
                notebook_id=args.notebook_id,
                run_hour=args.hour,
                run_minute=args.minute
            ))
        except KeyboardInterrupt:
            print("\nScheduler stopped")
