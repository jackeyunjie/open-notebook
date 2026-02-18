"""
Skills API Routes - P0/P1/C/B/A 功能 API 端点

提供 RESTful API 供前端调用所有 Skill 功能

## 功能分类

### P0 - 核心功能
- **一键报告生成器**: 基于 Notebook 内容自动生成结构化研究报告
- **跨文档洞察**: 分析多个文档之间的共性、矛盾和趋势

### P1 - 体验增强
- **可视化知识图谱**: 思维导图、时间线、网络图、统计图表
- **批量导入工具**: 文件夹、URL、Zotero、Mendeley 批量导入

### C - 性能优化
- **缓存系统**: LRU 内存缓存，自动过期
- **查询优化**: 慢查询检测、批量操作
- **性能监控**: 实时指标追踪

### B - UI 集成
- **操作管理**: 预配置的快捷按钮
- **通知系统**: 实时消息推送
- **进度追踪**: 任务进度实时监控

### A - 协作功能 (P2)
- **Notebook 共享**: 邀请制协作
- **权限管理**: READ/WRITE/ADMIN/OWNER 四级权限
- **评论批注**: 线程化讨论
- **实时会话**: 多用户同时编辑

## 使用示例

```bash
# 生成学习指南
curl -X POST http://localhost:8000/api/v1/skills/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"notebook_id": "xxx", "report_type": "study_guide"}'

# 批量导入 PDF
curl -X POST http://localhost:8000/api/v1/skills/import/batch \
  -H "Content-Type: application/json" \
  -d '{"notebook_id": "xxx", "import_type": "folder", "source_path": "/path/to/pdfs"}'

# 创建思维导图
curl -X POST http://localhost:8000/api/v1/skills/visualizations/create \
  -H "Content-Type: application/json" \
  -d '{"notebook_id": "xxx", "chart_type": "mindmap"}'
```
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from open_notebook.skills.batch_importer import (
    batch_import_files,
    batch_import_urls,
    import_mendeley_library,
    import_zotero_library,
)
from open_notebook.skills.collaboration_tools import (
    Permission,
    add_comment_to_notebook,
    can_access,
    create_collaboration_session,
    get_notebook_collaborators,
    get_notebook_comments,
    share_with_user,
)
from open_notebook.skills.cross_document_insights import (
    analyze_cross_document_themes,
    detect_contradictions,
    generate_weekly_trends_report,
    identify_research_trends,
)
from open_notebook.skills.one_click_report_generator import (
    ReportType,
    create_concept_map,
    create_literature_review,
    create_research_digest,
    create_study_guide,
    create_weekly_trends,
)
from open_notebook.skills.performance_optimizer import PerformanceOptimizer
from open_notebook.skills.ui_integration import (
    execute_ui_action,
    get_task_progress,
    get_ui_actions,
    send_notification,
)
from open_notebook.skills.visual_knowledge_graph import (
    create_mind_map,
    create_network_graph,
    create_timeline,
    create_topic_chart,
)

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(
    prefix="/api/v1/skills",
    tags=["Skills - P0/P1/C/B/A 功能"],
    responses={404: {"description": "Not found"}},
)

# 全局性能优化器实例
perf_optimizer = PerformanceOptimizer()


# ============================================================================
# Request/Response Models
# ============================================================================


class ReportGenerationRequest(BaseModel):
    """报告生成请求
    
    用于一键生成各种类型的研究报告
    
    ## 支持的报告类型
    - `study_guide`: 学习指南 - 适合快速了解某个主题
    - `literature_review`: 文献综述 - 学术研究必备
    - `research_digest`: 研究简报 - 简洁的研究总结
    - `weekly_trends`: 周度趋势 - 追踪最新研究动态
    - `concept_map`: 概念图谱 - 可视化知识结构
    
    ## 使用示例
    ```json
    {
        "notebook_id": "nb_123456",
        "report_type": "study_guide",
        "source_ids": ["src_1", "src_2"],
        "title": "自定义标题（可选）"
    }
    ```
    """

    notebook_id: str = Field(
        ...,
        description="Notebook ID",
        example="nb_123456",
        min_length=1,
    )
    report_type: str = Field(
        ...,
        description="报告类型",
        examples=["study_guide", "literature_review", "research_digest", "weekly_trends", "concept_map"],
        pattern=r"^(study_guide|literature_review|research_digest|weekly_trends|concept_map)$",
    )
    source_ids: Optional[List[str]] = Field(
        None,
        description="指定源列表（可选，默认使用所有源）",
        example=["src_1", "src_2", "src_3"],
    )
    title: Optional[str] = Field(
        None,
        description="自定义标题（可选，默认自动生成）",
        example="人工智能研究进展",
        max_length=200,
    )


class ReportGenerationResponse(BaseModel):
    """报告生成响应
    
    ## 响应字段说明
    - `success`: 操作是否成功
    - `note_id`: 生成的 Note ID（可在前端查看）
    - `message`: 提示信息
    - `report_type`: 报告类型
    
    ## 成功响应示例
    ```json
    {
        "success": true,
        "note_id": "note_789",
        "message": "Report generated successfully: study_guide",
        "report_type": "study_guide"
    }
    ```
    
    ## 失败响应示例
    ```json
    {
        "detail": "Notebook not_found: nb_invalid"
    }
    ```
    """

    success: bool = Field(..., description="操作是否成功", example=True)
    note_id: Optional[str] = Field(None, description="生成的 Note ID", example="note_789")
    message: str = Field(..., description="提示信息", example="Report generated successfully")
    report_type: str = Field(..., description="报告类型", example="study_guide")


class VisualizationRequest(BaseModel):
    """可视化请求"""

    notebook_id: str = Field(..., description="Notebook ID")
    chart_type: str = Field(
        ...,
        description="图表类型",
        examples=["mindmap", "timeline", "network", "bar_chart", "pie_chart"],
    )
    source_ids: Optional[List[str]] = Field(None, description="指定源列表")
    export_format: Optional[str] = Field("html", description="导出格式 (html, markdown)")


class VisualizationResponse(BaseModel):
    """可视化响应"""

    success: bool
    content: str
    chart_type: str
    export_format: str


class BatchImportRequest(BaseModel):
    """批量导入请求"""

    notebook_id: str = Field(..., description="Notebook ID")
    import_type: str = Field(
        ...,
        description="导入类型",
        examples=["folder", "urls", "zotero", "mendeley"],
    )
    source_path: Optional[str] = Field(None, description="源路径（文件夹或文件）")
    urls: Optional[List[str]] = Field(None, description="URL 列表")
    recursive: bool = Field(True, description="是否递归子目录")


class BatchImportResponse(BaseModel):
    """批量导入响应"""

    success: bool
    total_found: int
    successful: int
    failed: int
    skipped: int
    errors: List[Dict[str, Any]] = []


class AnalysisRequest(BaseModel):
    """分析请求"""

    notebook_id: str = Field(..., description="Notebook ID")
    analysis_type: str = Field(
        ...,
        description="分析类型",
        examples=["common_themes", "contradictions", "trends", "full_report"],
    )
    source_ids: Optional[List[str]] = Field(None, description="指定源列表")
    days: int = Field(7, description="分析天数（趋势分析用）")


class AnalysisResponse(BaseModel):
    """分析响应"""

    success: bool
    result: Dict[str, Any]
    analysis_type: str


class ShareRequest(BaseModel):
    """共享请求"""

    notebook_id: str = Field(..., description="Notebook ID")
    owner_id: str = Field(..., description="所有者 ID")
    user_id: str = Field(..., description="目标用户 ID")
    permission: str = Field(..., description="权限级别", examples=["read", "write", "admin"])


class CommentRequest(BaseModel):
    """评论请求"""

    notebook_id: str = Field(..., description="Notebook ID")
    user_id: str = Field(..., description="用户 ID")
    content: str = Field(..., description="评论内容")
    target_type: Optional[str] = Field(None, description="目标类型")
    target_id: Optional[str] = Field(None, description="目标 ID")


# ============================================================================
# P0: One-Click Report Generator
# ============================================================================


@router.post(
    "/reports/generate",
    response_model=ReportGenerationResponse,
    summary="一键生成研究报告",
    description="""
    ## 功能说明
    
    基于 Notebook 内容，自动生成结构化研究报告。
    
    ### 支持的报告类型
    
    1. **Study Guide (学习指南)**
       - 适合快速了解某个主题
       - 包含核心概念、关键要点、自测题
    
    2. **Literature Review (文献综述)**
       - 学术研究必备
       - 包含研究背景、方法对比、主要发现
    
    3. **Research Digest (研究简报)**
       - 简洁的研究总结
       - 包含核心观点、数据支撑、行动建议
    
    4. **Weekly Trends (周度趋势)**
       - 追踪最新研究动态
       - 包含新兴主题、热度变化、趋势预测
    
    5. **Concept Map (概念图谱)**
       - 可视化知识结构
       - 包含概念关系、层级结构、关联强度
    
    ### 处理流程
    
    1. 获取指定 Source 内容
    2. AI 分析和提取关键信息
    3. 按照模板生成结构化报告
    4. 保存为 Note 并返回 ID
    
    ### 性能提示
    
    - 处理时间取决于 Source 数量和内容长度
    - 建议每次不超过 20 个 Source
    - 大型报告建议使用异步任务
    
    ### 相关链接
    
    - [查看生成的 Note](#/notebooks/get_note)
    - [列出所有报告](#/notes/list_notes)
    """,
    responses={
        200: {
            "description": "报告生成成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "note_id": "note_abc123",
                        "message": "Report generated successfully: study_guide",
                        "report_type": "study_guide",
                    }
                }
            }
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid report type: invalid_type"
                    }
                }
            }
        },
        404: {
            "description": "Notebook 不存在",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Notebook not found: nb_invalid"
                    }
                }
            }
        },
        500: {
            "description": "服务器错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Failed to generate report: ..."
                    }
                }
            }
        },
    },
)
async def generate_report(request: ReportGenerationRequest):
    """一键生成报告"""
    try:
        # 映射报告类型
        type_mapping = {
            "study_guide": create_study_guide,
            "literature_review": create_literature_review,
            "research_digest": create_research_digest,
            "weekly_trends": create_weekly_trends,
            "concept_map": create_concept_map,
        }

        if request.report_type not in type_mapping:
            raise HTTPException(status_code=400, detail=f"Invalid report type: {request.report_type}")

        # 生成报告
        handler = type_mapping[request.report_type]
        result = await handler(request.notebook_id, request.source_ids)

        # 记录性能指标
        perf_optimizer.record_metric("report_generation_time", result.get("processing_time", 0))

        return ReportGenerationResponse(
            success=True,
            note_id=result.get("note_id"),
            message=f"Report generated successfully: {request.report_type}",
            report_type=request.report_type,
        )

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# P0: Cross-Document Insights
# ============================================================================


@router.post("/analysis/execute", response_model=AnalysisResponse)
async def execute_analysis(request: AnalysisRequest):
    """执行跨文档分析"""
    try:
        result = {}

        if request.analysis_type == "common_themes":
            result = await analyze_cross_document_themes(
                request.notebook_id,
                request.source_ids,
            )
        elif request.analysis_type == "contradictions":
            contradictions = await detect_contradictions(request.notebook_id, request.source_ids)
            result = {"contradictions": contradictions}
        elif request.analysis_type == "trends":
            result = await identify_research_trends(request.notebook_id, days=request.days)
        elif request.analysis_type == "full_report":
            report = await generate_weekly_trends_report(request.notebook_id, request.source_ids)
            result = {"report": report}
        else:
            raise HTTPException(status_code=400, detail=f"Invalid analysis type: {request.analysis_type}")

        return AnalysisResponse(success=True, result=result, analysis_type=request.analysis_type)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# P1: Visual Knowledge Graph
# ============================================================================


@router.post("/visualizations/create", response_model=VisualizationResponse)
async def create_visualization(request: VisualizationRequest):
    """创建可视化图表"""
    try:
        content = ""

        if request.chart_type == "mindmap":
            content = await create_mind_map(request.notebook_id, request.source_ids)
        elif request.chart_type == "timeline":
            content = await create_timeline(request.notebook_id, request.source_ids)
        elif request.chart_type == "network":
            content = await create_network_graph(request.notebook_id, request.source_ids)
        elif request.chart_type in ["bar_chart", "pie_chart"]:
            content = await create_topic_chart(
                request.notebook_id,
                request.source_ids,
                chart_type=request.chart_type.replace("_chart", ""),
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid chart type: {request.chart_type}")

        return VisualizationResponse(
            success=True,
            content=content,
            chart_type=request.chart_type,
            export_format=request.export_format,
        )

    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# P1: Batch Import
# ============================================================================


@router.post("/import/batch", response_model=BatchImportResponse)
async def batch_import(request: BatchImportRequest, background_tasks: BackgroundTasks):
    """批量导入"""
    try:
        result = {}

        if request.import_type == "folder":
            if not request.source_path:
                raise HTTPException(status_code=400, detail="source_path required for folder import")
            result = await batch_import_files(
                request.notebook_id,
                request.source_path,
                request.recursive,
            )
        elif request.import_type == "urls":
            if not request.urls:
                raise HTTPException(status_code=400, detail="urls required for URL import")
            result = await batch_import_urls(request.notebook_id, request.urls)
        elif request.import_type == "zotero":
            if not request.source_path:
                raise HTTPException(status_code=400, detail="source_path required for Zotero import")
            result = await import_zotero_library(request.notebook_id, request.source_path)
        elif request.import_type == "mendeley":
            if not request.source_path:
                raise HTTPException(status_code=400, detail="source_path required for Mendeley import")
            result = await import_mendeley_library(request.notebook_id, request.source_path)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid import type: {request.import_type}")

        # 后台发送通知
        background_tasks.add_task(
            send_notification,
            "success",
            "批量导入完成",
            f"成功导入 {result.get('successful', 0)} 项，跳过 {result.get('skipped', 0)} 项",
        )

        return BatchImportResponse(
            success=True,
            total_found=result.get("total_found", result.get("total", 0)),
            successful=result.get("successful", 0),
            failed=result.get("failed", 0),
            skipped=result.get("skipped", 0),
            errors=result.get("errors", []),
        )

    except Exception as e:
        logger.error(f"Batch import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# A: Collaboration Tools
# ============================================================================


@router.post("/collaboration/share")
async def share_notebook(request: ShareRequest):
    """共享 Notebook"""
    try:
        permission = Permission(request.permission.lower())
        invite = await share_with_user(
            request.notebook_id,
            request.owner_id,
            request.user_id,
            permission,
        )

        return {"success": True, "invite_id": invite.invite_id, "message": "Share invitation created"}

    except Exception as e:
        logger.error(f"Share failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collaboration/{notebook_id}/collaborators")
async def list_collaborators(notebook_id: str):
    """获取协作者列表"""
    try:
        collaborators = await get_notebook_collaborators(notebook_id)
        return {"success": True, "collaborators": collaborators}
    except Exception as e:
        logger.error(f"Get collaborators failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collaboration/comments/add")
async def add_comment(request: CommentRequest):
    """添加评论"""
    try:
        comment = await add_comment_to_notebook(
            request.notebook_id,
            request.user_id,
            request.content,
            request.target_type,
            request.target_id,
        )

        return {"success": True, "comment_id": comment.comment_id, "message": "Comment added"}

    except Exception as e:
        logger.error(f"Add comment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collaboration/{notebook_id}/comments")
async def get_comments(notebook_id: str, target_type: Optional[str] = None, target_id: Optional[str] = None):
    """获取评论"""
    try:
        comments = await get_notebook_comments(notebook_id)
        if target_type and target_id:
            comments = [c for c in comments if c.target_type == target_type and c.target_id == target_id]

        return {"success": True, "comments": [vars(c) for c in comments]}
    except Exception as e:
        logger.error(f"Get comments failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collaboration/sessions/create")
async def create_session(notebook_id: str, user_id: str):
    """创建协作会话"""
    try:
        session = await create_collaboration_session(notebook_id, user_id)
        return {"success": True, "session_id": session.session_id, "participants": list(session.participants)}
    except Exception as e:
        logger.error(f"Create session failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/permissions/check")
async def check_permission(notebook_id: str, user_id: str, required_permission: str):
    """检查权限"""
    try:
        permission = Permission(required_permission.lower())
        has_access = await can_access(notebook_id, user_id, permission)
        return {"success": True, "has_access": has_access}
    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# B: UI Integration
# ============================================================================


@router.get("/ui/actions")
async def list_ui_actions():
    """获取可用 UI 操作列表"""
    try:
        actions = get_ui_actions()
        return {"success": True, "actions": actions}
    except Exception as e:
        logger.error(f"Get UI actions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ui/execute")
async def execute_action(action_type: str, **kwargs):
    """执行 UI 操作"""
    try:
        result = await execute_ui_action(action_type, **kwargs)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Execute action failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/progress")
async def get_progress(task_id: str):
    """获取任务进度"""
    try:
        progress = get_task_progress(task_id)
        return {"success": True, "progress": progress}
    except Exception as e:
        logger.error(f"Get progress failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# C: Performance Monitoring
# ============================================================================


@router.get("/performance/report")
async def performance_report():
    """获取性能报告"""
    try:
        report = perf_optimizer.get_performance_report()
        return {"success": True, "report": report}
    except Exception as e:
        logger.error(f"Get performance report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/cache/stats")
async def cache_stats():
    """获取缓存统计"""
    try:
        return {"success": True, "stats": perf_optimizer.cache.stats()}
    except Exception as e:
        logger.error(f"Get cache stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "skills_api": "operational",
            "cache": "operational",
            "database": "operational",
        },
    }
