"""Unified Data Access Layer for Open Notebook + Living Knowledge System.

This module provides a unified interface to access data from both:
- SurrealDB: Core business data (notebooks, sources, notes, chat sessions)
- PostgreSQL: Living system data (cells, agents, metrics, triggers)

Design Principles:
1. Repository Pattern: Abstract database-specific implementations
2. Async-First: All operations are async by default
3. Transparent Routing: Auto-route queries to correct database
4. Consistent Interface: Same API regardless of underlying storage
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
)

from loguru import logger

# Type variable for generic results
T = TypeVar("T")


class DataDomain(Enum):
    """Data domain classification for routing."""
    CORE = auto()       # Notebooks, Sources, Notes (SurrealDB)
    LIVING = auto()     # Cells, Agents, Metrics (PostgreSQL)
    CROSS = auto()      # Cross-domain queries (requires aggregation)


class StorageBackend(Enum):
    """Available storage backends."""
    SURREALDB = "surrealdb"
    POSTGRESQL = "postgresql"


@dataclass
class QueryResult(Generic[T]):
    """Standardized query result wrapper."""
    data: T
    source: StorageBackend
    query_time_ms: float
    cached: bool = False


@dataclass
class EntityReference:
    """Cross-database entity reference."""
    entity_type: str
    entity_id: str
    domain: DataDomain
    backend: StorageBackend


# ============================================================================
# Unified Repository Interface
# ============================================================================

class UnifiedRepository(ABC):
    """Abstract unified repository interface.
    
    Implementations handle routing to appropriate backend database.
    """

    @abstractmethod
    async def query(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
    ) -> QueryResult[List[Dict[str, Any]]]:
        """Query entities with optional filtering.
        
        Args:
            entity_type: Type of entity (notebook, source, cell, agent, etc.)
            filters: Optional field filters
            limit: Maximum results to return
            offset: Pagination offset
            order_by: Optional ordering field
            
        Returns:
            QueryResult containing list of entities
        """
        pass

    @abstractmethod
    async def get_by_id(
        self,
        entity_type: str,
        entity_id: str,
    ) -> QueryResult[Optional[Dict[str, Any]]]:
        """Get single entity by ID.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            
        Returns:
            QueryResult containing entity or None
        """
        pass

    @abstractmethod
    async def create(
        self,
        entity_type: str,
        data: Dict[str, Any],
    ) -> QueryResult[Dict[str, Any]]:
        """Create new entity.
        
        Args:
            entity_type: Type of entity to create
            data: Entity data
            
        Returns:
            QueryResult containing created entity
        """
        pass

    @abstractmethod
    async def update(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
    ) -> QueryResult[Dict[str, Any]]:
        """Update existing entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            data: Fields to update
            
        Returns:
            QueryResult containing updated entity
        """
        pass

    @abstractmethod
    async def delete(
        self,
        entity_type: str,
        entity_id: str,
    ) -> QueryResult[bool]:
        """Delete entity by ID.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            
        Returns:
            QueryResult containing success status
        """
        pass

    @abstractmethod
    async def get_related(
        self,
        entity_type: str,
        entity_id: str,
        relation_type: str,
    ) -> QueryResult[List[Dict[str, Any]]]:
        """Get related entities.
        
        Args:
            entity_type: Source entity type
            entity_id: Source entity ID
            relation_type: Type of relationship
            
        Returns:
            QueryResult containing related entities
        """
        pass


# ============================================================================
# Domain Router
# ============================================================================

class DomainRouter:
    """Routes entity operations to appropriate database backend.
    
    This is the core of the unified layer - it knows which database
    stores which entity types and routes queries accordingly.
    """

    # Entity type to domain mapping
    ENTITY_DOMAINS: Dict[str, DataDomain] = {
        # Core domain (SurrealDB)
        "notebook": DataDomain.CORE,
        "source": DataDomain.CORE,
        "note": DataDomain.CORE,
        "chat_session": DataDomain.CORE,
        "insight": DataDomain.CORE,
        "transformation": DataDomain.CORE,
        "workflow": DataDomain.CORE,
        
        # Living domain (PostgreSQL)
        "cell": DataDomain.LIVING,
        "agent": DataDomain.LIVING,
        "meridian_metrics": DataDomain.LIVING,
        "trigger_record": DataDomain.LIVING,
        "data_lineage": DataDomain.LIVING,
        
        # Cross-domain (requires special handling)
        "search_result": DataDomain.CROSS,
        "activity_feed": DataDomain.CROSS,
    }

    @classmethod
    def get_domain(cls, entity_type: str) -> DataDomain:
        """Get domain for entity type."""
        return cls.ENTITY_DOMAINS.get(entity_type, DataDomain.CORE)

    @classmethod
    def get_backend(cls, entity_type: str) -> StorageBackend:
        """Get storage backend for entity type."""
        domain = cls.get_domain(entity_type)
        if domain == DataDomain.LIVING:
            return StorageBackend.POSTGRESQL
        return StorageBackend.SURREALDB

    @classmethod
    def is_cross_domain(cls, entity_types: List[str]) -> bool:
        """Check if query spans multiple domains."""
        if not entity_types:
            return False
        domains = {cls.get_domain(et) for et in entity_types}
        return len(domains) > 1


# ============================================================================
# Backend Adapters
# ============================================================================

class BackendAdapter(ABC):
    """Abstract adapter for specific database backend."""

    @property
    @abstractmethod
    def backend_type(self) -> StorageBackend:
        """Return backend type identifier."""
        pass

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to backend."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close backend connection."""
        pass

    @abstractmethod
    async def query(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute query on this backend."""
        pass

    @abstractmethod
    async def get_by_id(
        self,
        entity_type: str,
        entity_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get entity by ID from this backend."""
        pass

    @abstractmethod
    async def create(
        self,
        entity_type: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create entity in this backend."""
        pass

    @abstractmethod
    async def update(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update entity in this backend."""
        pass

    @abstractmethod
    async def delete(
        self,
        entity_type: str,
        entity_id: str,
    ) -> bool:
        """Delete entity from this backend."""
        pass


# ============================================================================
# Unified Repository Implementation
# ============================================================================

class UnifiedRepositoryImpl(UnifiedRepository):
    """Production implementation of unified repository.
    
    Routes operations to appropriate backend based on entity type.
    Supports both single-domain and cross-domain queries.
    """

    def __init__(
        self,
        surreal_adapter: Optional[BackendAdapter] = None,
        postgres_adapter: Optional[BackendAdapter] = None,
    ):
        self.surreal_adapter = surreal_adapter
        self.postgres_adapter = postgres_adapter
        self._adapters: Dict[StorageBackend, Optional[BackendAdapter]] = {
            StorageBackend.SURREALDB: surreal_adapter,
            StorageBackend.POSTGRESQL: postgres_adapter,
        }

    def _get_adapter(self, entity_type: str) -> Optional[BackendAdapter]:
        """Get appropriate adapter for entity type."""
        backend = DomainRouter.get_backend(entity_type)
        return self._adapters.get(backend)

    async def query(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
    ) -> QueryResult[List[Dict[str, Any]]]:
        """Route query to appropriate backend."""
        start_time = datetime.now()
        adapter = self._get_adapter(entity_type)
        
        if not adapter:
            raise RuntimeError(f"No adapter available for entity type: {entity_type}")

        data = await adapter.query(
            entity_type=entity_type,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return QueryResult(
            data=data,
            source=adapter.backend_type,
            query_time_ms=elapsed_ms,
        )

    async def get_by_id(
        self,
        entity_type: str,
        entity_id: str,
    ) -> QueryResult[Optional[Dict[str, Any]]]:
        """Route get_by_id to appropriate backend."""
        start_time = datetime.now()
        adapter = self._get_adapter(entity_type)
        
        if not adapter:
            raise RuntimeError(f"No adapter available for entity type: {entity_type}")

        data = await adapter.get_by_id(entity_type, entity_id)
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return QueryResult(
            data=data,
            source=adapter.backend_type,
            query_time_ms=elapsed_ms,
        )

    async def create(
        self,
        entity_type: str,
        data: Dict[str, Any],
    ) -> QueryResult[Dict[str, Any]]:
        """Route create to appropriate backend."""
        start_time = datetime.now()
        adapter = self._get_adapter(entity_type)
        
        if not adapter:
            raise RuntimeError(f"No adapter available for entity type: {entity_type}")

        result = await adapter.create(entity_type, data)
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return QueryResult(
            data=result,
            source=adapter.backend_type,
            query_time_ms=elapsed_ms,
        )

    async def update(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
    ) -> QueryResult[Dict[str, Any]]:
        """Route update to appropriate backend."""
        start_time = datetime.now()
        adapter = self._get_adapter(entity_type)
        
        if not adapter:
            raise RuntimeError(f"No adapter available for entity type: {entity_type}")

        result = await adapter.update(entity_type, entity_id, data)
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return QueryResult(
            data=result,
            source=adapter.backend_type,
            query_time_ms=elapsed_ms,
        )

    async def delete(
        self,
        entity_type: str,
        entity_id: str,
    ) -> QueryResult[bool]:
        """Route delete to appropriate backend."""
        start_time = datetime.now()
        adapter = self._get_adapter(entity_type)
        
        if not adapter:
            raise RuntimeError(f"No adapter available for entity type: {entity_type}")

        result = await adapter.delete(entity_type, entity_id)
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return QueryResult(
            data=result,
            source=adapter.backend_type,
            query_time_ms=elapsed_ms,
        )

    async def get_related(
        self,
        entity_type: str,
        entity_id: str,
        relation_type: str,
    ) -> QueryResult[List[Dict[str, Any]]]:
        """Get related entities.
        
        For cross-domain relationships, this requires special handling
        that will be implemented in the relationship sync layer.
        """
        start_time = datetime.now()
        
        # For now, route to the same backend as the source entity
        # Cross-domain relations will be handled by the sync layer
        adapter = self._get_adapter(entity_type)
        
        if not adapter:
            raise RuntimeError(f"No adapter available for entity type: {entity_type}")

        # This is a placeholder - real implementation depends on
        # how relationships are stored in each backend
        data: List[Dict[str, Any]] = []
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return QueryResult(
            data=data,
            source=adapter.backend_type,
            query_time_ms=elapsed_ms,
        )


# ============================================================================
# Global Repository Instance
# ============================================================================

# Module-level repository instance (initialized on first use)
_unified_repo: Optional[UnifiedRepositoryImpl] = None


async def get_unified_repository(
    surreal_adapter: Optional[BackendAdapter] = None,
    postgres_adapter: Optional[BackendAdapter] = None,
) -> UnifiedRepository:
    """Get or create global unified repository instance.
    
    Args:
        surreal_adapter: Optional SurrealDB adapter (auto-created if None)
        postgres_adapter: Optional PostgreSQL adapter (auto-created if None)
        
    Returns:
        UnifiedRepository instance
    """
    global _unified_repo
    
    if _unified_repo is None:
        # Auto-create adapters if not provided
        if surreal_adapter is None:
            from .surrealdb_adapter import SurrealDBAdapter
            surreal_adapter = SurrealDBAdapter()
            await surreal_adapter.connect()
            
        if postgres_adapter is None:
            from open_notebook.skills.living.database.postgresql import (
                create_postgresql_database,
            )
            # The PostgreSQL class already implements LivingDatabase interface
            # We'll wrap it in an adapter
            from .postgresql_adapter import PostgreSQLAdapter
            postgres_db = await create_postgresql_database()
            postgres_adapter = PostgreSQLAdapter(postgres_db)
        
        _unified_repo = UnifiedRepositoryImpl(
            surreal_adapter=surreal_adapter,
            postgres_adapter=postgres_adapter,
        )
        logger.info("Unified repository initialized")
    
    return _unified_repo


def reset_repository() -> None:
    """Reset global repository (useful for testing)."""
    global _unified_repo
    _unified_repo = None
