"""
Email Service - 邮件发送服务

发送 HTML 格式的每日简报邮件
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime


class EmailService:
    """邮件服务"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        """
        初始化邮件服务
        
        Args:
            smtp_server: SMTP 服务器地址
            smtp_port: SMTP 端口
            username: 邮箱账号
            password: 邮箱密码/授权码
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def generate_html_email(
        self, 
        items: List[Dict[str, Any]], 
        date: str = None
    ) -> str:
        """
        生成 HTML 格式的邮件内容
        
        Args:
            items: 内容列表
            date: 日期字符串
            
        Returns:
            HTML 字符串
        """
        if not date:
            date = datetime.now().strftime("%Y年%m月%d日")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OPC & OpenClaw & AI Coding 每日简报</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .header p {{
            font-size: 16px;
            opacity: 0.9;
        }}
        
        .date {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.3);
            font-size: 14px;
            opacity: 0.8;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .summary {{
            background-color: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px 20px;
            margin-bottom: 25px;
            border-radius: 4px;
        }}
        
        .summary h3 {{
            color: #667eea;
            font-size: 16px;
            margin-bottom: 8px;
        }}
        
        .summary p {{
            color: #555;
            font-size: 14px;
            line-height: 1.7;
        }}
        
        .item {{
            margin-bottom: 25px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        
        .item:hover {{
            border-color: #667eea;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
            transform: translateY(-2px);
        }}
        
        .item-header {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        
        .item-number {{
            display: inline-block;
            width: 28px;
            height: 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            line-height: 28px;
            border-radius: 50%;
            font-weight: bold;
            font-size: 14px;
            margin-right: 12px;
            flex-shrink: 0;
        }}
        
        .platform-tag {{
            display: inline-block;
            padding: 3px 10px;
            background-color: #e8f0fe;
            color: #667eea;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            margin-left: auto;
        }}
        
        .item-title {{
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }}
        
        .item-title a {{
            color: inherit;
            text-decoration: none;
            transition: color 0.2s;
        }}
        
        .item-title a:hover {{
            color: #667eea;
        }}
        
        .item-meta {{
            display: flex;
            gap: 15px;
            margin-bottom: 10px;
            font-size: 13px;
            color: #666;
        }}
        
        .item-author {{
            display: flex;
            align-items: center;
        }}
        
        .item-author::before {{
            content: "👤";
            margin-right: 5px;
        }}
        
        .item-time {{
            display: flex;
            align-items: center;
        }}
        
        .item-time::before {{
            content: "🕐";
            margin-right: 5px;
        }}
        
        .item-content {{
            color: #555;
            font-size: 14px;
            line-height: 1.8;
            margin-bottom: 10px;
        }}
        
        .item-tags {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        
        .tag {{
            display: inline-block;
            padding: 3px 8px;
            background-color: #f5f5f5;
            color: #666;
            border-radius: 4px;
            font-size: 12px;
        }}
        
        .footer {{
            background-color: #f9f9f9;
            padding: 20px 30px;
            text-align: center;
            font-size: 13px;
            color: #999;
            border-top: 1px solid #e0e0e0;
        }}
        
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        @media (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 22px;
            }}
            
            .item {{
                padding: 15px;
            }}
            
            .item-title {{
                font-size: 16px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 OPC & OpenClaw & AI Coding 每日简报</h1>
            <p>每日精选 Top 10 行业洞察</p>
            <div class="date">{date}</div>
        </div>
        
        <div class="content">
            <div class="summary">
                <h3>📊 今日概览</h3>
                <p>
                    本报表自动汇总了来自小红书、知乎、抖音、GitHub 等平台的优质内容，
                    聚焦 OPC、OpenClaw、AI Coding 领域的最新动态和技术分享。
                </p>
            </div>
            
            <h2 style="margin-bottom: 20px; color: #333;">🔥 Top {len(items)} 推荐</h2>
            
            {self._generate_items_html(items)}
            
        </div>
        
        <div class="footer">
            <p>此邮件由 <a href="#">Open Notebook</a> 自动生成</p>
            <p style="margin-top: 8px;">如有问题或建议，请联系：1300893414@qq.com</p>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return html
    
    def _generate_items_html(self, items: List[Dict[str, Any]]) -> str:
        """生成内容项 HTML"""
        html_parts = []
        
        for i, item in enumerate(items, 1):
            tags_html = "".join([
                f'<span class="tag">{tag}</span>' 
                for tag in item.get('tags', [])
            ])
            
            item_html = f"""
            <div class="item">
                <div class="item-header">
                    <span class="item-number">{i}</span>
                    <span class="platform-tag">{item.get('platform', '未知')}</span>
                </div>
                <div class="item-title">
                    <a href="{item.get('url', '#')}" target="_blank">
                        {item.get('title', '无标题')}
                    </a>
                </div>
                <div class="item-meta">
                    <span class="item-author">{item.get('author', '匿名')}</span>
                    <span class="item-time">{item.get('publish_time', '未知时间')}</span>
                </div>
                <div class="item-content">
                    {item.get('content', '无内容')}
                </div>
                <div class="item-tags">
                    {tags_html}
                </div>
            </div>
            """
            html_parts.append(item_html)
        
        return "\n".join(html_parts)
    
    def send_email(
        self,
        to_address: str,
        subject: str,
        html_content: str
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_address: 收件人地址
            subject: 邮件主题
            html_content: HTML 内容
            
        Returns:
            是否发送成功
        """
        try:
            # 创建邮件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.username
            msg["To"] = to_address
            
            # 添加 HTML 内容
            part = MIMEText(html_content, "html", "utf-8")
            msg.attach(part)
            
            # 发送邮件
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.username, self.password)
                server.sendmail(self.username, [to_address], msg.as_string())
            
            print(f"✅ 邮件已发送至：{to_address}")
            return True
            
        except Exception as e:
            print(f"❌ 邮件发送失败：{e}")
            return False


# ============================================================================
# 使用示例
# ============================================================================

def test_email_service():
    """测试邮件服务"""
    # 配置（从环境变量读取）
    import os
    smtp_server = os.getenv("SMTP_SERVER", "smtp.qq.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    
    # 示例数据
    items = [
        {
            "platform": "小红书",
            "author": "AI 编程笔记",
            "title": "使用 AI 高效学习 Python 的 5 个技巧",
            "content": "通过 AI 辅助编程，学习效率提升 3 倍...",
            "url": "https://xiaohongshu.com/example1",
            "tags": ["AI 编程", "Python"],
            "publish_time": "2026-02-18 10:30"
        }
    ]
    
    # 生成 HTML
    email_service = EmailService(smtp_server, smtp_port, username, password)
    html = email_service.generate_html_email(items)
    
    # 保存 HTML 到文件查看效果
    with open("email_preview.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ HTML 预览已保存到：email_preview.html")


if __name__ == "__main__":
    test_email_service()
