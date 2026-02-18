"""
Collaboration Tools - 协作工具

功能:
1. Notebook 共享
2. 权限管理（读/写/管理员）
3. 变更历史记录
4. 实时协作编辑
5. 评论和批注
6. 团队成员管理
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from loguru import logger


class Permission(str, Enum):
    """权限级别"""
    READ = "read"           # 只读
    WRITE = "write"         # 可编辑
    ADMIN = "admin"         # 管理员
    OWNER = "owner"         # 所有者


class ChangeType(str, Enum):
    """变更类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SHARE = "share"
    PERMISSION_CHANGE = "permission_change"


@dataclass
class User:
    """用户"""
    user_id: str
    username: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ShareInvite:
    """共享邀请"""
    invite_id: str
    notebook_id: str
    inviter_id: str
    invitee_email: str
    permission: Permission
    status: str = "pending"  # pending, accepted, rejected
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class ChangeRecord:
    """变更记录"""
    record_id: str
    notebook_id: str
    user_id: str
    change_type: ChangeType
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Comment:
    """评论"""
    comment_id: str
    notebook_id: str
    user_id: str
    content: str
    target_type: Optional[str] = None  # 'source', 'note', 'section'
    target_id: Optional[str] = None
    parent_comment_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    is_resolved: bool = False


