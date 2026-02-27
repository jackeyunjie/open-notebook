"""Content Quality Assessor Skill (P1 Layer).

文案质量评估技能 - 基于 P1 四维评估框架，专门针对营销/推广内容的质量判断。

核心维度：
- 可信度 (Credibility): 声称可验证性、具体性、来源引用
- 独特性 (Uniqueness): 差异化程度、无陈词滥调、角度新颖性
- 效用 (Utility): 可操作性、场景清晰度、下一步明确
- 吸引力 (Engagement): 钩子强度、情感共鸣、可分享性

设计原则：
- 可信度权重最高（0.35），避免空洞夸张
- 吸引力权重最低（0.15），不为热度牺牲质量
- 黑名单机制惩罚"神器""救星"等空洞词汇
- 加分机制奖励具体场景和对比维度
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus


class ContentType(str, Enum):
    """内容类型"""
    MARKETING = "marketing"          # 营销推广
    TECHNICAL = "technical"          # 技术文档
    EDUCATIONAL = "educational"      # 教育内容
    SOCIAL_MEDIA = "social_media"    # 社交媒体
    PRODUCT_DESC = "product_desc"    # 产品描述


class QualityLevel(str, Enum):
    """质量等级"""
    EXCELLENT = "excellent"   # >= 0.8
    GOOD = "good"             # >= 0.6
    AVERAGE = "average"       # >= 0.4
    POOR = "poor"             # < 0.4


@dataclass
class QualityIssue:
    """质量问题"""
    dimension: str              # 所属维度
    severity: str               # critical/warning/info
    description: str            # 问题描述
    matched_text: Optional[str] = None  # 匹配到的文本
    suggestion: Optional[str] = None    # 改进建议


@dataclass
class QualityAssessment:
    """质量评估结果"""
    content: str                           # 原始内容
    content_type: ContentType              # 内容类型
    overall_score: float                   # 总分 0-1
    quality_level: QualityLevel            # 质量等级
    dimension_scores: Dict[str, float]     # 各维度得分
    issues: List[QualityIssue]             # 问题列表
    suggestions: List[str]                 # 改进建议
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content_preview": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "content_type": self.content_type.value,
            "overall_score": round(self.overall_score, 3),
            "quality_level": self.quality_level.value,
            "dimension_scores": {k: round(v, 3) for k, v in self.dimension_scores.items()},
            "issues": [
                {
                    "dimension": issue.dimension,
                    "severity": issue.severity,
                    "description": issue.description,
                    "matched_text": issue.matched_text,
                    "suggestion": issue.suggestion,
                }
                for issue in self.issues
            ],
            "suggestions": self.suggestions,
            "assessed_at": self.assessed_at.isoformat(),
        }


class ContentQualityAssessorSkill(Skill):
    """
    文案质量评估技能
    
    基于 P1 四维度框架，专门针对营销/推广内容的质量评估。
    
    核心功能：
    1. 四维度评估（可信度、独特性、效用、吸引力）
    2. 黑名单词汇惩罚（"神器"、"救星"、"强X倍"等）
    3. 加分项奖励（具体场景、对比维度、数字支撑）
    4. 自动生成改进建议
    
    使用示例：
    ```python
    assessor = ContentQualityAssessorSkill(config)
    result = await assessor.assess_content(
        content="这款神器让你效率提升10倍！",
        content_type=ContentType.MARKETING
    )
    print(result.quality_level)  # QualityLevel.POOR
    print(result.issues)  # [QualityIssue(dimension="credibility", ...)]
    ```
    """
    
    skill_type = "content_quality_assessor"
    name = "文案质量评估师"
    description = "基于P1四维评估框架，评估文案的可信度、独特性、效用和吸引力"
    
    # 评估维度及权重
    DIMENSIONS = {
        "credibility": {
            "name": "可信度",
            "weight": 0.35,  # 最高权重，避免空洞夸张
            "factors": {
                "claim_verifiability": 0.4,  # 声称可验证性
                "specificity": 0.3,          # 具体性
                "source_citation": 0.3       # 来源引用
            }
        },
        "uniqueness": {
            "name": "独特性",
            "weight": 0.25,
            "factors": {
                "differentiation": 0.5,      # 差异化程度
                "cliche_absence": 0.3,       # 无陈词滥调
                "angle_freshness": 0.2       # 角度新颖性
            }
        },
        "utility": {
            "name": "效用",
            "weight": 0.25,
            "factors": {
                "actionability": 0.5,        # 可操作性
                "scenario_clarity": 0.3,     # 场景清晰度
                "next_step_clear": 0.2       # 下一步明确
            }
        },
        "engagement": {
            "name": "吸引力",
            "weight": 0.15,  # 最低权重，不为热度牺牲质量
            "factors": {
                "hook_strength": 0.4,        # 钩子强度
                "emotional_resonance": 0.3,  # 情感共鸣
                "shareability": 0.3          # 可分享性
            }
        }
    }
    
    # 可信度惩罚项：(正则, 扣分, 描述)
    CREDIBILITY_PENALTIES: List[Tuple[str, float, str]] = [
        (r"\d+\s*倍", -0.2, "无依据的倍数声称"),
        (r"神器|救星|王炸|炸裂|逆天", -0.15, "空洞形容词"),
        (r"超厉害|太牛了|绝了|无敌|碾压", -0.12, "主观夸张词"),
        (r"一键|秒|瞬间|立刻见效", -0.1, "过度简化承诺"),
        (r"100%|绝对|肯定|保证", -0.1, "绝对化声称"),
        (r"最强|第一|唯一|独家", -0.08, "未验证的最高级"),
    ]
    
    # 可信度加分项：(正则, 加分, 描述)
    CREDIBILITY_BONUSES: List[Tuple[str, float, str]] = [
        (r"对比.*维度|vs\.?|versus|相比", +0.1, "有对比维度"),
        (r"例如|比如|场景[：:]", +0.1, "有具体场景"),
        (r"\d+分钟|\d+步|\d+天", +0.05, "有具体数字（非倍数）"),
        (r"根据.*数据|研究表明|测试显示", +0.08, "有数据支撑"),
        (r"\[cite:|来源[：:]|参考[：:]", +0.08, "有引用来源"),
    ]
    
    # 独特性惩罚项（常见套路）
    UNIQUENESS_PENALTIES: List[Tuple[str, float, str]] = [
        (r"你还在.*吗[？?]", -0.1, "老套开头句式"),
        (r"别再.*了", -0.08, "陈旧劝诫句式"),
        (r"不看.*后悔|错过.*损失", -0.1, "焦虑营销"),
        (r"强烈推荐|墙裂推荐|必看", -0.06, "推荐类陈词"),
    ]
    
    # 效用加分项
    UTILITY_BONUSES: List[Tuple[str, float, str]] = [
        (r"第一步|第二步|步骤\d|Step\s*\d", +0.1, "有步骤指引"),
        (r"上传.*→|导入.*→|打开.*→", +0.12, "有操作流程"),
        (r"适合.*人群|如果你是", +0.08, "有目标人群"),
        (r"最小可行|MVP|快速开始", +0.06, "有最小场景"),
    ]
    
    # 吸引力检测项（中性，不作为主要评判）
    ENGAGEMENT_SIGNALS: List[Tuple[str, float, str]] = [
        (r"[！!]{2,}|[？?]{2,}", +0.02, "强调标点"),
        (r"[\U0001F300-\U0001F9FF]", +0.02, "使用emoji"),
        (r"#[^\s#]+", +0.02, "使用话题标签"),
    ]
    
    # 参数模式
    parameters_schema = {
        "content": {
            "type": "string",
            "description": "待评估的文案内容",
            "required": True
        },
        "content_type": {
            "type": "string",
            "description": "内容类型：marketing/technical/educational/social_media/product_desc",
            "default": "marketing"
        },
        "competitor_content": {
            "type": "list",
            "description": "竞品内容列表，用于独特性对比",
            "default": []
        }
    }
    
    def __init__(self, config: Optional[SkillConfig] = None):
        """初始化评估器"""
        if config is None:
            config = SkillConfig(
                skill_type=self.skill_type,
                name=self.name,
                description=self.description,
            )
        super().__init__(config)
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """执行评估"""
        started_at = datetime.utcnow()
        
        try:
            content = context.get_param("content", "")
            content_type_str = context.get_param("content_type", "marketing")
            competitor_content = context.get_param("competitor_content", [])
            
            if not content:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                    error_message="内容不能为空"
                )
            
            content_type = ContentType(content_type_str)
            assessment = await self.assess_content(content, content_type, competitor_content)
            
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                output=assessment.to_dict()
            )
            
        except Exception as e:
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def assess_content(
        self,
        content: str,
        content_type: ContentType = ContentType.MARKETING,
        competitor_content: Optional[List[str]] = None
    ) -> QualityAssessment:
        """
        评估内容质量
        
        Args:
            content: 待评估内容
            content_type: 内容类型
            competitor_content: 竞品内容列表（可选）
            
        Returns:
            QualityAssessment 评估结果
        """
        issues: List[QualityIssue] = []
        dimension_scores: Dict[str, float] = {}
        
        # 1. 可信度评估
        cred_score, cred_issues = self._assess_credibility(content)
        dimension_scores["credibility"] = cred_score
        issues.extend(cred_issues)
        
        # 2. 独特性评估
        uniq_score, uniq_issues = self._assess_uniqueness(content, competitor_content or [])
        dimension_scores["uniqueness"] = uniq_score
        issues.extend(uniq_issues)
        
        # 3. 效用评估
        util_score, util_issues = self._assess_utility(content)
        dimension_scores["utility"] = util_score
        issues.extend(util_issues)
        
        # 4. 吸引力评估
        eng_score, eng_issues = self._assess_engagement(content)
        dimension_scores["engagement"] = eng_score
        issues.extend(eng_issues)
        
        # 加权总分
        overall_score = sum(
            dimension_scores[dim] * self.DIMENSIONS[dim]["weight"]
            for dim in self.DIMENSIONS
        )
        overall_score = max(0.0, min(1.0, overall_score))  # 限制在0-1
        
        # 确定质量等级
        quality_level = self._determine_quality_level(overall_score)
        
        # 生成改进建议
        suggestions = self._generate_suggestions(dimension_scores, issues)
        
        return QualityAssessment(
            content=content,
            content_type=content_type,
            overall_score=overall_score,
            quality_level=quality_level,
            dimension_scores=dimension_scores,
            issues=issues,
            suggestions=suggestions,
        )
    
    def _assess_credibility(self, content: str) -> Tuple[float, List[QualityIssue]]:
        """评估可信度"""
        base_score = 0.6  # 基础分
        issues: List[QualityIssue] = []
        
        # 检查惩罚项
        for pattern, penalty, description in self.CREDIBILITY_PENALTIES:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                base_score += penalty
                issues.append(QualityIssue(
                    dimension="credibility",
                    severity="warning" if penalty > -0.15 else "critical",
                    description=description,
                    matched_text=matches[0] if matches else None,
                    suggestion=f"考虑删除或替换「{matches[0]}」"
                ))
        
        # 检查加分项
        for pattern, bonus, description in self.CREDIBILITY_BONUSES:
            if re.search(pattern, content, re.IGNORECASE):
                base_score += bonus
        
        # 具体性评估：是否有具体数字（非夸张倍数）
        has_specific_numbers = bool(re.search(r'\d+(?:个|篇|份|页|章)', content))
        if has_specific_numbers:
            base_score += 0.05
        
        return max(0.0, min(1.0, base_score)), issues
    
    def _assess_uniqueness(
        self, 
        content: str, 
        competitors: List[str]
    ) -> Tuple[float, List[QualityIssue]]:
        """评估独特性"""
        base_score = 0.65
        issues: List[QualityIssue] = []
        
        # 检查陈词滥调
        for pattern, penalty, description in self.UNIQUENESS_PENALTIES:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                base_score += penalty
                issues.append(QualityIssue(
                    dimension="uniqueness",
                    severity="warning",
                    description=description,
                    matched_text=matches[0] if matches else None,
                    suggestion="尝试更有创意的表达方式"
                ))
        
        # 如果有竞品内容，检查相似度
        if competitors:
            similarity_penalty = self._check_competitor_similarity(content, competitors)
            if similarity_penalty > 0.15:
                base_score -= similarity_penalty
                issues.append(QualityIssue(
                    dimension="uniqueness",
                    severity="critical",
                    description="与竞品内容高度相似",
                    suggestion="突出差异化卖点，如「活体知识系统」"
                ))
        
        # 检查是否有差异化关键词
        differentiation_keywords = [
            "活体知识", "五层架构", "本地部署", "数据主权",
            "持续学习", "个性化", "自适应"
        ]
        has_differentiation = any(kw in content for kw in differentiation_keywords)
        if has_differentiation:
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score)), issues
    
    def _assess_utility(self, content: str) -> Tuple[float, List[QualityIssue]]:
        """评估效用"""
        base_score = 0.5
        issues: List[QualityIssue] = []
        
        # 检查加分项
        for pattern, bonus, description in self.UTILITY_BONUSES:
            if re.search(pattern, content, re.IGNORECASE):
                base_score += bonus
        
        # 检查是否有明确的下一步
        has_cta = bool(re.search(
            r'GitHub|链接|下载|试试|安装|部署|git clone|docker',
            content, re.IGNORECASE
        ))
        if has_cta:
            base_score += 0.1
        else:
            issues.append(QualityIssue(
                dimension="utility",
                severity="info",
                description="缺少明确的行动指引",
                suggestion="添加具体的下一步操作，如 GitHub 链接或安装命令"
            ))
        
        # 检查是否有目标场景
        has_scenario = bool(re.search(
            r'研究生|学生|开发者|创作者|写论文|做研究|整理资料',
            content, re.IGNORECASE
        ))
        if has_scenario:
            base_score += 0.1
        else:
            issues.append(QualityIssue(
                dimension="utility",
                severity="warning",
                description="缺少具体使用场景",
                suggestion="添加目标用户场景，如「研究生写文献综述」"
            ))
        
        return max(0.0, min(1.0, base_score)), issues
    
    def _assess_engagement(self, content: str) -> Tuple[float, List[QualityIssue]]:
        """评估吸引力（权重最低，仅作参考）"""
        base_score = 0.5
        issues: List[QualityIssue] = []
        
        # 检查吸引力信号
        for pattern, bonus, description in self.ENGAGEMENT_SIGNALS:
            if re.search(pattern, content):
                base_score += bonus
        
        # 检查长度适中（社交媒体150-300字为佳）
        content_length = len(content)
        if 100 <= content_length <= 300:
            base_score += 0.1
        elif content_length < 50:
            issues.append(QualityIssue(
                dimension="engagement",
                severity="info",
                description="内容过短，信息量可能不足",
                suggestion="适当扩充内容，增加价值信息"
            ))
        elif content_length > 500:
            issues.append(QualityIssue(
                dimension="engagement",
                severity="info",
                description="内容较长，社交媒体可能不易传播",
                suggestion="考虑精简为150字以内的核心版本"
            ))
        
        # 检查开头吸引力
        first_line = content.split('\n')[0] if '\n' in content else content[:50]
        has_hook = bool(re.search(r'[？?]|痛点|问题|困扰|烦恼', first_line))
        if has_hook:
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score)), issues
    
    def _check_competitor_similarity(self, content: str, competitors: List[str]) -> float:
        """检查与竞品的相似度"""
        # 简单的关键词重合度检查
        content_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}', content))
        
        max_similarity = 0.0
        for comp in competitors:
            comp_keywords = set(re.findall(r'[\u4e00-\u9fff]{2,}', comp))
            if content_keywords and comp_keywords:
                overlap = len(content_keywords & comp_keywords)
                similarity = overlap / max(len(content_keywords), len(comp_keywords))
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity * 0.3  # 转换为惩罚值
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级"""
        if score >= 0.8:
            return QualityLevel.EXCELLENT
        elif score >= 0.6:
            return QualityLevel.GOOD
        elif score >= 0.4:
            return QualityLevel.AVERAGE
        else:
            return QualityLevel.POOR
    
    def _generate_suggestions(
        self,
        dimension_scores: Dict[str, float],
        issues: List[QualityIssue]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 按维度得分生成建议
        if dimension_scores.get("credibility", 1) < 0.5:
            suggestions.append("可信度较低：删除夸张数字和空洞形容词，增加具体案例或数据支撑")
        
        if dimension_scores.get("uniqueness", 1) < 0.5:
            suggestions.append("独特性不足：突出差异化卖点（如活体知识系统、本地数据主权），避免与竞品雷同")
        
        if dimension_scores.get("utility", 1) < 0.5:
            suggestions.append("效用不明确：添加具体使用场景和操作步骤，让读者知道「我怎么用」")
        
        if dimension_scores.get("engagement", 1) < 0.4:
            suggestions.append("吸引力一般：可适当增加钩子开头，但不要牺牲可信度")
        
        # 从严重问题中提取建议
        critical_issues = [i for i in issues if i.severity == "critical"]
        for issue in critical_issues[:2]:
            if issue.suggestion:
                suggestions.append(f"【重点修改】{issue.suggestion}")
        
        return suggestions[:5]  # 最多返回5条建议


# 便捷函数
async def assess_content_quality(
    content: str,
    content_type: str = "marketing",
    competitor_content: Optional[List[str]] = None
) -> QualityAssessment:
    """
    评估内容质量的便捷函数
    
    Args:
        content: 待评估内容
        content_type: 内容类型
        competitor_content: 竞品内容列表
        
    Returns:
        QualityAssessment 评估结果
        
    示例:
        >>> result = await assess_content_quality("这款神器让你效率提升10倍！")
        >>> print(result.quality_level)  # QualityLevel.POOR
        >>> print(result.suggestions)
    """
    assessor = ContentQualityAssessorSkill()
    return await assessor.assess_content(
        content=content,
        content_type=ContentType(content_type),
        competitor_content=competitor_content or []
    )


async def rewrite_with_quality_guidance(
    content: str,
    target_score: float = 0.7
) -> Dict[str, Any]:
    """
    评估并生成重写指导
    
    返回评估结果和针对性的重写 prompt
    """
    assessment = await assess_content_quality(content)
    
    rewrite_prompt = f"""重写以下推广文案，要求：
1. 删掉所有「神器」「救星」「超厉害」等空洞形容词
2. 用一个具体场景替代功能列表（比如：研究生写文献综述）
3. 差异化卖点聚焦在「活体知识系统」——它会自己进化，不是死工具
4. 长度控制在 150 字以内
5. 必须包含明确的行动指引（如 GitHub 链接）

当前评分：{assessment.overall_score:.2f}（目标：{target_score}）
问题维度：{', '.join(d for d, s in assessment.dimension_scores.items() if s < 0.5)}

原文案：
{content}
"""
    
    return {
        "current_assessment": assessment.to_dict(),
        "rewrite_prompt": rewrite_prompt,
        "key_issues": [i.description for i in assessment.issues if i.severity == "critical"]
    }


# NotebookLM 竞品功能列表（用于独特性对比）
NOTEBOOKLM_FEATURES = [
    "上传文档", "生成摘要", "问答对话", "播客生成",
    "引用来源", "多文档", "AI助手", "笔记整理"
]


def get_differentiation_keywords() -> List[str]:
    """获取 Open Notebook 差异化关键词"""
    return [
        "活体知识系统",
        "五层架构",
        "本地部署",
        "数据主权",
        "持续学习",
        "个性化进化",
        "10大AI技能",
        "知识图谱可视化",
        "批量导入",
        "跨文档洞察",
    ]
