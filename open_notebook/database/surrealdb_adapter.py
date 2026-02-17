"""SurrealDB adapter for unified repository.

Wraps the existing repository.py functions to implement the BackendAdapter interface.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.database.repository import (
    db_connection,
    parse_record_ids,
    repo_create,
    repo_delete,
    repo_query,
    repo_update,
)

from .unified_repository import BackendAdapter, StorageBackend


class SurrealDBAdapter(BackendAdapter):
    """Adapter for SurrealDB backend.
    
    Wraps existing repository.py functions to provide unified interface.
    """

    def __init__(self):
        self._connected = False

    @property
    def backend_type(self) -> StorageBackend:
        """Return backend type identifier."""
        return StorageBackend.SURREALDB

    async def connect(self) -> None:
        """Verify SurrealDB connection.
        
        SurrealDB uses per-operation connections, so this just verifies
        that the database is accessible.
        """
        try:
            # Test connection by running a simple query
            async with db_connection() as conn:
                result = await conn.query("SELECT 1 as test")
                if result:
                    self._connected = True
                    logger.info("SurrealDB adapter connected")
                else:
                    raise ConnectionError("SurrealDB connection test failed")
        except Exception as e:
            logger.error(f"Failed to connect to SurrealDB: {e}")
            raise

    async def disconnect(self) -> None:
        """No-op for SurrealDB (connection per operation)."""
        self._connected = False
        logger.info("SurrealDB adapter disconnected")

    async def query(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query entities from SurrealDB.
        
        Args:
            entity_type: Table name (notebook, source, note, etc.)
            filters: Field filters as dict
            limit: Max results
            offset: Pagination offset
            order_by: Field to order by (prefix with - for desc)
            
        Returns:
            List of entity dictionaries
        """
        # Build SurrealQL query
        query_parts = [f"SELECT * FROM {entity_type}"]
        
        # Add filters
        vars_dict: Dict[str, Any] = {}
        if filters:
            conditions = []
            for i, (key, value) in enumerate(filters.items()):
                param_name = f"filter_{i}"
                conditions.append(f"{key} = ${param_name}")
                vars_dict[param_name] = value
            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))
        
        # Add ordering
        if order_by:
            if order_by.startswith("-"):
                query_parts.append(f"ORDER BY {order_by[1:]} DESC")
            else:
                query_parts.append(f"ORDER BY {order_by}")
        else:
            # Default ordering by updated desc
            query_parts.append("ORDER BY updated DESC")
        
        # Add pagination
        query_parts.append(f"LIMIT {limit}")
        if offset > 0:
            query_parts.append(f"START {offset}")
        
        query_str = " ".join(query_parts)
        
        try:
            results = await repo_query(query_str, vars_dict if vars_dict else None)
            return results if results else []
        except Exception as e:
            logger.error(f"SurrealDB query failed: {e}")
            raise

    async def get_by_id(
        self,
        entity_type: str,
        entity_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get entity by ID from SurrealDB.
        
        Args:
            entity_type: Table name
            entity_id: Record ID (can be 'table:id' or just 'id')
            
        Returns:
            Entity dict or None
        """
        # Handle both full record IDs and simple IDs
        if ":" in entity_id:
            record_id = entity_id
        else:
            record_id = f"{entity_type}:{entity_id}"
        
        query_str = f"SELECT * FROM {record_id}"
        
        try:
            results = await repo_query(query_str)
            if results and len(results) > 0:
                return results[0]
            return None
        except Exception as e:
            logger.error(f"SurrealDB get_by_id failed: {e}")
            raise

    async def create(
        self,
        entity_type: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create entity in SurrealDB.
        
        Args:
            entity_type: Table name
            data: Entity data
            
        Returns:
            Created entity dict
        """
        try:
            result = await repo_create(entity_type, data)
            return result
        except Exception as e:
            logger.error(f"SurrealDB create failed: {e}")
            raise

    async def update(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update entity in SurrealDB.
        
        Args:
            entity_type: Table name
            entity_id: Record ID
            data: Fields to update
            
        Returns:
            Updated entity dict
        """
        from surrealdb import RecordID
        from open_notebook.database.repository import ensure_record_id
        
        try:
            result = await repo_update(entity_type, entity_id, data)
            return result
        except Exception as e:
            logger.error(f"SurrealDB update failed: {e}")
            raise

    async def delete(
        self,
        entity_type: str,
        entity_id: str,
    ) -> bool:
        """Delete entity from SurrealDB.
        
        Args:
            entity_type: Table name
            entity_id: Record ID
            
        Returns:
            True if deleted
        """
        from open_notebook.database.repository import repo_delete, ensure_record_id
        from surrealdb import RecordID
        
        try:
            # Handle both full record IDs and simple IDs
            if ":" in entity_id:
                record_id = RecordID.parse(entity_id)
            else:
                record_id = RecordID(entity_type, entity_id)
            
            await repo_delete(record_id)
            return True
        except Exception as e:
            logger.error(f"SurrealDB delete failed: {e}")
            return False

    async def get_related(
        self,
        entity_type: str,
        entity_id: str,
        relation_type: str,
    ) -> List[Dict[str, Any]]:
        """Get related entities via graph relationships.
        
        SurrealDB has native graph support, so we use that.
        
        Args:
            entity_type: Source entity type
            entity_id: Source entity ID
            relation_type: Edge/relation type (e.g., 'reference', 'artifact')
            
        Returns:
            List of related entities
        """
        # Handle record ID format
        if ":" in entity_id:
            record_id = entity_id
        else:
            record_id = f"{entity_type}:{entity_id}"
        
        # Query graph relationship
        # This assumes standard graph pattern: entity -> relation -> target
        query_str = f"""
            SELECT * FROM (
                SELECT out FROM {relation_type} WHERE in = {record_id}
            ) FETCH out
        """
        
        try:
            results = await repo_query(query_str)
            # Extract the 'out' field which contains the related entity
            return [r.get("out", r) for r in results] if results else []
        except Exception as e:
            logger.error(f"SurrealDB get_related failed: {e}")
            raise


# ============================================================================
# Convenience Functions
# ============================================================================

async def create_surrealdb_adapter() -> SurrealDBAdapter:
    """Factory function to create and connect SurrealDB adapter.
    
    Returns:
        Connected SurrealDBAdapter instance
    """
    adapter = SurrealDBAdapter()
    await adapter.connect()
    return adapter
