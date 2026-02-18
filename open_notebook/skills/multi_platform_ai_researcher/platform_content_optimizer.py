"""Platform Content Optimizer - Analyze and optimize content for different platforms.

This module analyzes the content format characteristics of 6 Chinese social media platforms
and provides optimization recommendations for content creation.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from datetime import datetime

from loguru import logger


class PlatformType(Enum):
    """Supported platforms."""
    XIAOHONGSHU = "xiaohongshu"
    ZHIHU = "zhihu"
    WEIBO = "weibo"
    VIDEO_ACCOUNT = "video_account"
    OFFICIAL_ACCOUNT = "official_account"
    DOUYIN = "douyin"


@dataclass
class PlatformCharacteristics:
    """Content format characteristics for a platform."""
    name: str
    name_cn: str
    content_type: str
    optimal_length: Dict[str, int]  # min, max, optimal
    formatting_rules: List[str]
    hashtag_strategy: Dict[str, Any]
    emoji_usage: Dict[str, Any]
    call_to_action: List[str]
    best_posting_times: List[str]
    audience_demographics: Dict[str, Any]
    tone_style: str
    structure_template: str
    engagement_tactics: List[str]
    prohibited_content: List[str]
    image_video_specs: Dict[str, Any]


class PlatformContentOptimizer:
    """Analyze and optimize content for different platforms."""

    def __init__(self):
        self.platforms = self._initialize_platforms()

    def _initialize_platforms(self) -> Dict[PlatformType, PlatformCharacteristics]:
        """Initialize platform characteristics."""
        return {
            PlatformType.XIAOHONGSHU: PlatformCharacteristics(
                name="xiaohongshu",
                name_cn="小红书",
                content_type="图文笔记 / 短视频",
                optimal_length={
                    "title_min": 10,
                    "title_max": 20,
                    "title_optimal": 15,
                    "content_min": 100,
                    "content_max": 1000,
                    "content_optimal": 300
                },
                formatting_rules=[
                    "标题用emoji点缀，增加视觉吸引力",
                    "正文分段清晰，每段不超过3行",
                    "关键信息用【】或「」标注",
                    "使用项目符号或数字列表",
                    "结尾添加相关话题标签"
                ],
                hashtag_strategy={
                    "count": "3-8个",
                    "placement": "文末集中",
                    "types": ["核心关键词", "场景标签", "情绪标签"],
                    "examples": ["#AI工具", "#效率提升", "#打工人必备"]
                },
                emoji_usage={
                    "density": "高频使用",
                    "placement": "标题、段落开头、重点标注",
                    "recommended": ["✨", "🔥", "💡", "📌", "⚡", "🚀", "⭐"],
                    "avoid": ["过于生僻的emoji"]
                },
                call_to_action=[
                    "点赞收藏，下次不迷路",
                    "评论区告诉我你的想法",
                    "关注我，获取更多干货",
                    "戳主页看更多"
                ],
                best_posting_times=[
                    "早高峰: 7:30-9:00",
                    "午休: 12:00-13:30",
                    "晚高峰: 18:00-20:00",
                    "睡前: 21:00-23:00"
                ],
                audience_demographics={
                    "age": "18-35岁为主",
                    "gender": "女性用户70%+",
                    "interests": ["美妆", "生活方式", "学习成长", "职场"],
                    "behavior": "喜欢收藏实用内容，追求精致生活"
                },
                tone_style="亲切友好、真实分享、干货满满、略带种草性质",
                structure_template="""
【标题】痛点/利益点 + emoji

【开场】共鸣场景描述（1-2句）

【正文】
- 核心观点/干货1
- 核心观点/干货2
- 核心观点/干货3

【总结】金句收尾 + 引导互动

