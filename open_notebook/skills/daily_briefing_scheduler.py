"""
Daily Briefing Scheduler - 每日简报调度器

每天自动采集、汇总并发送邮件简报
"""

import asyncio
import schedule
import time
from datetime import datetime
from typing import Optional
from pathlib import Path

from .daily_briefing_collector import DailyBriefingCollector, ContentItem
from .email_service import EmailService


class DailyBriefingScheduler:
    """每日简报调度器"""
    
    def __init__(
        self,
        smtp_server: str = "smtp.qq.com",
        smtp_port: int = 465,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        recipient_email: str = "1300893414@qq.com",
        send_time: str = "08:00"  # 默认早上 8 点发送
    ):
        """
        初始化调度器
        
        Args:
            smtp_server: SMTP 服务器
            smtp_port: SMTP 端口
            sender_email: 发件人邮箱
            sender_password: 发件人密码/授权码
            recipient_email: 收件人邮箱
            send_time: 发送时间（HH:MM 格式）
        """
        self.recipient_email = recipient_email
        self.send_time = send_time
        
        # 从环境变量读取邮箱配置（如果未提供）
        import os
        self.sender_email = sender_email or os.getenv("SMTP_USERNAME")
        self.sender_password = sender_password or os.getenv("SMTP_PASSWORD")
        
        if not self.sender_email or not self.sender_password:
            print("⚠️  警告：未配置邮箱信息，邮件发送功能将不可用")
            print("   请设置环境变量：SMTP_USERNAME 和 SMTP_PASSWORD")
        
        # 初始化服务
        self.collector = DailyBriefingCollector()
        
        if self.sender_email and self.sender_password:
            self.email_service = EmailService(
                smtp_server, 
                smtp_port, 
                self.sender_email, 
                self.sender_password
            )
        else:
            self.email_service = None
    
    async def generate_and_send_briefing(self) -> bool:
        """生成并发送简报"""
        try:
            print(f"\n{'='*60}")
            print(f"📬 开始生成每日简报 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            print(f"{'='*60}\n")
            
            # 1. 采集内容
            items = await self.collector.collect_all()
            
            # 2. 筛选 Top 10
            top_items = self.collector.filter_top_n(items, 10)
            
            # 3. 转换为字典格式
            items_dict = [
                {
                    "platform": item.platform,
                    "author": item.author,
                    "title": item.title,
                    "content": item.content,
                    "url": item.url,
                    "tags": item.tags,
                    "publish_time": item.publish_time
                }
                for item in top_items
            ]
            
            # 4. 生成 HTML 邮件
            date_str = datetime.now().strftime("%Y年%m月%d日")
            subject = f"📋 OPC & OpenClaw & AI Coding 每日简报 - {date_str}"
            
            if self.email_service:
                html_content = self.email_service.generate_html_email(items_dict, date_str)
                
                # 5. 发送邮件
                success = self.email_service.send_email(
                    self.recipient_email,
                    subject,
                    html_content
                )
                
                if success:
                    print(f"✅ 简报已成功发送至：{self.recipient_email}")
                    return True
                else:
                    print(f"❌ 邮件发送失败")
                    return False
            else:
                # 无邮箱配置时，保存为 HTML 文件
                output_path = Path(f"briefing_{datetime.now().strftime('%Y%m%d')}.html")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(self.email_service.generate_html_email(items_dict, date_str))
                
                print(f"⚠️  邮箱未配置，简报已保存到：{output_path}")
                return True
                
        except Exception as e:
            print(f"❌ 生成简报失败：{e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _run_scheduler(self):
        """运行调度器（阻塞式）"""
        print(f"\n{'='*60}")
        print(f"🕐 每日简报调度器已启动")
        print(f"📧 收件人：{self.recipient_email}")
        print(f"⏰ 发送时间：每天 {self.send_time}")
        print(f"{'='*60}\n")
        
        # 安排定时任务
        schedule.every().day.at(self.send_time).do(
            lambda: asyncio.run(self.generate_and_send_briefing())
        )
        
        # 立即执行一次测试
        print("🚀 立即执行一次测试...")
        asyncio.run(self.generate_and_send_briefing())
        
        # 持续运行
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    def start(self, blocking: bool = True):
        """
        启动调度器
        
        Args:
            blocking: 是否阻塞运行
        """
        if blocking:
            self._run_scheduler()
        else:
            # 非阻塞模式，在后台线程运行
            import threading
            thread = threading.Thread(target=self._run_scheduler, daemon=True)
            thread.start()
            print(f"✅ 调度器已在后台启动")
            return thread


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OPC & OpenClaw & AI Coding 每日简报系统")
    
    parser.add_argument(
        "--email",
        type=str,
        default="1300893414@qq.com",
        help="收件人邮箱"
    )
    
    parser.add_argument(
        "--time",
        type=str,
        default="08:00",
        help="发送时间（HH:MM 格式）"
    )
    
    parser.add_argument(
        "--once",
        action="store_true",
        help="仅执行一次，不启动定时任务"
    )
    
    args = parser.parse_args()
    
    # 创建调度器
    scheduler = DailyBriefingScheduler(
        recipient_email=args.email,
        send_time=args.time
    )
    
    if args.once:
        # 仅执行一次
        print("🚀 执行单次简报生成...\n")
        success = asyncio.run(scheduler.generate_and_send_briefing())
        exit(0 if success else 1)
    else:
        # 启动定时任务
        scheduler.start(blocking=True)


if __name__ == "__main__":
    main()
