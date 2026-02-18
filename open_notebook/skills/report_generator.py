"""
Report Generator - 可视化报告生成器

功能:
1. 生成 HTML 格式的周度/月度报告
2. 数据图表可视化（趋势图、柱状图、饼图等）
3. 趋势分析看板
4. 支持导出 PDF（通过浏览器打印）
5. 交互式数据探索
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class ReportGenerator:
    """可视化报告生成器"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / "report_templates"
        
    def generate_html_report(
        self,
        report_data: Dict[str, Any],
        output_path: Optional[str] = None,
        template_name: str = "weekly_evolution.html"
    ) -> str:
        """生成 HTML 格式报告
        
        Args:
            report_data: 报告数据
            output_path: 输出文件路径
            template_name: 模板文件名
            
        Returns:
            生成的 HTML 文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"report_{timestamp}.html"
        
        html_content = self._render_html_template(report_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_path}")
        return output_path
    
    def _render_html_template(self, data: Dict[str, Any]) -> str:
        """渲染 HTML 模板"""
        
        # 提取关键数据
        period = data.get('period', 'Unknown Period')
        evolution_score = data.get('evolution_score', 0)
        metrics = data.get('metrics', {})
        insights = data.get('key_insights', [])
        action_items = data.get('action_items', [])
        
        # 生成图表数据
        chart_data = self._prepare_chart_data(data)
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>周度进化报告 - {period}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 16px;
            opacity: 0.9;
        }}
        
        .score-section {{
            padding: 40px;
            text-align: center;
            background: #f8f9fa;
        }}
        
        .score-circle {{
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }}
        
        .score-number {{
            font-size: 64px;
            font-weight: bold;
            color: white;
        }}
        
        .score-label {{
            font-size: 18px;
            color: #666;
            margin-top: 10px;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 24px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            border-color: #667eea;
        }}
        
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            font-size: 14px;
            color: #666;
        }}
        
        .insights-list {{
            list-style: none;
        }}
        
        .insight-item {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px 20px;
            margin-bottom: 15px;
            border-radius: 8px;
        }}
        
        .insight-text {{
            font-size: 16px;
            color: #333;
            line-height: 1.6;
        }}
        
        .action-list {{
            list-style: none;
        }}
        
        .action-item {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            display: flex;
            align-items: center;
        }}
        
        .action-checkbox {{
            width: 24px;
            height: 24px;
            border: 2px solid white;
            border-radius: 50%;
            margin-right: 15px;
            flex-shrink: 0;
        }}
        
        .action-text {{
            font-size: 16px;
            line-height: 1.6;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin-top: 30px;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 周度进化报告</h1>
            <p>{period}</p>
        </div>
        
        <div class="score-section">
            <div class="score-circle">
                <span class="score-number">{evolution_score}</span>
            </div>
            <div class="score-label">进化得分 / 100</div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2 class="section-title">📊 核心指标</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('total_views', 0):,}</div>
                        <div class="metric-label">总阅读量</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('total_followers_gain', 0):,}</div>
                        <div class="metric-label">总涨粉数</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('engagement_rate', 0)}%</div>
                        <div class="metric-label">互动率</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('follower_conversion_rate', 0)}%</div>
                        <div class="metric-label">涨粉转化率</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('content_count', 0)}</div>
                        <div class="metric-label">内容数量</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.get('avg_views_per_content', 0):,.0f}</div>
                        <div class="metric-label">平均阅读量</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">💡 关键洞察</h2>
                <ul class="insights-list">
                    {self._generate_insights_html(insights)}
                </ul>
            </div>
            
            <div class="section">
                <h2 class="section-title">✅ 优先行动</h2>
                <ul class="action-list">
                    {self._generate_actions_html(action_items)}
                </ul>
            </div>
            
            <div class="section">
                <h2 class="section-title">📈 趋势分析</h2>
                <div class="chart-container">
                    <canvas id="trendChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Open Notebook 进化系统</p>
        </div>
    </div>
    
    <script>
        // 趋势图表
        const ctx = document.getElementById('trendChart').getContext('2d');
        const trendChart = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
                datasets: [{{
                    label: '阅读量',
                    data: {json.dumps(chart_data.get('daily_views', [0, 0, 0, 0, 0, 0, 0]))},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }}, {{
                    label: '互动数',
                    data: {json.dumps(chart_data.get('daily_engagement', [0, 0, 0, 0, 0, 0, 0]))},
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top'
                    }},
                    title: {{
                        display: true,
                        text: '周度趋势变化'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        
        return html
    
    def _generate_insights_html(self, insights: List[str]) -> str:
        """生成洞察 HTML"""
        html = ""
        for insight in insights:
            html += f"""
            <li class="insight-item">
                <div class="insight-text">{insight}</div>
            </li>
            """
        return html
    
    def _generate_actions_html(self, actions: List[str]) -> str:
        """生成行动项 HTML"""
        html = ""
        for action in actions:
            html += f"""
            <li class="action-item">
                <div class="action-checkbox"></div>
                <div class="action-text">{action}</div>
            </li>
            """
        return html
    
    def _prepare_chart_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备图表数据"""
        # TODO: 实际实现需要从数据库查询每日数据
        # 这里使用模拟数据
        return {
            'daily_views': [1200, 1800, 1500, 2200, 1900, 2800, 2500],
            'daily_engagement': [85, 120, 95, 150, 130, 200, 175]
        }
    
    def generate_pdf_report(
        self,
        html_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """从 HTML 生成 PDF（需要浏览器支持）
        
        Args:
            html_path: HTML 文件路径
            output_path: PDF 输出路径
            
        Returns:
            PDF 文件路径
        """
        if output_path is None:
            output_path = html_path.replace('.html', '.pdf')
        
        # TODO: 实际实现需要使用 headless 浏览器
        logger.info(f"PDF generation not implemented yet. Please use browser print function.")
        
        return html_path  # 返回 HTML 路径，用户可手动打印为 PDF


# ============================================================================
# Convenience Function
# ============================================================================

def generate_visualized_report(
    report_data: Dict[str, Any],
    output_path: Optional[str] = None,
    format: str = "html"
) -> str:
    """便捷函数：生成可视化报告"""
    generator = ReportGenerator()
    
    if format == "html":
        return generator.generate_html_report(report_data, output_path)
    elif format == "pdf":
        html_path = generator.generate_html_report(report_data)
        return generator.generate_pdf_report(html_path, output_path)
    else:
        raise ValueError(f"Unsupported format: {format}")
