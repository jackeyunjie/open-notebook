"""
UI Integration - 前端 UI 集成工具

功能:
1. API 路由自动生成
2. 快捷按钮配置
3. 用户体验流程优化
4. 实时通知和进度追踪
5. 错误处理和用户反馈
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from loguru import logger


class ActionType(str, Enum):
    """操作类型"""
    GENERATE_REPORT = "generate_report"
    ANALYZE_CROSS_DOCS = "analyze_cross_docs"
    VISUALIZE_KNOWLEDGE = "visualize_knowledge"
    BATCH_IMPORT = "batch_import"
    EXPORT_DATA = "export_data"


@dataclass
class ActionConfig:
    """操作配置"""
    action_type: ActionType
    label: str
    icon: str
    description: str
    handler: Callable
    parameters: Dict[str, Any]
    confirm_required: bool = False
    show_progress: bool = True
    success_message: Optional[str] = None
    error_message: Optional[str] = None


class UIManager:
    """UI 管理器"""
    
    def __init__(self):
        self.actions: Dict[str, ActionConfig] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_progress: Dict[str, Dict[str, Any]] = {}
        
    def register_action(
        self,
        action_type: ActionType,
        label: str,
        icon: str,
        description: str,
        handler: Callable,
        parameters: Optional[Dict[str, Any]] = None,
        confirm_required: bool = False,
        success_message: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """注册 UI 操作
        
        Args:
            action_type: 操作类型
            label: 按钮标签
            icon: 图标名称
            description: 操作描述
            handler: 处理函数
            parameters: 参数字典
            confirm_required: 是否需要确认
            success_message: 成功消息
            error_message: 失败消息
        """
        config = ActionConfig(
            action_type=action_type,
            label=label,
            icon=icon,
            description=description,
            handler=handler,
            parameters=parameters or {},
            confirm_required=confirm_required,
            show_progress=True,
            success_message=success_message,
            error_message=error_message
        )
        
        self.actions[action_type.value] = config
        logger.info(f"Registered UI action: {label}")
    
    async def execute_action(
        self,
        action_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """执行操作
        
        Args:
            action_type: 操作类型
            **kwargs: 传递给处理函数的参数
            
        Returns:
            执行结果
        """
        if action_type not in self.actions:
            raise ValueError(f"Unknown action type: {action_type}")
        
        config = self.actions[action_type]
        task_id = f"{action_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            logger.info(f"Executing action: {config.label}")
            
            # 创建异步任务
            async def task_wrapper():
                self.task_progress[task_id] = {
                    'status': 'running',
                    'progress': 0,
                    'message': 'Starting...',
                    'started_at': datetime.now()
                }
                
                try:
                    result = await config.handler(**kwargs)
                    
                    self.task_progress[task_id] = {
                        'status': 'completed',
                        'progress': 100,
                        'message': config.success_message or 'Completed!',
                        'completed_at': datetime.now(),
                        'result': result
                    }
                    
                    return result
                    
                except Exception as e:
                    self.task_progress[task_id] = {
                        'status': 'failed',
                        'progress': 0,
                        'message': config.error_message or f'Error: {str(e)}',
                        'failed_at': datetime.now(),
                        'error': str(e)
                    }
                    raise
            
            task = asyncio.create_task(task_wrapper())
            self.active_tasks[task_id] = task
            
            return {
                'task_id': task_id,
                'status': 'started',
                'message': f'{config.label} started'
            }
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            raise
    
    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """获取任务进度"""
        return self.task_progress.get(task_id, {
            'status': 'not_found',
            'progress': 0,
            'message': 'Task not found'
        })
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled task: {task_id}")
                return True
        return False
    
    def get_available_actions(self) -> List[Dict[str, Any]]:
        """获取可用操作列表"""
        return [
            {
                'type': action.action_type.value,
                'label': action.label,
                'icon': action.icon,
                'description': action.description,
                'parameters': action.parameters,
                'confirm_required': action.confirm_required
            }
            for action in self.actions.values()
        ]


# ============================================================================
# Pre-configured Actions for P0/P1 Features
# ============================================================================

def setup_p0_p1_actions(ui_manager: UIManager):
    """设置 P0/P1 功能的 UI 操作"""
    
    # 1. 一键报告生成器动作
    ui_manager.register_action(
        action_type=ActionType.GENERATE_REPORT,
        label="📊 一键生成报告",
        icon="chart-bar",
        description="基于当前 Notebook 内容，自动生成结构化研究报告",
        handler=None,  # 由前端指定具体处理函数
        parameters={
            'report_types': [
                {'value': 'study_guide', 'label': '学习指南'},
                {'value': 'literature_review', 'label': '文献综述'},
                {'value': 'research_digest', 'label': '研究简报'},
                {'value': 'weekly_trends', 'label': '周度趋势'},
                {'value': 'concept_map', 'label': '概念图谱'}
            ],
            'notebook_id': {'type': 'string', 'required': True},
            'source_ids': {'type': 'array', 'required': False}
        },
        confirm_required=False,
        success_message="✅ 报告已生成并保存到笔记",
        error_message="❌ 报告生成失败"
    )
    
    # 2. 跨文档洞察动作
    ui_manager.register_action(
        action_type=ActionType.ANALYZE_CROSS_DOCS,
        label="🔍 跨文档分析",
        icon="search",
        description="分析多个文档之间的共性、矛盾和趋势",
        handler=None,
        parameters={
            'analysis_types': [
                {'value': 'common_themes', 'label': '共同主题'},
                {'value': 'contradictions', 'label': '矛盾检测'},
                {'value': 'trends', 'label': '趋势识别'},
                {'value': 'full_report', 'label': '完整报告'}
            ],
            'notebook_id': {'type': 'string', 'required': True},
            'days': {'type': 'integer', 'default': 7, 'label': '分析天数'}
        },
        confirm_required=False,
        success_message="✅ 分析完成",
        error_message="❌ 分析失败"
    )
    
    # 3. 可视化图谱动作
    ui_manager.register_action(
        action_type=ActionType.VISUALIZE_KNOWLEDGE,
        label="🗺️ 知识可视化",
        icon="project-diagram",
        description="生成思维导图、时间线、网络图等可视化图表",
        handler=None,
        parameters={
            'chart_types': [
                {'value': 'mindmap', 'label': '思维导图'},
                {'value': 'timeline', 'label': '时间线'},
                {'value': 'network', 'label': '网络图'},
                {'value': 'bar_chart', 'label': '柱状图'},
                {'value': 'pie_chart', 'label': '饼图'}
            ],
            'notebook_id': {'type': 'string', 'required': True},
            'export_format': {'type': 'string', 'default': 'html', 'options': ['html', 'markdown']}
        },
        confirm_required=False,
        success_message="✅ 图表已生成",
        error_message="❌ 图表生成失败"
    )
    
    # 4. 批量导入动作
    ui_manager.register_action(
        action_type=ActionType.BATCH_IMPORT,
        label="📁 批量导入",
        icon="upload",
        description="批量导入文件、URL 或文献库（Zotero/Mendeley）",
        handler=None,
        parameters={
            'import_types': [
                {'value': 'folder', 'label': '文件夹'},
                {'value': 'urls', 'label': 'URL 列表'},
                {'value': 'zotero', 'label': 'Zotero 导出'},
                {'value': 'mendeley', 'label': 'Mendeley 导出'}
            ],
            'notebook_id': {'type': 'string', 'required': True},
            'source_path': {'type': 'string', 'required': False},
            'recursive': {'type': 'boolean', 'default': True}
        },
        confirm_required=True,
        success_message="✅ 批量导入完成",
        error_message="❌ 批量导入失败"
    )
    
    # 5. 数据导出动作
    ui_manager.register_action(
        action_type=ActionType.EXPORT_DATA,
        label="💾 导出数据",
        icon="download",
        description="导出研究报告、可视化图表和分析结果",
        handler=None,
        parameters={
            'export_formats': [
                {'value': 'markdown', 'label': 'Markdown'},
                {'value': 'html', 'label': 'HTML'},
                {'value': 'pdf', 'label': 'PDF'}
            ],
            'content_types': [
                {'value': 'reports', 'label': '研究报告'},
                {'value': 'visualizations', 'label': '可视化图表'},
                {'value': 'raw_data', 'label': '原始数据'}
            ],
            'notebook_id': {'type': 'string', 'required': True}
        },
        confirm_required=False,
        success_message="✅ 导出成功",
        error_message="❌ 导出失败"
    )
    
    logger.info("P0/P1 UI actions registered successfully")


# ============================================================================
# Progress Notification System
# ============================================================================

class NotificationType(str, Enum):
    """通知类型"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"


