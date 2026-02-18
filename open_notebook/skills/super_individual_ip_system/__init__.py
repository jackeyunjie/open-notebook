"""Super Individual IP System - Self-evolving personal brand building system.

This module provides a complete system for building and evolving a personal IP (Influencer Persona)
based on the P3 Evolution Layer concept from the Living Knowledge System.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│           Super Individual IP Self-Evolution System          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  P0: Perception Layer (感知层)                               │
│  ├─ Market Intelligence Collector (6 platforms + Feishu)    │
│  ├─ Competitor Monitoring                                   │
│  └─ User Feedback Analysis                                  │
│                                                              │
│  P1: Judgment Layer (判断层)                                 │
│  ├─ IP Positioning Analysis                                 │
│  ├─ Market Gap Identification                               │
│  └─ Strategy Priority Scoring                               │
│                                                              │
│  P2: Relationship Layer (关系层)                             │
│  ├─ Content Network Mapping                                 │
│  ├─ Audience Persona Building                               │
│  └─ Cross-Platform Strategy                                 │
│                                                              │
│  P3: Evolution Layer (演化层)                                │
│  ├─ Content Strategy Evolution                              │
│  ├─ Persona Optimization                                    │
│  ├─ Template Iteration                                      │
│  └─ Performance Feedback Loop                               │
│                                                              │
│  P4: DataAgent Layer (数据层)                                │
│  ├─ Historical Data Management                              │
│  ├─ Quality Monitoring                                      │
│  └─ Cost Optimization                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Evolution Cycle

```
Perception → Analysis → Decision → Action → Feedback → Evolution
    ↑                                                  ↓
    └────────────────── Loop ──────────────────────────┘
```

## Quick Start

```python
from open_notebook.skills.super_individual_ip_system import evolve_super_individual_ip

# Run complete evolution cycle
result = await evolve_super_individual_ip()

# Access results
print(f"Market gaps: {result['positioning']['market_gaps']}")
print(f"New content directions: {result['content_strategy']['new_directions']}")
print(f"Influence score: {result['influence']['score']}")
```

## Components

- **SuperIndividualIPSystem**: Main system class
- **MarketIntelligenceCollector**: Gathers data from all sources
- **IPPositioningAnalyzer**: Analyzes market position and gaps
- **ContentStrategyEvolver**: Evolves content strategy based on feedback
- **PersonaOptimizer**: Optimizes personal brand persona
- **InfluenceEvaluator**: Evaluates and tracks influence metrics

## Integration

This system integrates with:
- Multi-Platform AI Researcher (6 social platforms)
- Feishu Knowledge Collector (internal documents)
- Content Creation Workflow (content generation)
- Living Knowledge System (P3 Evolution)
"""

from .super_individual_ip_system import (
    SuperIndividualIPSystem,
    MarketIntelligenceCollector,
    IPPositioningAnalyzer,
    ContentStrategyEvolver,
    PersonaOptimizer,
    InfluenceEvaluator,
    evolve_super_individual_ip
)

__all__ = [
    "SuperIndividualIPSystem",
    "MarketIntelligenceCollector",
    "IPPositioningAnalyzer",
    "ContentStrategyEvolver",
    "PersonaOptimizer",
    "InfluenceEvaluator",
    "evolve_super_individual_ip"
]