【标签】#话题1 #话题2 #话题3
""",
                engagement_tactics=[
                    "封面图要精美，标题大字报",
                    "前3秒/前3行抓住注意力",
                    "提供可操作的步骤/清单",
                    "制造信息差（你不知道的...）",
                    "利用FOMO心理（限时/稀缺）"
                ],
                prohibited_content=[
                    "直接放微信号/二维码",
                    "过度营销硬广",
                    "诱导分享/关注",
                    "敏感政治话题"
                ],
                image_video_specs={
                    "image_ratio": "3:4 或 1:1",
                    "image_count": "3-9张",
                    "video_length": "15秒-3分钟",
                    "cover_style": "大字报标题+人物"
                }
            ),

            PlatformType.ZHIHU: PlatformCharacteristics(
                name="zhihu",
                name_cn="知乎",
                content_type="长文回答 / 文章 / 想法",
                optimal_length={
                    "title_min": 10,
                    "title_max": 50,
                    "title_optimal": 25,
                    "content_min": 500,
                    "content_max": 10000,
                    "content_optimal": 2000
                },
                formatting_rules=[
                    "使用知乎编辑器格式（H2/H3标题）",
                    "段落之间空一行",
                    "重要观点使用引用框或加粗",
                    "数据/案例使用表格呈现",
                    "文末添加分隔线和作者简介"
                ],
                hashtag_strategy={
                    "count": "2-5个",
                    "placement": "文末或段落中",
                    "types": ["垂直领域标签", "具体问题标签"],
                    "examples": ["#人工智能", "#ChatGPT", "#效率工具"]
                },
                emoji_usage={
                    "density": "低频使用",
                    "placement": "仅用于强调",
                    "recommended": ["✅", "❌", "📌", "💡"],
                    "avoid": ["过多emoji", "娱乐性emoji"]
                },
                call_to_action=[
                    "赞同收藏，感谢支持",
                    "欢迎在评论区讨论",
                    "关注我看更多深度回答",
                    "觉得有用请点个赞"
                ],
                best_posting_times=[
                    "上午: 9:00-11:00",
                    "下午: 14:00-17:00",
                    "晚间: 20:00-23:00"
                ],
                audience_demographics={
                    "age": "22-40岁",
                    "gender": "男女均衡",
                    "interests": ["科技", "商业", "职场", "学习"],
                    "behavior": "追求深度、理性分析、重视逻辑"
                },
                tone_style="专业严谨、逻辑清晰、有理有据、适度幽默",
                structure_template="""
【标题】问题核心 + 价值点

【引言】
- 回答背景
- 核心观点预告（目录式）

【正文】
## 第一部分：概念/背景阐述
- 定义关键概念
- 提供数据支撑

## 第二部分：核心分析
- 分点论述（每点一个小标题）
- 案例说明
- 对比分析

## 第三部分：实践建议
- 具体方法论
- 操作步骤
- 注意事项

【总结】
- 核心观点回顾
- 升华/展望

【互动引导】
""",
                engagement_tactics=[
                    "回答热门问题，抢占前排",
                    "开篇抛出爆点或数据",
                    "使用图表增强说服力",
                    "提供独家观点/一手经验",
                    "适时引用权威来源"
                ],
                prohibited_content=[
                    "洗稿/抄袭",
                    "未注明来源的转载",
                    "恶意引战",
                    "过度营销"
                ],
                image_video_specs={
                    "image_style": "信息图、数据图、流程图",
                    "image_quality": "高清，文字清晰可读",
                    "video": "辅助说明，非必须"
                }
            ),

            PlatformType.WEIBO: PlatformCharacteristics(
                name="weibo",
                name_cn="微博",
                content_type="短微博 / 长微博 / 视频",
                optimal_length={
                    "title_min": 0,
                    "title_max": 0,
                    "title_optimal": 0,
                    "content_min": 20,
                    "content_max": 5000,
                    "content_optimal": 140
                },
                formatting_rules=[
                    "短微博控制在140字以内",
                    "关键信息前置",
                    "使用换行增加可读性",
                    "@相关账号增加曝光",
                    "话题标签用##包裹"
                ],
                hashtag_strategy={
                    "count": "1-3个",
                    "placement": "内容中自然穿插",
                    "types": ["热点话题", "垂直话题", "品牌话题"],
                    "examples": ["#AI工具推荐", "#数码测评", "#效率神器"]
                },
                emoji_usage={
                    "density": "中等",
                    "placement": "情绪表达、强调",
                    "recommended": ["[doge]", "[笑cry]", "✨", "🔥", "💪"],
                    "avoid": ["与情绪不符的emoji"]
                },
                call_to_action=[
                    "转评赞走起",
                    "评论区聊聊",
                    "转发给需要的朋友",
                    "关注我，持续更新"
                ],
                best_posting_times=[
                    "早: 8:00-9:30",
                    "午: 12:00-13:00",
                    "晚: 18:00-20:00",
                    "深夜: 22:00-24:00"
                ],
                audience_demographics={
                    "age": "16-35岁",
                    "gender": "女性略多",
                    "interests": ["娱乐", "热点", "美妆", "科技"],
                    "behavior": "碎片化阅读，追求新鲜热梗"
                },
                tone_style="轻松活泼、紧跟热点、口语化、有梗有趣",
                structure_template="""