class CollaborationManager:
    """协作管理器"""
    
    def __init__(self):
        self.shares: Dict[str, Dict[str, Permission]] = {}  # notebook_id -> {user_id -> permission}
        self.invites: Dict[str, ShareInvite] = {}
        self.change_history: Dict[str, List[ChangeRecord]] = {}  # notebook_id -> [records]
        self.comments: Dict[str, List[Comment]] = {}  # notebook_id -> [comments]
        self.active_users: Dict[str, Set[str]] = {}  # notebook_id -> {user_ids}
        
    async def share_notebook(
        self,
        notebook_id: str,
        owner_id: str,
        target_user_id: str,
        permission: Permission
    ) -> ShareInvite:
        """共享 Notebook
        
        Args:
            notebook_id: Notebook ID
            owner_id: 所有者 ID
            target_user_id: 目标用户 ID
            permission: 权限级别
            
        Returns:
            共享邀请对象
        """
        invite_id = f"invite_{notebook_id}_{target_user_id}_{datetime.now().timestamp()}"
        
        invite = ShareInvite(
            invite_id=invite_id,
            notebook_id=notebook_id,
            inviter_id=owner_id,
            invitee_email=target_user_id,  # 简化处理，实际应该是邮箱
            permission=permission,
            expires_at=datetime.now().replace(hour=23, minute=59, second=59)
        )
        
        self.invites[invite_id] = invite
        
        # 记录变更
        await self._record_change(
            notebook_id=notebook_id,
            user_id=owner_id,
            change_type=ChangeType.SHARE,
            description=f"Shared with {target_user_id}",
            metadata={'target_user': target_user_id, 'permission': permission.value}
        )
        
        logger.info(f"Notebook {notebook_id} shared with {target_user_id} as {permission.value}")
        
        return invite
    
    async def accept_invite(self, invite_id: str, user_id: str) -> bool:
        """接受邀请"""
        if invite_id not in self.invites:
            raise ValueError(f"Invite not found: {invite_id}")
        
        invite = self.invites[invite_id]
        
        if invite.invitee_email != user_id:
            raise ValueError("User mismatch")
        
        if invite.status != "pending":
            raise ValueError(f"Invite already {invite.status}")
        
        # 更新状态
        invite.status = "accepted"
        
        # 添加权限
        if invite.notebook_id not in self.shares:
            self.shares[invite.notebook_id] = {}
        
        self.shares[invite.notebook_id][user_id] = invite.permission
        
        # 记录变更
        await self._record_change(
            notebook_id=invite.notebook_id,
            user_id=user_id,
            change_type=ChangeType.PERMISSION_CHANGE,
            description=f"Accepted invite with {invite.permission.value} permission"
        )
        
        logger.info(f"Invite {invite_id} accepted by {user_id}")
        
        return True
    
    async def check_permission(
        self,
        notebook_id: str,
        user_id: str,
        required_permission: Permission
    ) -> bool:
        """检查权限
        
        Args:
            notebook_id: Notebook ID
            user_id: 用户 ID
            required_permission: 需要的权限级别
            
        Returns:
            是否有权限
        """
        if notebook_id not in self.shares:
            return False
        
        user_permission = self.shares[notebook_id].get(user_id)
        
        if user_permission is None:
            return False
        
        # 权限等级比较
        permission_levels = {
            Permission.READ: 1,
            Permission.WRITE: 2,
            Permission.ADMIN: 3,
            Permission.OWNER: 4
        }
        
        return permission_levels[user_permission] >= permission_levels[required_permission]
    
    async def update_permission(
        self,
        notebook_id: str,
        admin_user_id: str,
        target_user_id: str,
        new_permission: Permission
    ):
        """更新用户权限"""
        # 验证管理员权限
        has_admin = await self.check_permission(
            notebook_id, admin_user_id, Permission.ADMIN
        )
        if not has_admin:
            raise PermissionError("Admin permission required")
        
        if notebook_id not in self.shares:
            self.shares[notebook_id] = {}
        
        self.shares[notebook_id][target_user_id] = new_permission
        
        # 记录变更
        await self._record_change(
            notebook_id=notebook_id,
            user_id=admin_user_id,
            change_type=ChangeType.PERMISSION_CHANGE,
            description=f"Updated permission for {target_user_id} to {new_permission.value}",
            metadata={'target_user': target_user_id, 'new_permission': new_permission.value}
        )
        
        logger.info(f"Permission updated for {target_user_id} in {notebook_id}")
    
    async def remove_access(
        self,
        notebook_id: str,
        admin_user_id: str,
        target_user_id: str
    ):
        """移除用户访问权限"""
        has_admin = await self.check_permission(
            notebook_id, admin_user_id, Permission.ADMIN
        )
        if not has_admin:
            raise PermissionError("Admin permission required")
        
        if notebook_id in self.shares and target_user_id in self.shares[notebook_id]:
            del self.shares[notebook_id][target_user_id]
            
            # 记录变更
            await self._record_change(
                notebook_id=notebook_id,
                user_id=admin_user_id,
                change_type=ChangeType.PERMISSION_CHANGE,
                description=f"Removed access for {target_user_id}"
            )
            
            logger.info(f"Access removed for {target_user_id} from {notebook_id}")
    
    async def get_collaborators(self, notebook_id: str) -> List[Dict[str, Any]]:
        """获取协作者列表"""
        if notebook_id not in self.shares:
            return []
        
        return [
            {'user_id': user_id, 'permission': perm.value}
            for user_id, perm in self.shares[notebook_id].items()
        ]
    
    async def _record_change(
        self,
        notebook_id: str,
        user_id: str,
        change_type: ChangeType,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """记录变更历史"""
        if notebook_id not in self.change_history:
            self.change_history[notebook_id] = []
        
        record = ChangeRecord(
            record_id=f"change_{notebook_id}_{datetime.now().timestamp()}",
            notebook_id=notebook_id,
            user_id=user_id,
            change_type=change_type,
            description=description,
            metadata=metadata or {}
        )
        
        self.change_history[notebook_id].append(record)
        
        # 保留最近 100 条记录
        if len(self.change_history[notebook_id]) > 100:
            self.change_history[notebook_id] = self.change_history[notebook_id][-100:]
    
    async def get_change_history(
        self,
        notebook_id: str,
        limit: int = 50
    ) -> List[ChangeRecord]:
        """获取变更历史"""
        records = self.change_history.get(notebook_id, [])
        return records[-limit:]
    
    async def add_comment(
        self,
        notebook_id: str,
        user_id: str,
        content: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        parent_comment_id: Optional[str] = None
    ) -> Comment:
        """添加评论"""
        comment_id = f"comment_{notebook_id}_{datetime.now().timestamp()}"
        
        comment = Comment(
            comment_id=comment_id,
            notebook_id=notebook_id,
            user_id=user_id,
            content=content,
            target_type=target_type,
            target_id=target_id,
            parent_comment_id=parent_comment_id
        )
        
        if notebook_id not in self.comments:
            self.comments[notebook_id] = []
        
        self.comments[notebook_id].append(comment)
        
        logger.info(f"Comment added to {notebook_id}")
        
        return comment
    
    async def get_comments(
        self,
        notebook_id: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None
    ) -> List[Comment]:
        """获取评论"""
        all_comments = self.comments.get(notebook_id, [])
        
        if target_type and target_id:
            return [c for c in all_comments if c.target_type == target_type and c.target_id == target_id]
        
        return all_comments
    
    async def resolve_comment(self, comment_id: str, user_id: str) -> bool:
        """解决评论"""
        for comments_list in self.comments.values():
            for comment in comments_list:
                if comment.comment_id == comment_id:
                    comment.is_resolved = True
                    comment.updated_at = datetime.now()
                    logger.info(f"Comment {comment_id} resolved")
                    return True
        return False
    
    async def mark_user_active(self, notebook_id: str, user_id: str):
        """标记用户为活跃状态"""
        if notebook_id not in self.active_users:
            self.active_users[notebook_id] = set()
        
        self.active_users[notebook_id].add(user_id)
    
    async def get_active_users(self, notebook_id: str) -> Set[str]:
        """获取活跃用户"""
        return self.active_users.get(notebook_id, set())
    
    async def mark_user_inactive(self, notebook_id: str, user_id: str):
        """标记用户为非活跃状态"""
        if notebook_id in self.active_users:
            self.active_users[notebook_id].discard(user_id)


# ============================================================================
# Real-time Collaboration Session
# ============================================================================

class CollaborationSession:
    """实时协作会话"""
    
    def __init__(self, session_id: str, notebook_id: str):
        self.session_id = session_id
        self.notebook_id = notebook_id
        self.participants: Set[str] = set()
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
    async def join(self, user_id: str):
        """加入会话"""
        self.participants.add(user_id)
        self.last_activity = datetime.now()
        logger.info(f"User {user_id} joined session {self.session_id}")
    
    async def leave(self, user_id: str):
        """离开会话"""
        self.participants.discard(user_id)
        self.last_activity = datetime.now()
        logger.info(f"User {user_id} left session {self.session_id}")
    
    async def broadcast(self, message: Dict[str, Any], exclude_user: Optional[str] = None):
        """广播消息给所有参与者"""
        # 实际实现应该通过 WebSocket 推送
        participants = self.participants - ({exclude_user} if exclude_user else set())
        logger.info(f"Broadcasting to {len(participants)} participants: {message}")
        return list(participants)
    
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """检查会话是否活跃"""
        return (datetime.now() - self.last_activity).total_seconds() < timeout_minutes * 60


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}
        
    async def create_session(self, notebook_id: str, user_id: str) -> CollaborationSession:
        """创建会话"""
        session_id = f"session_{notebook_id}_{datetime.now().timestamp()}"
        session = CollaborationSession(session_id, notebook_id)
        await session.join(user_id)
        self.sessions[session_id] = session
        
        logger.info(f"Session created: {session_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """关闭会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session closed: {session_id}")
    
    def cleanup_inactive_sessions(self, timeout_minutes: int = 60):
        """清理不活跃的会话"""
        inactive_sessions = [
            sid for sid, session in self.sessions.items()
            if not session.is_active(timeout_minutes)
        ]
        
        for session_id in inactive_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up inactive session: {session_id}")


# ============================================================================
# Global Instances
# ============================================================================

collaboration_manager = CollaborationManager()
session_manager = SessionManager()


# ============================================================================
# Convenience Functions
# ============================================================================

async def share_with_user(notebook_id: str, owner_id: str, user_id: str, permission: Permission) -> ShareInvite:
    """便捷函数：共享给指定用户"""
    return await collaboration_manager.share_notebook(notebook_id, owner_id, user_id, permission)


async def accept_share_invite(invite_id: str, user_id: str) -> bool:
    """便捷函数：接受共享邀请"""
    return await collaboration_manager.accept_invite(invite_id, user_id)


async def can_access(notebook_id: str, user_id: str, permission: Permission) -> bool:
    """便捷函数：检查访问权限"""
    return await collaboration_manager.check_permission(notebook_id, user_id, permission)


async def get_notebook_collaborators(notebook_id: str) -> List[Dict[str, Any]]:
    """便捷函数：获取协作者列表"""
    return await collaboration_manager.get_collaborators(notebook_id)


async def add_comment_to_notebook(notebook_id: str, user_id: str, content: str) -> Comment:
    """便捷函数：添加评论"""
    return await collaboration_manager.add_comment(notebook_id, user_id, content)


async def get_notebook_comments(notebook_id: str) -> List[Comment]:
    """便捷函数：获取评论"""
    return await collaboration_manager.get_comments(notebook_id)


async def create_collaboration_session(notebook_id: str, user_id: str) -> CollaborationSession:
    """便捷函数：创建协作会话"""
    return await session_manager.create_session(notebook_id, user_id)


async def get_collaboration_session(session_id: str) -> Optional[CollaborationSession]:
    """便捷函数：获取会话"""
    return await session_manager.get_session(session_id)
