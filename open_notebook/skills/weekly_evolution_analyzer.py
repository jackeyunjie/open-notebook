"""
Weekly Evolution Analyzer - 周度进化分析器

功能:
1. 分析上周内容表现数据
2. 识别高价值内容和低价值内容
3. 生成策略调整建议
4. 预测下周趋势
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class WeeklyEvolutionAnalyzer:
    """周度进化分析器"""
    
    def __init__(self, notebook_id: Optional[str] = None):
        self.notebook_id = notebook_id
        
    async def initialize(self):
        """初始化"""
        logger.info("Initializing WeeklyEvolutionAnalyzer...")
        
    async def analyze_weekly_evolution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析周度数据并生成进化报告
        
        Args:
            data: 包含上周数据的字典，包括:
                - period: 时间周期
                - total_views: 总阅读量
                - total_followers: 总涨粉数
                - total_engagement: 总互动数
                - content_count: 内容数量
                - platforms: 各平台详细数据
                
        Returns:
            分析报告字典
        """
        logger.info("Analyzing weekly evolution data...")
        
        # Step 1: 计算核心指标
        metrics = self._calculate_metrics(data)
        
        # Step 2: 识别高价值和低价值内容
        content_analysis = self._analyze_content_performance(data)
        
        # Step 3: 生成洞察
        insights = self._generate_insights(metrics, content_analysis, data)
        
        # Step 4: 策略调整建议
        strategy_adjustments = self._suggest_strategy_adjustments(insights, content_analysis)
        
        # Step 5: 趋势预测
        trend_prediction = self._predict_trend(metrics, data)
        
        # Step 6: 行动项
        action_items = self._generate_action_items(strategy_adjustments, trend_prediction)
        
        report = {
            'period': data.get('period', 'Unknown'),
            'generated_at': datetime.now().isoformat(),
            'metrics': metrics,
            'content_analysis': content_analysis,
            'key_insights': insights[:5],  # Top 5 insights
            'strategy_adjustments': strategy_adjustments,
            'trend_prediction': trend_prediction,
            'action_items': action_items,
            'evolution_score': self._calculate_evolution_score(metrics, insights)
        }
        
        logger.info(f"Analysis complete. Evolution score: {report['evolution_score']}/100")
        return report
    
    def _calculate_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算核心指标"""
        total_views = data.get('total_views', 0)
        total_followers = data.get('total_followers', 0)
        total_engagement = data.get('total_engagement', 0)
        content_count = max(data.get('content_count', 1), 1)  # Avoid division by zero
        
        return {
            'total_views': total_views,
            'total_followers_gain': total_followers,
            'total_engagement': total_engagement,
            'content_count': content_count,
            'avg_views_per_content': round(total_views / content_count, 2),
            'avg_followers_per_content': round(total_followers / content_count, 2),
            'engagement_rate': round((total_engagement / total_views * 100) if total_views > 0 else 0, 2),
            'follower_conversion_rate': round((total_followers / total_views * 100) if total_views > 0 else 0, 2),
        }
    
    def _analyze_content_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析内容表现"""
        # TODO: 实际实现需要从数据库查询具体内容数据
        return {
            'high_performers': [],  # Top 20% content
            'low_performers': [],   # Bottom 20% content
            'avg_performance': {},
            'platform_breakdown': data.get('platforms', {})
        }
    
    def _generate_insights(self, metrics: Dict, content_analysis: Dict, data: Dict) -> List[str]:
        """生成洞察"""
        insights = []
        
        # Insight 1: 整体表现评估
        engagement_rate = metrics.get('engagement_rate', 0)
        if engagement_rate > 5:
            insights.append(f"互动率优秀 ({engagement_rate}%)，内容质量获得认可")
        elif engagement_rate > 2:
            insights.append(f"互动率良好 ({engagement_rate}%)，有提升空间")
        else:
            insights.append(f"互动率偏低 ({engagement_rate}%)，需要优化内容吸引力")
        
        # Insight 2: 涨粉效率
        follower_rate = metrics.get('follower_conversion_rate', 0)
        if follower_rate > 1:
            insights.append(f"涨粉转化率高 ({follower_rate}%)，人设定位清晰")
        else:
            insights.append(f"涨粉转化率待提升 ({follower_rate}%)，需强化关注动机设计")
        
        # Insight 3: 内容产出效率
        content_count = metrics.get('content_count', 0)
        avg_views = metrics.get('avg_views_per_content', 0)
        if content_count > 7 and avg_views > 1000:
            insights.append("高频高质内容策略见效，建议保持")
        elif content_count < 3:
            insights.append("内容产出不足，建议增加发布频率")
        
        # Insight 4: 平台表现差异
        platforms = data.get('platforms', {})
        if platforms:
            best_platform = max(platforms.items(), key=lambda x: x[1].get('views', 0))
            insights.append(f"{best_platform[0]} 表现最佳，可加大投入")
        
        return insights
    
    def _suggest_strategy_adjustments(self, insights: List[str], content_analysis: Dict) -> List[str]:
        """建议策略调整"""
        adjustments = []
        
        # 基于洞察生成调整建议
        for insight in insights:
            if "互动率偏低" in insight:
                adjustments.append("增加互动引导话术，如提问、投票、抽奖等")
                adjustments.append("优化开头 3 秒/前 3 行，提升完读率")
            
            if "涨粉转化率待提升" in insight:
                adjustments.append("在内容中植入系列化钩子，引导关注追更")
                adjustments.append("优化个人主页装修，强化专业定位")
            
            if "内容产出不足" in insight:
                adjustments.append("建立内容日历，提前规划选题")
                adjustments.append("采用批量创作 + 错峰发布策略")
        
        # 默认建议
        if not adjustments:
            adjustments.append("保持当前策略，持续优化细节")
        
        return list(set(adjustments))  # Remove duplicates
    
    def _predict_trend(self, metrics: Dict, data: Dict) -> str:
        """趋势预测"""
        # 简化的趋势预测逻辑
        engagement_rate = metrics.get('engagement_rate', 0)
        follower_rate = metrics.get('follower_conversion_rate', 0)
        
        if engagement_rate > 5 and follower_rate > 1:
            return "上升趋势，预计下周流量和涨粉将持续增长"
        elif engagement_rate > 2:
            return "平稳发展，建议通过爆款内容突破流量层级"
        else:
            return "需要调整，建议复盘内容方向和表达方式"
    
    def _calculate_evolution_score(self, metrics: Dict, insights: List[str]) -> int:
        """计算进化得分 (0-100)"""
        score = 0
        
        # 基础分 (40 分)
        score += min(metrics.get('engagement_rate', 0) * 8, 40)  # 最高 40 分
        
        # 涨粉分 (30 分)
        score += min(metrics.get('follower_conversion_rate', 0) * 15, 30)  # 最高 30 分
        
        # 产出分 (20 分)
        content_count = metrics.get('content_count', 0)
        score += min(content_count * 3, 20)  # 每周 7 篇得满分
        
        # 洞察分 (10 分)
        positive_insights = sum(1 for i in insights if any(kw in i for kw in ['优秀', '良好', '高', '清晰']))
        score += positive_insights * 2
        
        return min(int(score), 100)
    
    def _generate_action_items(self, strategy_adjustments: List[str], trend_prediction: str) -> List[str]:
        """生成行动项"""
        action_items = []
        
        # 从策略调整中提取可执行项
        for adjustment in strategy_adjustments[:3]:  # Top 3 priority
            if "互动引导" in adjustment:
                action_items.append("每条内容结尾添加互动问题或行动号召")
            if "开头 3 秒" in adjustment:
                action_items.append("优化视频前 3 秒/文案前 3 行的钩子设计")
            if "系列化" in adjustment:
                action_items.append("规划 3-5 期系列内容，形成连续剧效应")
            if "内容日历" in adjustment:
                action_items.append("制定下周内容发布计划表")
        
        # 趋势相关的行动
        if "上升" in trend_prediction:
            action_items.append("加大投放预算，放大增长势能")
        elif "调整" in trend_prediction:
            action_items.append("深度复盘近 3 篇数据最差内容，找出问题")
        
        # 默认行动
        if not action_items:
            action_items.append("保持现有节奏，监控数据变化")
        
        return action_items
    
    async def close(self):
        """关闭"""
        logger.info("Closing WeeklyEvolutionAnalyzer...")


# ============================================================================
# Convenience Function
# ============================================================================

async def analyze_evolution(data: Dict[str, Any], notebook_id: Optional[str] = None) -> Dict[str, Any]:
    """便捷函数：分析周度进化"""
    analyzer = WeeklyEvolutionAnalyzer(notebook_id=notebook_id)
    await analyzer.initialize()
    try:
        return await analyzer.analyze_weekly_evolution(data)
    finally:
        await analyzer.close()
