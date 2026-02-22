"""
Daily Briefing API Router - 每日简报 API 端点

提供 REST API 用于手动触发简报生成
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

from open_notebook.skills.daily_briefing_collector import DailyBriefingCollector
from open_notebook.skills.email_service import EmailService


router = APIRouter(
    prefix="/api/v1/briefing",
    tags=["Daily Briefing - 每日简报"],
    responses={404: {"description": "Not found"}},
)


class BriefingRequest(BaseModel):
    """简报生成请求"""
    recipient_email: EmailStr = "1300893414@qq.com"
    send_immediately: bool = True
    custom_keywords: Optional[List[str]] = None
    top_n: int = 10


class BriefingResponse(BaseModel):
    """简报生成响应"""
    success: bool
    message: str
    items_count: int
    email_sent: bool
    preview_url: Optional[str] = None


@router.post(
    "/generate",
    response_model=BriefingResponse,
    summary="生成每日简报",
    description="手动触发每日简报生成和发送",
    responses={
        200: {"description": "生成成功"},
        500: {"description": "服务器错误"},
    },
)
async def generate_briefing(request: BriefingRequest):
    """生成每日简报"""
    import os
    import asyncio
    
    try:
        # 初始化采集器
        collector = DailyBriefingCollector()
        
        # 如果有自定义关键词，覆盖默认值
        if request.custom_keywords:
            collector.keywords = request.custom_keywords
        
        # 采集内容
        items = await collector.collect_all()
        
        # 筛选 Top N
        top_items = collector.filter_top_n(items, request.top_n)
        
        # 转换为字典
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
        
        # 发送邮件
        email_sent = False
        preview_url = None
        
        if request.send_immediately:
            # 从环境变量读取 SMTP 配置
            smtp_server = os.getenv("SMTP_SERVER", "smtp.qq.com")
            smtp_port = int(os.getenv("SMTP_PORT", "465"))
            username = os.getenv("SMTP_USERNAME")
            password = os.getenv("SMTP_PASSWORD")
            
            if username and password:
                email_service = EmailService(smtp_server, smtp_port, username, password)
                
                # 生成 HTML
                date_str = datetime.now().strftime("%Y年%m月%d日")
                subject = f"📋 OPC & OpenClaw & AI Coding 每日简报 - {date_str}"
                html_content = email_service.generate_html_email(items_dict, date_str)
                
                # 发送邮件
                email_sent = email_service.send_email(
                    request.recipient_email,
                    subject,
                    html_content
                )
            else:
                # 无邮箱配置，保存为文件
                from pathlib import Path
                output_path = Path(f"briefing_{datetime.now().strftime('%Y%m%d')}.html")
                
                # 需要临时创建一个 email_service 实例来生成 HTML
                temp_service = EmailService("", 465, "", "")
                html_content = temp_service.generate_html_email(items_dict, date_str)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                preview_url = f"/static/{output_path.name}"
        
        return BriefingResponse(
            success=True,
            message=f"已生成 {len(top_items)} 条内容的简报",
            items_count=len(top_items),
            email_sent=email_sent,
            preview_url=preview_url
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/test",
    summary="测试简报生成",
    description="测试采集器是否正常工作（不发送邮件）",
)
async def test_collector():
    """测试采集器"""
    collector = DailyBriefingCollector()
    items = await collector.collect_all()
    
    return {
        "success": True,
        "total_items": len(items),
        "platforms": list(set(item.platform for item in items)),
        "sample_items": [
            {
                "platform": item.platform,
                "title": item.title,
                "relevance_score": item.relevance_score
            }
            for item in items[:3]
        ]
    }
