"""API Router for Platform Account Management.

Provides endpoints to connect, sync, and manage social media platform accounts.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from open_notebook.domain.platform_connector import (
    PlatformAccount,
    PlatformContentData,
    PlatformType,
    ConnectorRegistry,
)
from open_notebook.skills.connectors import XiaohongshuConnector, WeiboConnector

router = APIRouter(prefix="/platform-accounts", tags=["Platform Accounts"])


# ============================================================================
# Pydantic Models
# ============================================================================

class ConnectAccountRequest(BaseModel):
    """Request to connect a platform account."""
    platform: str
    username: str = ""
    auth_type: str = "cookie"
    auth_data: Dict[str, Any]
    profile_id: Optional[str] = None


class SyncResponse(BaseModel):
    """Response from sync operation."""
    status: str
    content_count: int
    error: Optional[str] = None


class PlatformInfoResponse(BaseModel):
    """Response with platform information."""
    platform: str
    name: str
    name_en: str
    auth_type: str
    content_types: List[str]
    features: List[str]


class AccountResponse(BaseModel):
    """Response with account details."""
    id: str
    platform: str
    username: str
    display_name: str
    is_authenticated: bool
    auto_sync: bool
    last_sync_at: Optional[str]
    last_sync_status: str
    total_content_fetched: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/platforms", summary="List Supported Platforms")
async def list_platforms():
    """List all supported platforms and their configurations."""
    from open_notebook.domain.platform_connector import PLATFORM_CONFIGS

    platforms = []
    for platform_type, config in PLATFORM_CONFIGS.items():
        platforms.append({
            "platform": platform_type.value,
            "name": config.get("name", ""),
            "name_en": config.get("name_en", ""),
            "auth_type": config.get("auth_type", {}).value if config.get("auth_type") else "",
            "content_types": config.get("content_types", []),
            "features": config.get("features", []),
        })

    return {"platforms": platforms}


@router.post("/connect", summary="Connect Platform Account")
async def connect_account(request: ConnectAccountRequest):
    """Connect a new social media account."""
    try:
        # Validate platform
        try:
            platform = PlatformType(request.platform)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {request.platform}")

        # Create account
        account = PlatformAccount(
            platform=request.platform,
            username=request.username,
            auth_type=request.auth_type,
            auth_data=request.auth_data,
            personal_ip_profile_id=request.profile_id,
            is_authenticated=False,
        )
        await account.save()

        # Test connection
        connector = ConnectorRegistry.get_connector(account)
        if not connector:
            raise HTTPException(status_code=400, detail=f"No connector available for {request.platform}")

        success, message = await connector.test_connection()

        if success:
            account.is_authenticated = True
            await account.save()

            # Trigger initial sync
            await connector.sync_content()

            return {
                "status": "connected",
                "account_id": str(account.id),
                "platform": request.platform,
                "message": message,
            }
        else:
            return {
                "status": "auth_failed",
                "account_id": str(account.id),
                "platform": request.platform,
                "message": message,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts", summary="List Connected Accounts")
async def list_accounts(profile_id: Optional[str] = None):
    """List all connected platform accounts."""
    try:
        # This would query the database with filter
        # For now, return all accounts
        accounts = await PlatformAccount.get_all()

        if profile_id:
            accounts = [a for a in accounts if a.personal_ip_profile_id == profile_id]

        return {
            "accounts": [
                {
                    "id": str(a.id),
                    "platform": a.platform,
                    "username": a.username,
                    "display_name": a.display_name,
                    "is_authenticated": a.is_authenticated,
                    "auto_sync": a.auto_sync,
                    "last_sync_at": a.last_sync_at.isoformat() if a.last_sync_at else None,
                    "last_sync_status": a.last_sync_status,
                    "total_content_fetched": a.total_content_fetched,
                }
                for a in accounts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}", summary="Get Account Details")
async def get_account(account_id: str):
    """Get detailed information about a connected account."""
    try:
        account = await PlatformAccount.get(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Get connector and fetch fresh profile
        connector = ConnectorRegistry.get_connector(account)
        profile = {}
        if connector:
            profile = await connector.get_user_profile()

        return {
            "account": {
                "id": str(account.id),
                "platform": account.platform,
                "username": account.username,
                "display_name": account.display_name,
                "avatar_url": account.avatar_url,
                "is_authenticated": account.is_authenticated,
                "auto_sync": account.auto_sync,
                "sync_frequency_hours": account.sync_frequency_hours,
                "last_sync_at": account.last_sync_at.isoformat() if account.last_sync_at else None,
                "last_sync_status": account.last_sync_status,
                "last_sync_error": account.last_sync_error,
                "total_content_fetched": account.total_content_fetched,
            },
            "profile": profile,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accounts/{account_id}/sync", response_model=SyncResponse, summary="Sync Account Content")
async def sync_account(account_id: str, background_tasks: BackgroundTasks):
    """Manually trigger content synchronization for an account."""
    try:
        account = await PlatformAccount.get(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        connector = ConnectorRegistry.get_connector(account)
        if not connector:
            raise HTTPException(status_code=400, detail="No connector available")

        # Perform sync
        count, error = await connector.sync_content()

        return SyncResponse(
            status="success" if error is None else "failed",
            content_count=count,
            error=error
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accounts/{account_id}/test", summary="Test Account Connection")
async def test_account_connection(account_id: str):
    """Test if account connection is working."""
    try:
        account = await PlatformAccount.get(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        connector = ConnectorRegistry.get_connector(account)
        if not connector:
            raise HTTPException(status_code=400, detail="No connector available")

        success, message = await connector.test_connection()

        return {
            "account_id": account_id,
            "is_connected": success,
            "message": message,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/accounts/{account_id}/settings", summary="Update Account Settings")
async def update_account_settings(
    account_id: str,
    auto_sync: Optional[bool] = None,
    sync_frequency_hours: Optional[int] = None
):
    """Update account synchronization settings."""
    try:
        account = await PlatformAccount.get(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        if auto_sync is not None:
            account.auto_sync = auto_sync
        if sync_frequency_hours is not None:
            account.sync_frequency_hours = sync_frequency_hours

        account.updated_at = datetime.utcnow()
        await account.save()

        return {
            "status": "updated",
            "account_id": account_id,
            "auto_sync": account.auto_sync,
            "sync_frequency_hours": account.sync_frequency_hours,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/accounts/{account_id}", summary="Disconnect Account")
async def disconnect_account(account_id: str):
    """Disconnect and delete a platform account."""
    try:
        account = await PlatformAccount.get(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        await account.delete()
        return {"status": "disconnected", "account_id": account_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}/content", summary="Get Account Content")
async def get_account_content(
    account_id: str,
    limit: int = 50,
    offset: int = 0,
    content_type: Optional[str] = None,
):
    """Get synchronized content from an account."""
    try:
        account = await PlatformAccount.get(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Query content from database
        # This would be a proper query in production
        contents = await PlatformContentData.get_all()
        contents = [c for c in contents if c.account_id == account_id]

        if content_type:
            contents = [c for c in contents if c.content_type == content_type]

        # Sort by created_at desc
        contents.sort(key=lambda x: x.platform_created_at or datetime.min, reverse=True)

        total = len(contents)
        contents = contents[offset:offset + limit]

        return {
            "content": [
                {
                    "id": str(c.id),
                    "platform_content_id": c.platform_content_id,
                    "title": c.title,
                    "content_type": c.content_type,
                    "platform_created_at": c.platform_created_at.isoformat() if c.platform_created_at else None,
                    "engagement": {
                        "views": c.views,
                        "likes": c.likes,
                        "comments": c.comments,
                        "shares": c.shares,
                        "saves": c.saves,
                    },
                    "platform_url": c.platform_url,
                    "quadrant": c.quadrant,
                }
                for c in contents
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}/analytics", summary="Get Account Analytics")
async def get_account_analytics(account_id: str):
    """Get analytics for a platform account."""
    try:
        account = await PlatformAccount.get(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        connector = ConnectorRegistry.get_connector(account)
        if not connector:
            raise HTTPException(status_code=400, detail="No connector available")

        analytics = await connector.fetch_analytics()

        if analytics:
            return analytics.to_dict()
        else:
            return {"error": "Failed to fetch analytics"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all", summary="Sync All Accounts")
async def sync_all_accounts(background_tasks: BackgroundTasks, profile_id: Optional[str] = None):
    """Trigger synchronization for all accounts."""
    try:
        accounts = await PlatformAccount.get_all()

        if profile_id:
            accounts = [a for a in accounts if a.personal_ip_profile_id == profile_id]

        results = []
        for account in accounts:
            if account.is_authenticated and account.auto_sync:
                connector = ConnectorRegistry.get_connector(account)
                if connector:
                    count, error = await connector.sync_content()
                    results.append({
                        "account_id": str(account.id),
                        "platform": account.platform,
                        "content_count": count,
                        "error": error,
                    })

        return {
            "status": "completed",
            "accounts_synced": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