【短微博】
[热点/梗] + 核心观点 + [情绪emoji]

或

【长微博】
[导语] 一句话总结

[正文]
- 展开说明
- 分点论述
- 举例佐证

[结尾] 观点或互动引导

[话题] #话题1# #话题2#
""",
                engagement_tactics=[
                    "蹭热点要快，抢首发",
                    "使用网络热梗和流行语",
                    "配图要吸睛（9图最佳）",
                    "与粉丝高频互动",
                    "定期发福利/抽奖"
                ],
                prohibited_content=[
                    "敏感话题",
                    "未经证实的小道消息",
                    "过度营销",
                    "引战内容"
                ],
                image_video_specs={
                    "image_ratio": "不限",
                    "image_count": "1/4/6/9张最佳",
                    "gif": "受欢迎，增加趣味性",
                    "video": "横竖屏均可"
                }
            ),

            PlatformType.VIDEO_ACCOUNT: PlatformCharacteristics(
                name="video_account",
                name_cn="视频号",
                content_type="短视频 / 直播",
                optimal_length={
                    "title_min": 5,
                    "title_max": 30,
                    "title_optimal": 15,
                    "content_min": 0,
                    "content_max": 1000,
                    "content_optimal": 100
                },
                formatting_rules=[
                    "视频描述简洁有力",
                    "前三秒决定完播率",
                    "使用#话题#增加曝光",
                    "@微信好友或公众号",
                    "引导点赞评论收藏"
                ],
                hashtag_strategy={
                    "count": "3-5个",
                    "placement": "描述中",
                    "types": ["领域标签", "热点标签", "位置标签"],
                    "examples": ["#AI教程", "#微信视频号", "#知识分享"]
                },
                emoji_usage={
                    "density": "适量",
                    "placement": "标题和描述",
                    "recommended": ["🎬", "👆", "🔥", "💡", "✨"],
                    "avoid": ["过多emoji分散注意力"]
                },
                call_to_action=[
                    "点赞关注，持续更新",
                    "评论区说出你的问题",
                    "收藏起来慢慢看",
                    "转发给需要的朋友"
                ],
                best_posting_times=[
                    "早: 7:00-9:00",
                    "午: 12:00-14:00",
                    "晚: 18:00-22:00"
                ],
                audience_demographics={
                    "age": "25-50岁",
                    "gender": "均衡",
                    "interests": ["生活", "教育", "商业", "兴趣"],
                    "behavior": "依托微信生态，易转发朋友圈"
                },
                tone_style="真实自然、价值输出、信任感强",
                structure_template="""
【视频前3秒】
- 痛点提问 或 结果预告
- "你知道吗..." / "今天教你..."

【视频内容】
- 问题/痛点
- 解决方案（步骤演示）
- 效果展示

