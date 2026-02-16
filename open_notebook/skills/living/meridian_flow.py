"""Meridian Flow - Connects cells, tissues, and organs through data/control/temporal flows.

In traditional Chinese medicine, meridians are pathways through which qi (life energy)
flows. Similarly, in the living knowledge system:
- Data meridians: pathways for information flow
- Control meridians: pathways for command signals
- Temporal meridians: pathways for timing and synchronization
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Generic
from uuid import uuid4

from loguru import logger


T = TypeVar('T')


class FlowType(Enum):
    """Types of meridian flows."""
    DATA = "data"           # Information flow
    CONTROL = "control"     # Command signals
    TEMPORAL = "temporal"   # Timing and synchronization
    ENERGY = "energy"       # Resource allocation


class FlowDirection(Enum):
    """Direction of flow."""
    UNIDIRECTIONAL = "unidirectional"   # One way
    BIDIRECTIONAL = "bidirectional"     # Both ways
    MULTICAST = "multicast"             # One to many
    GATHER = "gather"                   # Many to one


@dataclass
class FlowPacket(Generic[T]):
    """A packet of data flowing through a meridian."""
    packet_id: str
    source: str
    destination: Optional[str]  # None = broadcast
    payload: T
    flow_type: FlowType
    timestamp: datetime
    priority: int = 5  # 1 (highest) to 10 (lowest)
    ttl: int = 10  # Time-to-live (hops)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowNode:
    """A node connected to the meridian system."""
    node_id: str
    node_type: str  # "skill", "agent", "organ", "external"
    capabilities: Set[FlowType] = field(default_factory=set)
    subscriptions: Set[str] = field(default_factory=set)  # Topics subscribed
    handler: Optional[Callable[[FlowPacket], Any]] = None


class MeridianFlow:
    """Base class for meridian flows connecting components.

    Meridians are like the body's circulatory and nervous systems:
    - They transport data/energy between components
    - They have pathways (routes)
    - They can have blockages (that need clearing)
    - They support different flow patterns
    """

    def __init__(
        self,
        meridian_id: str,
        name: str,
        flow_type: FlowType,
        direction: FlowDirection = FlowDirection.UNIDIRECTIONAL,
        capacity: int = 1000,  # Max packets in transit
    ):
        self.meridian_id = meridian_id
        self.name = name
        self.flow_type = flow_type
        self.direction = direction
        self.capacity = capacity

        # Connected nodes
        self.nodes: Dict[str, FlowNode] = {}
        self.routes: Dict[str, List[str]] = {}  # source -> [destinations]

        # Flow control
        self._packet_queue: asyncio.Queue = asyncio.Queue(maxsize=capacity)
        self._processing = False
        self._process_task: Optional[asyncio.Task] = None

        # Metrics
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_dropped = 0
        self.blockages: List[str] = []  # Blocked nodes

    async def start(self):
        """Start the meridian flow processing."""
        self._processing = True
        self._process_task = asyncio.create_task(self._process_loop())
        logger.info(f"Meridian {self.meridian_id} started")

    async def stop(self):
        """Stop the meridian flow."""
        self._processing = False
        if self._process_task:
            self._process_task.cancel()
        logger.info(f"Meridian {self.meridian_id} stopped")

    def connect(self, node: FlowNode, routes: Optional[List[str]] = None):
        """Connect a node to this meridian."""
        if self.flow_type not in node.capabilities:
            logger.warning(f"Node {node.node_id} doesn't support {self.flow_type.value} flow")
            return

        self.nodes[node.node_id] = node
        if routes:
            self.routes[node.node_id] = routes
        logger.debug(f"Connected {node.node_type} {node.node_id} to meridian {self.meridian_id}")

    def disconnect(self, node_id: str):
        """Disconnect a node from this meridian."""
        if node_id in self.nodes:
            del self.nodes[node_id]
        if node_id in self.routes:
            del self.routes[node_id]

    async def send(
        self,
        source: str,
        payload: Any,
        destination: Optional[str] = None,
        priority: int = 5,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Send a packet through the meridian."""
        if source not in self.nodes:
            logger.error(f"Source {source} not connected to meridian {self.meridian_id}")
            return False

        packet = FlowPacket(
            packet_id=str(uuid4()),
            source=source,
            destination=destination,
            payload=payload,
            flow_type=self.flow_type,
            timestamp=datetime.now(),
            priority=priority,
            metadata=metadata or {}
        )

        try:
            await asyncio.wait_for(
                self._packet_queue.put(packet),
                timeout=1.0
            )
            self.packets_sent += 1
            return True
        except asyncio.TimeoutError:
            self.packets_dropped += 1
            logger.warning(f"Meridian {self.meridian_id} congested, packet dropped")
            return False

    async def broadcast(
        self,
        source: str,
        payload: Any,
        priority: int = 5,
        metadata: Optional[Dict] = None
    ) -> int:
        """Broadcast a packet to all connected nodes."""
        sent = 0
        for node_id in self.nodes:
            if node_id != source:
                success = await self.send(
                    source=source,
                    payload=payload,
                    destination=node_id,
                    priority=priority,
                    metadata=metadata
                )
                if success:
                    sent += 1
        return sent

    async def _process_loop(self):
        """Main processing loop for the meridian."""
        while self._processing:
            try:
                packet: FlowPacket = await asyncio.wait_for(
                    self._packet_queue.get(),
                    timeout=1.0
                )

                # Process packet
                await self._route_packet(packet)
                self.packets_received += 1

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing packet in meridian {self.meridian_id}: {e}")

    async def _route_packet(self, packet: FlowPacket):
        """Route a packet to its destination(s)."""
        destinations = []

        if packet.destination:
            # Unicast
            destinations = [packet.destination]
        elif self.direction == FlowDirection.MULTICAST:
            # Broadcast to all except source
            destinations = [n for n in self.nodes.keys() if n != packet.source]
        elif packet.source in self.routes:
            # Follow predefined routes
            destinations = self.routes[packet.source]

        # Deliver to destinations
        for dest_id in destinations:
            if dest_id in self.blockages:
                logger.warning(f"Node {dest_id} is blocked, packet {packet.packet_id} cannot deliver")
                continue

            node = self.nodes.get(dest_id)
            if node and node.handler:
                try:
                    if asyncio.iscoroutinefunction(node.handler):
                        await node.handler(packet)
                    else:
                        node.handler(packet)
                except Exception as e:
                    logger.error(f"Error delivering packet to {dest_id}: {e}")

    def detect_blockage(self, node_id: str) -> bool:
        """Detect if a node is blocked (not responding)."""
        # Simple implementation - can be enhanced
        return node_id in self.blockages

    def clear_blockage(self, node_id: str):
        """Clear a blockage."""
        if node_id in self.blockages:
            self.blockages.remove(node_id)
            logger.info(f"Blockage cleared for node {node_id}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get meridian flow metrics."""
        return {
            "meridian_id": self.meridian_id,
            "flow_type": self.flow_type.value,
            "connected_nodes": len(self.nodes),
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "packets_dropped": self.packets_dropped,
            "queue_size": self._packet_queue.qsize(),
            "blockages": len(self.blockages),
        }


class DataMeridian(MeridianFlow):
    """Data flow meridian - transports information between components."""

    def __init__(self, meridian_id: str, name: str, **kwargs):
        super().__init__(
            meridian_id=meridian_id,
            name=name,
            flow_type=FlowType.DATA,
            **kwargs
        )
        self.topics: Dict[str, Set[str]] = {}  # topic -> subscribers

    def subscribe(self, node_id: str, topic: str):
        """Subscribe a node to a topic."""
        if topic not in self.topics:
            self.topics[topic] = set()
        self.topics[topic].add(node_id)

        node = self.nodes.get(node_id)
        if node:
            node.subscriptions.add(topic)

    def unsubscribe(self, node_id: str, topic: str):
        """Unsubscribe a node from a topic."""
        if topic in self.topics:
            self.topics[topic].discard(node_id)
        node = self.nodes.get(node_id)
        if node:
            node.subscriptions.discard(topic)

    async def publish(
        self,
        source: str,
        topic: str,
        data: Any,
        priority: int = 5
    ) -> int:
        """Publish data to a topic."""
        subscribers = self.topics.get(topic, set())
        sent = 0

        for node_id in subscribers:
            if node_id != source:
                success = await self.send(
                    source=source,
                    payload={"topic": topic, "data": data},
                    destination=node_id,
                    priority=priority,
                    metadata={"topic": topic}
                )
                if success:
                    sent += 1

        return sent


class ControlMeridian(MeridianFlow):
    """Control flow meridian - transports commands and signals."""

    def __init__(self, meridian_id: str, name: str, **kwargs):
        super().__init__(
            meridian_id=meridian_id,
            name=name,
            flow_type=FlowType.CONTROL,
            direction=FlowDirection.MULTICAST,
            **kwargs
        )
        self.command_handlers: Dict[str, Callable] = {}

    def register_command(self, command: str, handler: Callable):
        """Register a handler for a specific command."""
        self.command_handlers[command] = handler

    async def send_command(
        self,
        source: str,
        command: str,
        params: Optional[Dict] = None,
        destination: Optional[str] = None
    ) -> bool:
        """Send a command through the meridian."""
        return await self.send(
            source=source,
            payload={"command": command, "params": params or {}},
            destination=destination,
            priority=1,  # Commands are high priority
            metadata={"command": command}
        )


class TemporalMeridian(MeridianFlow):
    """Temporal flow meridian - synchronizes timing across components."""

    def __init__(self, meridian_id: str, name: str, **kwargs):
        super().__init__(
            meridian_id=meridian_id,
            name=name,
            flow_type=FlowType.TEMPORAL,
            direction=FlowDirection.MULTICAST,
            **kwargs
        )
        self.time_sync_interval = 60  # seconds
        self._sync_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the temporal meridian with time sync."""
        await super().start()
        self._sync_task = asyncio.create_task(self._time_sync_loop())

    async def stop(self):
        """Stop the temporal meridian."""
        if self._sync_task:
            self._sync_task.cancel()
        await super().stop()

    async def _time_sync_loop(self):
        """Periodically broadcast time sync signals."""
        while self._processing:
            try:
                await self.broadcast(
                    source="temporal_meridian",
                    payload={
                        "type": "time_sync",
                        "timestamp": datetime.now().isoformat()
                    },
                    priority=1
                )
                await asyncio.sleep(self.time_sync_interval)
            except Exception as e:
                logger.error(f"Time sync error: {e}")

    async def schedule_signal(
        self,
        signal_name: str,
        trigger_time: datetime,
        target: Optional[str] = None
    ):
        """Schedule a temporal signal."""
        delay = (trigger_time - datetime.now()).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)
            await self.send(
                source="temporal_meridian",
                payload={"type": "scheduled_signal", "signal": signal_name},
                destination=target
            )


# Global meridian system
class MeridianSystem:
    """Central registry and management of all meridians."""

    _meridians: Dict[str, MeridianFlow] = {}

    @classmethod
    def register(cls, meridian: MeridianFlow):
        """Register a meridian."""
        cls._meridians[meridian.meridian_id] = meridian

    @classmethod
    def get(cls, meridian_id: str) -> Optional[MeridianFlow]:
        """Get a meridian by ID."""
        return cls._meridians.get(meridian_id)

    @classmethod
    def list_by_type(cls, flow_type: FlowType) -> List[MeridianFlow]:
        """List all meridians of a specific type."""
        return [m for m in cls._meridians.values() if m.flow_type == flow_type]

    @classmethod
    async def start_all(cls):
        """Start all registered meridians."""
        for meridian in cls._meridians.values():
            await meridian.start()

    @classmethod
    async def stop_all(cls):
        """Stop all registered meridians."""
        for meridian in cls._meridians.values():
            await meridian.stop()
