"""
Activity Monitor API - Receives activity data from browser extension.

This module provides endpoints for the OPC Activity Monitor browser extension
to sync user activity data for self-understanding and workflow optimization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

router = APIRouter(prefix="/activity", tags=["activity"])


class ActivityRecord(BaseModel):
    """Single activity record from browser extension."""
    url: str
    title: Optional[str] = None
    domain: str
    startTime: int
    endTime: int
    duration: int
    category: str = "other"
    date: str


class DailySummary(BaseModel):
    """Daily activity summary."""
    totalTime: int
    categoryTime: Dict[str, int]
    domainTime: List[List[Any]]  # [[domain, time], ...]
    activityCount: int


class ActivityLogRequest(BaseModel):
    """Request body for activity log endpoint."""
    date: str
    activities: List[ActivityRecord]
    summary: DailySummary
    timestamp: int


class ActivityInsight(BaseModel):
    """AI-generated insight about activity patterns."""
    type: str
    title: str
    description: str
    recommendation: Optional[str] = None
    created_at: datetime = datetime.now()


# In-memory storage for MVP (will be replaced with database)
# Structure: {user_id: {date: {activities: [], summary: {}, insights: []}}}
_activity_store: Dict[str, Dict[str, Dict[str, Any]]] = {}


@router.post("/log")
async def log_activity(data: ActivityLogRequest) -> Dict[str, Any]:
    """
    Receive activity log from browser extension.

    This endpoint is called every minute by the browser extension
to sync the user's activity data.
    """
    try:
        user_id = "default"  # TODO: Get from auth token

        if user_id not in _activity_store:
            _activity_store[user_id] = {}

        _activity_store[user_id][data.date] = {
            "activities": [a.dict() for a in data.activities],
            "summary": data.summary.dict(),
            "last_sync": datetime.now().isoformat()
        }

        # Generate insights if we have enough data
        insights = _generate_insights(data.summary)

        logger.debug(f"Activity logged for {data.date}: {len(data.activities)} activities")

        return {
            "status": "success",
            "activities_received": len(data.activities),
            "insights": insights
        }

    except Exception as e:
        logger.error(f"Error logging activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/today")
async def get_today_activity() -> Dict[str, Any]:
    """Get today's activity data."""
    user_id = "default"
    today = datetime.now().strftime("%Y-%m-%d")

    if user_id not in _activity_store or today not in _activity_store[user_id]:
        return {
            "date": today,
            "activities": [],
            "summary": {
                "totalTime": 0,
                "categoryTime": {},
                "domainTime": [],
                "activityCount": 0
            },
            "insights": []
        }

    return _activity_store[user_id][today]


@router.get("/history")
async def get_activity_history(days: int = 7) -> List[Dict[str, Any]]:
    """Get activity history for the last N days."""
    user_id = "default"

    if user_id not in _activity_store:
        return []

    # Get last N days
    all_dates = sorted(_activity_store[user_id].keys(), reverse=True)
    recent_dates = all_dates[:days]

    return [
        {
            "date": date,
            "summary": _activity_store[user_id][date].get("summary", {})
        }
        for date in recent_dates
    ]


@router.get("/insights")
async def get_insights() -> List[ActivityInsight]:
    """Get AI-generated insights about activity patterns."""
    # TODO: Integrate with LKS P1 Judgment Layer for real insights
    return [
        ActivityInsight(
            type="focus",
            title="深度工作建议",
            description="根据你的浏览模式，建议在上午10-12点安排重要创作任务。",
            recommendation="尝试在这个时段关闭社交媒体通知。"
        ),
        ActivityInsight(
            type="balance",
            title="内容消费与生产",
            description="今天的消费/生产比例为3:1，建议增加原创输出。",
            recommendation="将看到的有价值内容转化为自己的笔记或短内容。"
        )
    ]


@router.get("/patterns")
async def get_activity_patterns() -> Dict[str, Any]:
    """Get long-term activity patterns."""
    user_id = "default"

    if user_id not in _activity_store:
        return {"message": "Not enough data"}

    # Analyze patterns across all stored data
    all_data = _activity_store[user_id].values()

    # Calculate average daily metrics
    total_days = len(all_data)
    avg_activities = sum(d["summary"]["activityCount"] for d in all_data) / total_days if total_days > 0 else 0
    avg_time = sum(d["summary"]["totalTime"] for d in all_data) / total_days if total_days > 0 else 0

    # Find most productive category
    category_totals = {}
    for day in all_data:
        for cat, time in day["summary"].get("categoryTime", {}).items():
            category_totals[cat] = category_totals.get(cat, 0) + time

    top_category = max(category_totals.items(), key=lambda x: x[1]) if category_totals else ("none", 0)

    return {
        "total_days_tracked": total_days,
        "average_daily_activities": round(avg_activities, 1),
        "average_daily_time_hours": round(avg_time / 3600000, 1),
        "most_common_category": top_category[0],
        "category_breakdown": category_totals
    }


def _generate_insights(summary: DailySummary) -> List[Dict[str, Any]]:
    """Generate simple insights based on daily summary."""
    insights = []

    # Focus insight
    total_time = summary.totalTime
    if total_time > 0:
        # Find longest continuous activity (simplified)
        focus_ratio = summary.activityCount / (total_time / 60000) if total_time > 0 else 0

        if focus_ratio < 0.1:  # Less than 1 switch per 10 minutes
            insights.append({
                "type": "focus",
                "title": "深度工作状态",
                "message": "你今天保持了较好的专注度。"
            })
        elif focus_ratio > 0.5:  # More than 1 switch per 2 minutes
            insights.append({
                "type": "focus",
                "title": "频繁切换注意",
                "message": "尝试减少多任务切换，提升单一任务深度。"
            })

    # Category balance insight
    if summary.categoryTime:
        top_cat = max(summary.categoryTime.items(), key=lambda x: x[1])
        top_ratio = top_cat[1] / total_time if total_time > 0 else 0

        if top_ratio > 0.7:
            insights.append({
                "type": "balance",
                "title": "单一领域聚焦",
                "message": f"今天70%以上时间投入在{top_cat[0]}，适合攻坚深度任务。"
            })

    return insights


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for extension connectivity test."""
    return {"status": "ok", "service": "activity-monitor"}