【视频描述】
核心观点一句话
#话题1# #话题2# #话题3#
@相关账号
""",
                engagement_tactics=[
                    "真人出镜增加信任",
                    "口播语速适中，清晰表达",
                    "字幕必须添加",
                    "背景音乐选择恰当",
                    "封面大字报风格"
                ],
                prohibited_content=[
                    "诱导分享朋友圈",
                    "二维码引流",
                    "夸张标题党",
                    "低俗内容"
                ],
                image_video_specs={
                    "ratio": "9:16竖屏最佳",
                    "length": "15秒-3分钟",
                    "cover": "大字标题+人物",
                    "subtitle": "必须添加"
                }
            ),

            PlatformType.OFFICIAL_ACCOUNT: PlatformCharacteristics(
                name="official_account",
                name_cn="公众号",
                content_type="长图文文章",
                optimal_length={
                    "title_min": 10,
                    "title_max": 64,
                    "title_optimal": 20,
                    "content_min": 800,
                    "content_max": 20000,
                    "content_optimal": 2000
                },
                formatting_rules=[
                    "标题要吸引人点击",
                    "开篇钩子很重要（故事/痛点/数据）",
                    "使用小标题分层",
                    "段落短，多留白",
                    "重点内容高亮/加粗"
                ],
                hashtag_strategy={
                    "count": "文章内不使用#",
                    "placement": "文末标签或话题",
                    "types": ["公众号话题", "页面模板分类"],
                    "examples": []
                },
                emoji_usage={
                    "density": "低频",
                    "placement": "标题或重点标注",
                    "recommended": ["🔥", "📌", "💡", "⚠️"],
                    "avoid": ["过于娱乐化的emoji"]
                },
                call_to_action=[
                    "点击在看，分享给朋友",
                    "关注公众号，回复关键词获取资料",
                    "加入读者群交流",
                    "星标公众号，第一时间收到推送"
                ],
                best_posting_times=[
                    "早高峰: 7:00-9:00",
                    "午休: 12:00-13:30",
                    "晚高峰: 18:00-20:00",
                    "深夜: 21:00-23:00"
                ],
                audience_demographics={
                    "age": "25-45岁",
                    "gender": "均衡",
                    "interests": ["深度阅读", "专业知识", "行业洞察"],
                    "behavior": "重视内容质量，愿意深度阅读"
                },
                tone_style="专业深度、逻辑严谨、文笔流畅、价值导向",
                structure_template="""
【标题】
- 悬念式 / 数字式 / 痛点式
- 例如："我用AI工具，3天完成了1个月的工作"

【封面图】
- 与标题呼应
- 风格统一

【导语/引言】
- 故事开场 或 痛点共鸣
- 预告文章价值

【正文】
## 01 背景/问题
- 阐述现状或问题

## 02 核心内容
- 分点论述
- 案例支撑
- 数据佐证

## 03 解决方案/建议
-  actionable insights
- 步骤说明

【总结升华】
- 核心观点回顾
- 金句收尾

【互动区】
- 引导评论
- 往期推荐
""",
                engagement_tactics=[
                    "标题决定打开率，要反复打磨",
                    "开篇3段决定读完率",
                    "图文并茂，善用排版",
                    "设置互动话题或投票",
                    "文末福利引导关注"
                ],
                prohibited_content=[
                    "诱导分享（不转不是中国人）",
                    "虚假宣传",
                    "抄袭洗稿",
                    "敏感政治内容"
                ],
                image_video_specs={
                    "header_image": "顶部引导图",
                    "body_image": "与内容相关，高清",
                    "gif": "适量使用增加趣味性",
                    "video": "可插入视频号视频"
                }
            ),

            PlatformType.DOUYIN: PlatformCharacteristics(
                name="douyin",
                name_cn="抖音",
                content_type="短视频 / 直播 / 图文",
                optimal_length={
                    "title_min": 5,
                    "title_max": 55,
                    "title_optimal": 20,
                    "content_min": 0,
                    "content_max": 500,
                    "content_optimal": 50
                },
                formatting_rules=[
                    "标题简短有力，制造好奇",
                    "前三秒必须有爆点",
                    "文案与视频互补",
                    "使用@和#增加曝光",
                    "评论区互动很重要"
                ],
                hashtag_strategy={
                    "count": "3-8个",
                    "placement": "文案中",
                    "types": ["热门挑战", "垂直标签", "品牌标签", "位置标签"],
                    "examples": ["#AI教程", "#干货分享", "#知识创作人"]
                },
                emoji_usage={
                    "density": "适量",
                    "placement": "标题和文案",
                    "recommended": ["🔥", "💯", "✨", "🎯", "💪"],
                    "avoid": ["与内容调性不符的emoji"]
                },
                call_to_action=[
                    "点赞收藏不迷路",
                    "评论区扣1领取资料",
                    "关注我，每天分享干货",
                    "转发给需要的朋友"
                ],
                best_posting_times=[
                    "早: 7:00-9:00",
                    "午: 12:00-14:00",
                    "晚: 18:00-20:00",
                    "深夜: 21:00-24:00"
                ],
                audience_demographics={
                    "age": "18-35岁",
                    "gender": "均衡",
                    "interests": ["娱乐", "知识", "生活", "美妆"],
                    "behavior": "追求刺激、快节奏、强互动"
                },
                tone_style="短平快、高能量、强情绪、抓眼球",
                structure_template="""
