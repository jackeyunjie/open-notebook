"""PostgreSQL adapter for unified repository.

Wraps the existing LKS PostgreSQL implementation to implement BackendAdapter interface.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.skills.living.database.abstract import LivingDatabase
from open_notebook.skills.living.database.postgresql import PostgreSQLDatabase

from .unified_repository import BackendAdapter, StorageBackend


class PostgreSQLAdapter(BackendAdapter):
    """Adapter for PostgreSQL backend (LKS data).
    
    Wraps the existing PostgreSQLDatabase class to provide unified interface.
    """

    def __init__(self, db: PostgreSQLDatabase):
        """Initialize with PostgreSQLDatabase instance.
        
        Args:
            db: Connected PostgreSQLDatabase instance
        """
        self.db = db
        self._connected = False

    @property
    def backend_type(self) -> StorageBackend:
        """Return backend type identifier."""
        return StorageBackend.POSTGRESQL

    async def connect(self) -> None:
        """Verify PostgreSQL connection."""
        if self.db.pool:
            self._connected = True
            logger.info("PostgreSQL adapter connected")
        else:
            raise ConnectionError("PostgreSQL database not connected")

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        if self.db:
            await self.db.disconnect()
        self._connected = False
        logger.info("PostgreSQL adapter disconnected")

    def _entity_to_table(self, entity_type: str) -> str:
        """Map entity type to PostgreSQL table name.
        
        Args:
            entity_type: Entity type (cell, agent, etc.)
            
        Returns:
            PostgreSQL table name
        """
        mapping = {
            "cell": "cell_states",
            "agent": "agent_states",
            "meridian_metrics": "meridian_metrics",
            "trigger_record": "trigger_records",
            "data_lineage": "data_lineage",
        }
        return mapping.get(entity_type, entity_type)

    async def query(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query entities from PostgreSQL.
        
        Args:
            entity_type: Entity type (cell, agent, etc.)
            filters: Field filters as dict
            limit: Max results
            offset: Pagination offset
            order_by: Field to order by
            
        Returns:
            List of entity dictionaries
        """
        table = self._entity_to_table(entity_type)
        
        # Build SQL query
        query_parts = [f"SELECT * FROM {table}"]
        
        # Add filters
        params: List[Any] = []
        if filters:
            conditions = []
            for key, value in filters.items():
                params.append(value)
                conditions.append(f"{key} = ${len(params)}")
            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))
        
        # Add ordering
        if order_by:
            if order_by.startswith("-"):
                query_parts.append(f"ORDER BY {order_by[1:]} DESC")
            else:
                query_parts.append(f"ORDER BY {order_by}")
        else:
            query_parts.append("ORDER BY updated_at DESC")
        
        # Add pagination
        params.append(limit)
        query_parts.append(f"LIMIT ${len(params)}")
        
        if offset > 0:
            params.append(offset)
            query_parts.append(f"OFFSET ${len(params)}")
        
        query_str = " ".join(query_parts)
        
        try:
            async with self.db.pool.acquire() as conn:
                rows = await conn.fetch(query_str, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"PostgreSQL query failed: {e}")
            raise

    async def get_by_id(
        self,
        entity_type: str,
        entity_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get entity by ID from PostgreSQL.
        
        Args:
            entity_type: Entity type
            entity_id: Entity identifier
            
        Returns:
            Entity dict or None
        """
        table = self._entity_to_table(entity_type)
        
        # Determine ID column based on entity type
        id_column = self._get_id_column(entity_type)
        
        try:
            async with self.db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"SELECT * FROM {table} WHERE {id_column} = $1",
                    entity_id
                )
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"PostgreSQL get_by_id failed: {e}")
            raise

    def _get_id_column(self, entity_type: str) -> str:
        """Get ID column name for entity type."""
        mapping = {
            "cell": "skill_id",
            "agent": "agent_id",
            "meridian_metrics": "meridian_id",
            "trigger_record": "trigger_id",
            "data_lineage": "data_id",
        }
        return mapping.get(entity_type, "id")

    async def create(
        self,
        entity_type: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create entity in PostgreSQL.
        
        Args:
            entity_type: Entity type
            data: Entity data
            
        Returns:
            Created entity dict
        """
        # Use the appropriate method from PostgreSQLDatabase
        if entity_type == "cell":
            from open_notebook.skills.living.database.abstract import CellState
            state = CellState(**data)
            await self.db.save_cell_state(state)
            # Return the saved state
            result = await self.get_by_id(entity_type, data.get("skill_id", ""))
            return result if result else data
            
        elif entity_type == "agent":
            from open_notebook.skills.living.database.abstract import AgentState
            state = AgentState(**data)
            await self.db.save_agent_state(state)
            result = await self.get_by_id(entity_type, data.get("agent_id", ""))
            return result if result else data
            
        elif entity_type == "meridian_metrics":
            from open_notebook.skills.living.database.abstract import MeridianMetrics
            metrics = MeridianMetrics(**data)
            await self.db.record_meridian_metrics(metrics)
            return data
            
        elif entity_type == "trigger_record":
            from open_notebook.skills.living.database.abstract import TriggerRecord
            record = TriggerRecord(**data)
            await self.db.record_trigger_activation(record)
            return data
            
        elif entity_type == "data_lineage":
            from open_notebook.skills.living.database.abstract import DataLineage
            lineage = DataLineage(**data)
            await self.db.register_data_lineage(lineage)
            result = await self.get_by_id(entity_type, data.get("data_id", ""))
            return result if result else data
        
        else:
            # Generic insert for unknown types
            table = self._entity_to_table(entity_type)
            columns = list(data.keys())
            values = list(data.values())
            
            col_str = ", ".join(columns)
            val_str = ", ".join(f"${i+1}" for i in range(len(values)))
            
            query = f"INSERT INTO {table} ({col_str}) VALUES ({val_str}) RETURNING *"
            
            async with self.db.pool.acquire() as conn:
                row = await conn.fetchrow(query, *values)
                return dict(row) if row else data

    async def update(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update entity in PostgreSQL.
        
        Args:
            entity_type: Entity type
            entity_id: Entity identifier
            data: Fields to update
            
        Returns:
            Updated entity dict
        """
        # For LKS entities, we use the same save methods (UPSERT)
        update_data = {**data}
        
        # Set the ID field appropriately
        if entity_type == "cell":
            update_data["skill_id"] = entity_id
        elif entity_type == "agent":
            update_data["agent_id"] = entity_id
        elif entity_type == "data_lineage":
            update_data["data_id"] = entity_id
        else:
            id_column = self._get_id_column(entity_type)
            update_data[id_column] = entity_id
        
        # Use create (which does UPSERT)
        return await self.create(entity_type, update_data)

    async def delete(
        self,
        entity_type: str,
        entity_id: str,
    ) -> bool:
        """Delete entity from PostgreSQL.
        
        Args:
            entity_type: Entity type
            entity_id: Entity identifier
            
        Returns:
            True if deleted
        """
        if entity_type == "cell":
            return await self.db.delete_cell_state(entity_id)
        
        # Generic delete for other types
        table = self._entity_to_table(entity_type)
        id_column = self._get_id_column(entity_type)
        
        try:
            async with self.db.pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {table} WHERE {id_column} = $1",
                    entity_id
                )
                return "DELETE 1" in result
        except Exception as e:
            logger.error(f"PostgreSQL delete failed: {e}")
            return False

    async def get_related(
        self,
        entity_type: str,
        entity_id: str,
        relation_type: str,
    ) -> List[Dict[str, Any]]:
        """Get related entities.
        
        PostgreSQL doesn't have native graph support like SurrealDB,
        so we rely on foreign key relationships or the data_lineage table.
        
        Args:
            entity_type: Source entity type
            entity_id: Source entity ID
            relation_type: Relation type
            
        Returns:
            List of related entities
        """
        # For now, return empty list
        # Real implementation would query data_lineage or foreign keys
        logger.debug(f"get_related not implemented for PostgreSQL: {entity_type} -> {relation_type}")
        return []


# ============================================================================
# Convenience Functions
# ============================================================================

async def create_postgresql_adapter(
    host: str = "localhost",
    port: int = 5433,
    database: str = "living_system",
    user: str = "living",
    password: str = "living",
) -> PostgreSQLAdapter:
    """Factory function to create and connect PostgreSQL adapter.
    
    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
        
    Returns:
        Connected PostgreSQLAdapter instance
    """
    from open_notebook.skills.living.database.postgresql import PostgreSQLDatabase
    
    db = PostgreSQLDatabase(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
    )
    await db.connect()
    
    adapter = PostgreSQLAdapter(db)
    await adapter.connect()
    return adapter
