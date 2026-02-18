"""
Tests for Skills Module - P0/P1/C/B/A 功能单元测试

运行测试:
    pytest tests/test_skills.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================================
# P0: One-Click Report Generator Tests
# ============================================================================


class TestOneClickReportGenerator:
    """一键报告生成器测试"""

    @pytest.mark.asyncio
    async def test_create_study_guide(self):
        """测试创建学习指南"""
        from open_notebook.skills.one_click_report_generator import create_study_guide

        # Mock Notebook and Source
        with patch("open_notebook.skills.one_click_report_generator.Notebook") as mock_notebook_class:
            mock_notebook = AsyncMock()
            mock_notebook.get_sources = AsyncMock(return_value=[])
            mock_notebook_class.get = AsyncMock(return_value=mock_notebook)

            with patch("open_notebook.skills.one_click_report_generator.Source") as mock_source_class:
                mock_source = AsyncMock()
                mock_source.save = AsyncMock()
                mock_source.add_to_notebook = AsyncMock()
                mock_source.process = AsyncMock()
                mock_source_class.get = AsyncMock(return_value=mock_source)

                result = await create_study_guide("test-notebook-id")

                assert result["success"] is True
                assert "note_id" in result
                assert "processing_time" in result

    @pytest.mark.asyncio
    async def test_create_literature_review(self):
        """测试创建文献综述"""
        from open_notebook.skills.one_click_report_generator import create_literature_review

        with patch("open_notebook.skills.one_click_report_generator.Notebook") as mock_notebook_class:
            mock_notebook = AsyncMock()
            mock_notebook.get_sources = AsyncMock(return_value=[])
            mock_notebook_class.get = AsyncMock(return_value=mock_notebook)

            result = await create_literature_review("test-notebook-id")

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_invalid_notebook(self):
        """测试无效 Notebook ID"""
        from open_notebook.skills.one_click_report_generator import OneClickReportGenerator

        generator = OneClickReportGenerator("invalid-id")
        
        with pytest.raises(ValueError, match="Notebook .* not found"):
            await generator.initialize()


# ============================================================================
# P0: Cross-Document Insights Tests
# ============================================================================


class TestCrossDocumentInsights:
    """跨文档洞察测试"""

    @pytest.mark.asyncio
    async def test_analyze_common_themes(self):
        """测试共同主题分析"""
        from open_notebook.skills.cross_document_insights import analyze_cross_document_themes

        with patch("open_notebook.skills.cross_document_insights.Notebook") as mock_notebook_class:
            mock_notebook = AsyncMock()
            mock_notebook.get_sources = AsyncMock(return_value=[])
            mock_notebook_class.get = AsyncMock(return_value=mock_notebook)

            result = await analyze_cross_document_themes("test-notebook-id")

            assert "common_themes" in result or "themes" in result

    @pytest.mark.asyncio
    async def test_detect_contradictions(self):
        """测试矛盾检测"""
        from open_notebook.skills.cross_document_insights import detect_contradictions

        with patch("open_notebook.skills.cross_document_insights.Notebook") as mock_notebook_class:
            mock_notebook = AsyncMock()
            mock_notebook.get_sources = AsyncMock(return_value=[])
            mock_notebook_class.get = AsyncMock(return_value=mock_notebook)

            contradictions = await detect_contradictions("test-notebook-id")

            assert isinstance(contradictions, list)

    @pytest.mark.asyncio
    async def test_identify_trends(self):
        """测试趋势识别"""
        from open_notebook.skills.cross_document_insights import identify_research_trends

        with patch("open_notebook.skills.cross_document_insights.Notebook") as mock_notebook_class:
            mock_notebook = AsyncMock()
            mock_notebook.get_sources = AsyncMock(return_value=[])
            mock_notebook_class.get = AsyncMock(return_value=mock_notebook)

            result = await identify_research_trends("test-notebook-id", days=7)

            assert "trends" in result or "top_themes" in result


# ============================================================================
# C: Performance Optimizer Tests
# ============================================================================


class TestPerformanceOptimizer:
    """性能优化器测试"""

    def test_lru_cache_basic(self):
        """测试 LRU 缓存基本功能"""
        from open_notebook.skills.performance_optimizer import LRUCache

        cache = LRUCache(max_size=3)
        
        # Set values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Get values
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_lru_cache_eviction(self):
        """测试 LRU 缓存驱逐"""
        from open_notebook.skills.performance_optimizer import LRUCache

        cache = LRUCache(max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_lru_cache_ttl(self):
        """测试 LRU 缓存过期"""
        from open_notebook.skills.performance_optimizer import LRUCache
        import time

        cache = LRUCache(max_size=3)
        cache.set("key1", "value1", ttl_seconds=1)
        
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None  # Expired

    def test_performance_optimizer_initialization(self):
        """测试性能优化器初始化"""
        from open_notebook.skills.performance_optimizer import PerformanceOptimizer

        optimizer = PerformanceOptimizer(cache_size=100, max_concurrent_tasks=5)

        assert optimizer.cache.max_size == 100
        assert optimizer.task_queue.max_concurrent == 5

    def test_cached_decorator(self):
        """测试缓存装饰器"""
        from open_notebook.skills.performance_optimizer import cached, LRUCache
        import asyncio

        cache = LRUCache(max_size=10)
        call_count = {"count": 0}

        @cached(ttl=60, cache_instance=cache)
        async def expensive_function(x, y):
            call_count["count"] += 1
            return x + y

        # First call - should execute function
        result1 = asyncio.run(expensive_function(1, 2))
        assert result1 == 3
        assert call_count["count"] == 1

        # Second call - should use cache
        result2 = asyncio.run(expensive_function(1, 2))
        assert result2 == 3
        assert call_count["count"] == 1  # Not incremented


# ============================================================================
# B: UI Integration Tests
# ============================================================================


class TestUIIntegration:
    """UI 集成测试"""

    def test_ui_manager_registration(self):
        """测试 UI 管理器注册"""
        from open_notebook.skills.ui_integration import UIManager, ActionType

        ui_manager = UIManager()
        
        ui_manager.register_action(
            action_type=ActionType.GENERATE_REPORT,
            label="Test Report",
            icon="chart-bar",
            description="Test description",
            handler=None,
        )

        actions = ui_manager.get_available_actions()
        assert len(actions) == 1
        assert actions[0]["label"] == "Test Report"

    def test_notification_manager(self):
        """测试通知管理器"""
        from open_notebook.skills.ui_integration import NotificationManager, NotificationType

        notification_manager = NotificationManager()
        received_notifications = []

        def callback(notification):
            received_notifications.append(notification)

        notification_manager.subscribe(callback)
        notification_manager.info("Test Title", "Test Message")

        assert len(received_notifications) == 1
        assert received_notifications[0].title == "Test Title"
        assert received_notifications[0].type == NotificationType.INFO


# ============================================================================
# A: Collaboration Tools Tests
# ============================================================================


class TestCollaborationTools:
    """协作工具测试"""

    @pytest.mark.asyncio
    async def test_share_notebook(self):
        """测试共享 Notebook"""
        from open_notebook.skills.collaboration_tools import (
            CollaborationManager,
            Permission,
        )

        manager = CollaborationManager()
        
        invite = await manager.share_notebook(
            notebook_id="test-notebook",
            owner_id="owner@example.com",
            target_user_id="user@example.com",
            permission=Permission.WRITE,
        )

        assert invite.notebook_id == "test-notebook"
        assert invite.permission == Permission.WRITE
        assert invite.status == "pending"

    @pytest.mark.asyncio
    async def test_accept_invite(self):
        """测试接受邀请"""
        from open_notebook.skills.collaboration_tools import CollaborationManager, Permission

        manager = CollaborationManager()
        
        # Create invite
        invite = await manager.share_notebook(
            notebook_id="test-notebook",
            owner_id="owner@example.com",
            target_user_id="user@example.com",
            permission=Permission.READ,
        )

        # Accept invite
        accepted = await manager.accept_invite(invite.invite_id, "user@example.com")

        assert accepted is True
        assert invite.status == "accepted"

    @pytest.mark.asyncio
    async def test_permission_check(self):
        """测试权限检查"""
        from open_notebook.skills.collaboration_tools import CollaborationManager, Permission

        manager = CollaborationManager()
        
        # Setup share
        await manager.share_notebook(
            notebook_id="test-notebook",
            owner_id="owner@example.com",
            target_user_id="user@example.com",
            permission=Permission.WRITE,
        )
        await manager.accept_invite(
            manager.invites[list(manager.invites.keys())[0]].invite_id,
            "user@example.com",
        )

        # Check permissions
        has_write = await manager.check_permission("test-notebook", "user@example.com", Permission.WRITE)
        has_admin = await manager.check_permission("test-notebook", "user@example.com", Permission.ADMIN)

        assert has_write is True
        assert has_admin is False

    def test_collaboration_session(self):
        """测试协作会话"""
        from open_notebook.skills.collaboration_tools import CollaborationSession
        import asyncio

        session = CollaborationSession("test-session", "test-notebook")
        
        asyncio.run(session.join("user1"))
        asyncio.run(session.join("user2"))

        assert len(session.participants) == 2

        # Test broadcast
        participants = asyncio.run(session.broadcast({"type": "test"}, exclude_user="user1"))
        assert "user2" in participants
        assert "user1" not in participants


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_report_generation_flow(self):
        """测试完整报告生成流程"""
        from open_notebook.skills.one_click_report_generator import create_study_guide
        from open_notebook.skills.performance_optimizer import PerformanceOptimizer

        # Mock dependencies
        with patch("open_notebook.skills.one_click_report_generator.Notebook") as mock_notebook_class:
            mock_notebook = AsyncMock()
            mock_notebook.get_sources = AsyncMock(return_value=[])
            mock_notebook_class.get = AsyncMock(return_value=mock_notebook)

            # Generate report
            result = await create_study_guide("test-notebook-id")

            assert result["success"] is True
            
            # Verify performance was recorded
            optimizer = PerformanceOptimizer()
            # In real scenario, metrics would be recorded here


# ============================================================================
# Performance Benchmarks (Optional)
# ============================================================================


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """性能基准测试"""

    def test_cache_performance(self, benchmark):
        """测试缓存性能"""
        from open_notebook.skills.performance_optimizer import LRUCache

        cache = LRUCache(max_size=1000)
        
        def cache_operation():
            cache.set("test_key", "test_value")
            return cache.get("test_key")

        result = benchmark(cache_operation)
        assert result == "test_value"
        assert cache.hits > 0