【视频前3秒】
- 钩子开场（结果/争议/好奇/痛点）
- "千万不要..." / "99%的人不知道..."

【视频内容】
- 快节奏剪辑
- 信息密度高
- 视觉冲击强

【文案】
一句话核心 + #话题1 #话题2
@抖音小助手

【评论区】
- 预埋评论引导互动
- 置顶补充信息
""",
                engagement_tactics=[
                    "蹭热点要快（黄金2小时）",
                    "使用热门BGM",
                    "视频节奏要快",
                    "完播率是核心指标",
                    "引导用户评论（争议/求助/投票）"
                ],
                prohibited_content=[
                    "虚假宣传",
                    "诱导未成年人",
                    "危险行为",
                    "过度营销"
                ],
                image_video_specs={
                    "ratio": "9:16竖屏",
                    "length": "7秒-3分钟（黄金15-30秒）",
                    "resolution": "1080P以上",
                    "cover": "高点击率封面"
                }
            )
        }

    def get_platform_characteristics(self, platform: str) -> Optional[PlatformCharacteristics]:
        """Get characteristics for a specific platform."""
        try:
            platform_type = PlatformType(platform.lower())
            return self.platforms.get(platform_type)
        except ValueError:
            logger.warning(f"Unknown platform: {platform}")
            return None

    def optimize_content(
        self,
        content: str,
        platform: str,
        content_type: str = "article"
    ) -> Dict[str, Any]:
        """Optimize content for a specific platform.

        Args:
            content: Original content
            platform: Target platform
            content_type: Type of content (article, short, video_desc, etc.)

        Returns:
            Optimized content with recommendations
        """
        characteristics = self.get_platform_characteristics(platform)
        if not characteristics:
            return {"error": f"Unknown platform: {platform}"}

        # Analyze content
        current_length = len(content)
        optimal = characteristics.optimal_length

        recommendations = []

        # Length check
        if content_type == "article":
            if current_length < optimal.get("content_min", 0):
                recommendations.append(f"内容较短，建议扩展到{optimal['content_optimal']}字左右")
            elif current_length > optimal.get("content_max", float('inf')):
                recommendations.append(f"内容过长，建议精简至{optimal['content_optimal']}字左右")

        # Formatting suggestions
        formatting_suggestions = []
        if platform == "xiaohongshu":
            if "【" not in content and "「" not in content:
                formatting_suggestions.append("建议使用【】或「」标注关键信息")
            if not any(emoji in content for emoji in characteristics.emoji_usage["recommended"]):
                formatting_suggestions.append("建议添加emoji增强视觉效果")

        elif platform == "zhihu":
            if "##" not in content:
                formatting_suggestions.append("建议使用Markdown标题分层")
            if len(content.split("\n\n")) < 5:
                formatting_suggestions.append("建议增加段落间距，提高可读性")

        # Generate optimized version
        optimized = self._generate_optimized_version(content, platform, characteristics)

        return {
            "platform": platform,
            "platform_name": characteristics.name_cn,
            "original_length": current_length,
            "optimal_length": optimal.get("content_optimal"),
            "recommendations": recommendations,
            "formatting_suggestions": formatting_suggestions,
            "optimized_content": optimized,
            "best_posting_times": characteristics.best_posting_times,
            "call_to_action_suggestions": characteristics.call_to_action[:3],
            "hashtag_suggestions": characteristics.hashtag_strategy["examples"]
        }

    def _generate_optimized_version(
        self,
        content: str,
        platform: str,
        characteristics: PlatformCharacteristics
    ) -> str:
        """Generate an optimized version of the content."""
        # This is a simplified version - in production, you'd use LLM
        optimized = content

        if platform == "xiaohongshu":
            # Add emoji to title if missing
            if not any(emoji in optimized[:50] for emoji in characteristics.emoji_usage["recommended"]):
                optimized = f"✨ {optimized}"
            # Add line breaks
            optimized = optimized.replace("。", "。\n\n")

        elif platform == "weibo":
            # Shorten and add hashtags
            if len(optimized) > 140:
                optimized = optimized[:137] + "..."

        return optimized

    def generate_multi_platform_versions(
        self,
        original_content: str,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate optimized versions for multiple platforms.

        Args:
            original_content: Original content
            platforms: List of platforms to optimize for (default: all)

        Returns:
            Dictionary with optimized versions for each platform
        """
        if platforms is None:
            platforms = [p.value for p in PlatformType]

        results = {}
        for platform in platforms:
            result = self.optimize_content(original_content, platform)
            results[platform] = result

        return {
            "original_content": original_content,
            "platform_versions": results,
            "generated_at": datetime.now().isoformat()
        }

    def get_content_template(self, platform: str) -> str:
        """Get the structure template for a platform."""
        characteristics = self.get_platform_characteristics(platform)
        if characteristics:
            return characteristics.structure_template
        return ""

    def compare_platforms(self) -> Dict[str, Any]:
        """Compare characteristics across all platforms."""
        comparison = {
            "platforms": {},
            "summary": {
                "total_platforms": len(self.platforms),
                "content_types": list(set(p.content_type for p in self.platforms.values())),
                "average_optimal_length": sum(
                    p.optimal_length.get("content_optimal", 0)
                    for p in self.platforms.values()
                ) // len(self.platforms)
            }
        }

        for platform_type, characteristics in self.platforms.items():
            comparison["platforms"][platform_type.value] = {
                "name_cn": characteristics.name_cn,
                "content_type": characteristics.content_type,
                "optimal_length": characteristics.optimal_length["content_optimal"],
                "tone_style": characteristics.tone_style,
                "audience": characteristics.audience_demographics["age"],
                "best_times": characteristics.best_posting_times[:2]
            }

        return comparison

    def generate_platform_guide(self) -> str:
        """Generate a comprehensive platform guide."""
        guide = "# 多平台内容创作指南\n\n"

        for platform_type, char in self.platforms.items():
            guide += f"\n## {char.name_cn} ({char.name})\n\n"
            guide += f"**内容类型**: {char.content_type}\n\n"
            guide += f"**目标受众**: {char.audience_demographics['age']}, {char.audience_demographics['behavior']}\n\n"
            guide += f"**调性风格**: {char.tone_style}\n\n"
            guide += f"**最佳字数**: {char.optimal_length['content_optimal']}字\n\n"
            guide += f"**发布时间**: {', '.join(char.best_posting_times[:2])}\n\n"
            guide += "**内容模板**:\n```\n" + char.structure_template + "\n```\n\n"
            guide += "**互动技巧**:\n"
            for tactic in char.engagement_tactics[:3]:
                guide += f"- {tactic}\n"
            guide += "\n---\n"

        return guide