@dataclass
class Notification:
    """通知消息"""
    type: NotificationType
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration: int = 5000  # 显示时长（毫秒）
    actionable: bool = False
    actions: List[Dict[str, str]] = field(default_factory=list)


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.notifications: List[Notification] = []
        self.subscribers: List[Callable] = []
        
    def subscribe(self, callback: Callable):
        """订阅通知"""
        self.subscribers.append(callback)
    
    def notify(
        self,
        type: NotificationType,
        title: str,
        message: str,
        duration: int = 5000,
        actions: Optional[List[Dict[str, str]]] = None
    ):
        """发送通知"""
        notification = Notification(
            type=type,
            title=title,
            message=message,
            duration=duration,
            actionable=actions is not None,
            actions=actions or []
        )
        
        self.notifications.append(notification)
        
        # 通知所有订阅者
        for callback in self.subscribers:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Notification callback error: {e}")
        
        logger.debug(f"Notification sent: [{type.value}] {title}")
    
    def info(self, title: str, message: str):
        """信息通知"""
        self.notify(NotificationType.INFO, title, message)
    
    def success(self, title: str, message: str):
        """成功通知"""
        self.notify(NotificationType.SUCCESS, title, message, duration=3000)
    
    def warning(self, title: str, message: str):
        """警告通知"""
        self.notify(NotificationType.WARNING, title, message, duration=8000)
    
    def error(self, title: str, message: str, actions: Optional[List[Dict[str, str]]] = None):
        """错误通知"""
        self.notify(NotificationType.ERROR, title, message, duration=10000, actions=actions)
    
    def progress(
        self,
        title: str,
        message: str,
        progress_percent: float,
        task_id: Optional[str] = None
    ):
        """进度通知"""
        notification = Notification(
            type=NotificationType.PROGRESS,
            title=title,
            message=f"{message} ({progress_percent:.0f}%)"
        )
        
        self.notifications.append(notification)
        
        for callback in self.subscribers:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")


# ============================================================================
# Global Instances
# ============================================================================

ui_manager = UIManager()
notification_manager = NotificationManager()

# 自动注册 P0/P1 操作
setup_p0_p1_actions(ui_manager)


# ============================================================================
# Convenience Functions
# ============================================================================

def get_ui_actions() -> List[Dict[str, Any]]:
    """获取所有可用的 UI 操作"""
    return ui_manager.get_available_actions()


async def execute_ui_action(action_type: str, **kwargs) -> Dict[str, Any]:
    """执行 UI 操作"""
    return await ui_manager.execute_action(action_type, **kwargs)


def send_notification(
    type: str,
    title: str,
    message: str,
    duration: int = 5000
):
    """发送通知"""
    notification_type = NotificationType(type.lower())
    notification_manager.notify(notification_type, title, message, duration)


def get_task_progress(task_id: str) -> Dict[str, Any]:
    """获取任务进度"""
    return ui_manager.get_task_progress(task_id)