# Convenience functions
def optimize_for_platform(content: str, platform: str) -> Dict[str, Any]:
    """Optimize content for a specific platform."""
    optimizer = PlatformContentOptimizer()
    return optimizer.optimize_content(content, platform)


def create_multi_platform_content(
    original_content: str,
    platforms: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create optimized content for multiple platforms."""
    optimizer = PlatformContentOptimizer()
    return optimizer.generate_multi_platform_versions(original_content, platforms)


def get_platform_guide() -> str:
    """Get the comprehensive platform guide."""
    optimizer = PlatformContentOptimizer()
    return optimizer.generate_platform_guide()


if __name__ == "__main__":
    # Test the optimizer
    test_content = """
    AI工具正在改变我们的工作效率。从ChatGPT到Midjourney，
    这些工具可以帮我们完成写作、设计、编程等各种任务。
    本文将介绍10个提升效率的AI工具。
    """

    optimizer = PlatformContentOptimizer()

    # Single platform optimization
    result = optimizer.optimize_content(test_content, "xiaohongshu")
    print(f"Platform: {result['platform_name']}")
    print(f"Recommendations: {result['recommendations']}")
    print()

    # Multi-platform versions
    multi = optimizer.generate_multi_platform_versions(
        test_content,
        platforms=["xiaohongshu", "zhihu", "weibo"]
    )
    print("Multi-platform versions generated:")
    for platform, version in multi["platform_versions"].items():
        print(f"  - {platform}: {len(version['optimized_content'])} chars")
