"""P0 Perception Organ - Living Knowledge System Example.

This demonstrates how to convert the P0 Perception Layer into the
living knowledge system architecture (Cell -> Tissue -> Organ).
"""

import asyncio
from datetime import timedelta
from typing import Any, Dict, List, Optional

from open_notebook.skills.living import (
    # Cell layer
    LivingSkill,
    SkillTemporal,
    SkillResource,
    SkillDependency,
    SkillState,
    # Tissue layer
    AgentTissue,
    AgentCoordination,
    AgentRhythm,
    CoordinationPattern,
    # Meridian layer
    DataMeridian,
    ControlMeridian,
    MeridianSystem,
    FlowNode,
    FlowType,
    # Acupoint layer
    AcupointTrigger,
    TriggerType,
    TriggerCondition,
    TriggerConfig,
    acupoint,
)


# =============================================================================
# P0 SKILLS (Cells)
# =============================================================================

def create_pain_scanner_skill() -> LivingSkill:
    """Create the PainScanner skill cell."""

    # Python script resource for execution
    pain_scanner_script = """
async def execute():
    '''Scan for pain points in social media and comments.'''
    context = globals().get('context', {})
    config = globals().get('config', {})

    # Get data from context
    platform_data = context.get('platform_data', {})

    # Analyze pain points
    pain_points = []
    for item in platform_data.get('comments', []):
        text = item.get('text', '')
        # Simple pain point detection (in real implementation, use NLP)
        pain_keywords = ['problem', 'issue', 'frustrated', 'struggle', 'pain', 'difficult']
        if any(kw in text.lower() for kw in pain_keywords):
            pain_points.append({
                'text': text,
                'source': item.get('platform'),
                'timestamp': item.get('timestamp'),
                'severity': calculate_severity(text)
            })

    return {
        'pain_points': pain_points,
        'count': len(pain_points),
        'top_severity': max([p['severity'] for p in pain_points], default=0)
    }

def calculate_severity(text: str) -> int:
    '''Calculate pain severity score.'''
    score = 0
    high_severity = ['urgent', 'critical', 'desperate', 'cannot', 'impossible']
    medium_severity = ['difficult', 'hard', 'annoying', 'problem']

    text_lower = text.lower()
    for kw in high_severity:
        if kw in text_lower:
            score += 3
    for kw in medium_severity:
        if kw in text_lower:
            score += 1

    return min(score, 10)
"""

    return LivingSkill(
        skill_id="p0.pain_scanner",
        name="Pain Scanner",
        description="Scan social platforms for user pain points and frustrations",
        version="1.0.0",
        temporal=SkillTemporal(
            cron="0 */4 * * *",  # Run every 4 hours
            timeout=timedelta(minutes=10),
            timezone="Asia/Shanghai"
        ),
        resources=[
            SkillResource(
                name="scanner",
                type="python",
                content=pain_scanner_script,
                entry_point="execute"
            )
        ],
        provides=["pain_points", "user_frustrations"],
        triggers=["p0.orchestrator"]  # Trigger orchestrator after completion
    )


def create_emotion_watcher_skill() -> LivingSkill:
    """Create the EmotionWatcher skill cell."""

    emotion_script = """
async def execute():
    '''Watch for emotional trends in user content.'''
    context = globals().get('context', {})

    content = context.get('content', [])

    emotions = {
        'joy': 0,
        'anger': 0,
        'sadness': 0,
        'fear': 0,
        'surprise': 0
    }

    for item in content:
        text = item.get('text', '')
        # Simple emotion detection (in real implementation, use sentiment analysis)
        if any(kw in text.lower() for kw in ['happy', 'love', 'great', 'awesome']):
            emotions['joy'] += 1
        if any(kw in text.lower() for kw in ['angry', 'hate', 'terrible', 'awful']):
            emotions['anger'] += 1
        if any(kw in text.lower() for kw in ['sad', 'depressed', 'sorry', 'miss']):
            emotions['sadness'] += 1

    dominant_emotion = max(emotions, key=emotions.get)

    return {
        'emotions': emotions,
        'dominant_emotion': dominant_emotion,
        'total_analyzed': len(content)
    }
"""

    return LivingSkill(
        skill_id="p0.emotion_watcher",
        name="Emotion Watcher",
        description="Monitor emotional trends and sentiment across platforms",
        temporal=SkillTemporal(
            interval=timedelta(hours=2),  # Run every 2 hours
            timeout=timedelta(minutes=5)
        ),
        resources=[
            SkillResource(
                name="watcher",
                type="python",
                content=emotion_script,
                entry_point="execute"
            )
        ],
        provides=["emotions", "sentiment", "mood_trends"]
    )


def create_trend_hunter_skill() -> LivingSkill:
    """Create the TrendHunter skill cell."""

    trend_script = """
async def execute():
    '''Hunt for emerging trends.'''
    context = globals().get('context', {})

    hashtags = context.get('hashtags', [])
    search_queries = context.get('search_queries', [])

    trends = []
    for tag in hashtags:
        trends.append({
            'name': tag['name'],
            'volume': tag.get('volume', 0),
            'growth_rate': tag.get('growth', 0),
            'category': categorize_trend(tag['name'])
        })

    # Sort by growth rate
    trends.sort(key=lambda x: x['growth_rate'], reverse=True)

    return {
        'trends': trends[:10],  # Top 10 trends
        'categories': list(set(t['category'] for t in trends)),
        'insights': generate_insights(trends[:5])
    }

def categorize_trend(name: str) -> str:
    '''Categorize a trend.'''
    categories = {
        'tech': ['ai', 'tech', 'digital', 'app'],
        'lifestyle': ['health', 'fitness', 'food', 'travel'],
        'business': ['startup', 'entrepreneur', 'marketing']
    }
    for cat, keywords in categories.items():
        if any(kw in name.lower() for kw in keywords):
            return cat
    return 'general'

def generate_insights(top_trends: list) -> list:
    '''Generate insights from top trends.'''
    return [f"{t['name']} growing at {t['growth_rate']}%" for t in top_trends]
"""

    return LivingSkill(
        skill_id="p0.trend_hunter",
        name="Trend Hunter",
        description="Discover emerging trends and viral content patterns",
        temporal=SkillTemporal(
            cron="0 */6 * * *",  # Every 6 hours
            timeout=timedelta(minutes=15)
        ),
        resources=[
            SkillResource(
                name="hunter",
                type="python",
                content=trend_script,
                entry_point="execute"
            )
        ],
        provides=["trends", "hashtags", "insights"],
        dependencies=[
            SkillDependency(skill_id="p0.platform_connector", required=False)
        ]
    )


def create_scene_discover_skill() -> LivingSkill:
    """Create the SceneDiscover skill cell."""

    scene_script = """
async def execute():
    '''Discover high-value scenes and contexts.'''
    context = globals().get('context', {})

    locations = context.get('locations', [])
    contexts = context.get('contexts', [])

    scenes = []
    for loc in locations:
        scenes.append({
            'location': loc['name'],
            'audience_size': loc.get('audience', 0),
            'engagement_rate': loc.get('engagement', 0),
            'content_opportunity': assess_opportunity(loc)
        })

    # Sort by opportunity score
    scenes.sort(key=lambda x: x['content_opportunity'], reverse=True)

    return {
        'scenes': scenes[:5],
        'total_addressable_audience': sum(s['audience_size'] for s in scenes),
        'avg_engagement': sum(s['engagement_rate'] for s in scenes) / len(scenes) if scenes else 0
    }

def assess_opportunity(location: dict) -> float:
    '''Assess content opportunity for a location.'''
    audience = location.get('audience', 0)
    engagement = location.get('engagement', 0)
    competition = location.get('competition', 1)

    # Simple opportunity score
    score = (audience * engagement) / (competition + 1)
    return round(score, 2)
"""

    return LivingSkill(
        skill_id="p0.scene_discover",
        name="Scene Discover",
        description="Discover high-value scenes and audience contexts",
        temporal=SkillTemporal(
            interval=timedelta(hours=8),
            timeout=timedelta(minutes=10)
        ),
        resources=[
            SkillResource(
                name="discoverer",
                type="python",
                content=scene_script,
                entry_point="execute"
            )
        ],
        provides=["scenes", "locations", "opportunities"]
    )


# =============================================================================
# P0 AGENT (Tissue)
# =============================================================================

def create_p0_perception_agent() -> AgentTissue:
    """Create the P0 Perception Agent tissue."""

    # Coordination: All skills run in parallel to gather perception data
    coordination = AgentCoordination(
        pattern=CoordinationPattern.PARALLEL,
        max_parallel=4,
        timeout=timedelta(minutes=15)
    )

    # Rhythm: Active during peak hours (9-11am, 2-4pm, 8-10pm)
    rhythm = AgentRhythm(
        pulse_interval=timedelta(minutes=30),  # Health check every 30 min
        active_hours=(6, 23),  # Active from 6am to 11pm
        peak_hours=[9, 10, 14, 15, 20, 21],
        rest_days=[]  # Work every day
    )

    return AgentTissue(
        agent_id="p0.perception",
        name="P0 Perception Agent",
        description="Sense and collect market intelligence from all platforms",
        purpose="Continuously monitor environment for pain points, emotions, trends, and opportunities",
        skills=[
            "p0.pain_scanner",
            "p0.emotion_watcher",
            "p0.trend_hunter",
            "p0.scene_discover"
        ],
        coordination=coordination,
        rhythm=rhythm,
        stimuli=["daily_sync", "platform_alert", "trending_spike"]
    )


# =============================================================================
# MERIDIANS (Flows)
# =============================================================================

def create_p0_meridians():
    """Create meridians for P0 data flow."""

    # Data meridian for perception data
    perception_data = DataMeridian(
        meridian_id="p0.data.perception",
        name="P0 Perception Data",
        capacity=5000
    )

    # Control meridian for orchestration
    perception_control = ControlMeridian(
        meridian_id="p0.control",
        name="P0 Control Signals"
    )

    # Register commands
    perception_control.register_command("daily_sync", lambda pkt: print(f"Daily sync: {pkt.payload}"))
    perception_control.register_command("pause", lambda pkt: print("Pausing P0"))
    perception_control.register_command("resume", lambda pkt: print("Resuming P0"))

    return perception_data, perception_control


# =============================================================================
# ACUPOINTS (Triggers)
# =============================================================================

@acupoint(
    name="daily_sync_trigger",
    trigger_type=TriggerType.TEMPORAL,
    target_agents=["p0.perception"],
    meridians=["p0.control"],
    cooldown_seconds=3600,  # 1 hour cooldown
    tags=["p0", "daily", "sync"]
)
async def on_daily_sync(event_data: Dict):
    """Daily sync trigger for P0."""
    print(f"[Daily Sync] Triggered at {event_data.get('timestamp')}")
    # This triggers the P0 perception agent
    return {"status": "triggered", "target": "p0.perception"}


@acupoint(
    name="platform_alert",
    trigger_type=TriggerType.EVENT,
    condition=TriggerCondition(
        threshold_type="value",
        threshold_value=100,
        comparison=">=",
        field_path="data.mention_count"
    ),
    target_agents=["p0.perception"],
    target_skills=["p0.pain_scanner"],
    meridians=["p0.data.perception"],
    cooldown_seconds=300,  # 5 min cooldown
    priority=2,
    tags=["p0", "alert", "platform"]
)
async def on_platform_alert(event_data: Dict):
    """Trigger when platform mentions spike."""
    print(f"[Platform Alert] High mention count: {event_data}")
    return {"status": "alert_processed"}


@acupoint(
    name="trending_spike",
    trigger_type=TriggerType.CONDITION,
    condition=TriggerCondition(
        pattern=r"#\w+trending",
        field_path="data.hashtag"
    ),
    target_agents=["p0.perception"],
    target_skills=["p0.trend_hunter"],
    cooldown_seconds=600,
    tags=["p0", "trending"]
)
async def on_trending_spike(event_data: Dict):
    """Trigger when trending hashtag detected."""
    print(f"[Trending] New trend detected: {event_data}")
    return {"status": "trend_captured"}


# =============================================================================
# INITIALIZATION
# =============================================================================

async def initialize_p0_organ():
    """Initialize the complete P0 Perception Organ."""

    print("=" * 60)
    print("Initializing P0 Perception Organ (Living Knowledge System)")
    print("=" * 60)

    # 1. Create Skills (Cells)
    print("\n[1/5] Creating Skill Cells...")
    pain_scanner = create_pain_scanner_skill()
    emotion_watcher = create_emotion_watcher_skill()
    trend_hunter = create_trend_hunter_skill()
    scene_discover = create_scene_discover_skill()
    print(f"  - Pain Scanner: {pain_scanner.skill_id}")
    print(f"  - Emotion Watcher: {emotion_watcher.skill_id}")
    print(f"  - Trend Hunter: {trend_hunter.skill_id}")
    print(f"  - Scene Discover: {scene_discover.skill_id}")

    # 2. Create Agent (Tissue)
    print("\n[2/5] Creating Agent Tissue...")
    p0_agent = create_p0_perception_agent()
    print(f"  - Agent: {p0_agent.agent_id}")
    print(f"  - Skills: {len(p0_agent.skill_ids)}")
    print(f"  - Coordination: {p0_agent.coordination.pattern.value}")
    print(f"  - Active Hours: {p0_agent.rhythm.active_hours}")

    # 3. Create Meridians (Flows)
    print("\n[3/5] Setting up Meridians...")
    perception_data, perception_control = create_p0_meridians()
    MeridianSystem.register(perception_data)
    MeridianSystem.register(perception_control)
    print(f"  - Data Meridian: {perception_data.meridian_id}")
    print(f"  - Control Meridian: {perception_control.meridian_id}")

    # 4. Register Acupoints (Triggers)
    print("\n[4/5] Registering Acupoint Triggers...")
    # Triggers are auto-registered by the @acupoint decorator
    from open_notebook.skills.living.acupoint_trigger import TriggerRegistry
    triggers = TriggerRegistry.list_all()
    p0_triggers = [t for t in triggers if t.trigger_id.startswith("__main__") or "p0" in t.config.tags]
    print(f"  - Registered {len(p0_triggers)} P0 triggers")
    for t in p0_triggers:
        print(f"    • {t.name} ({t.trigger_type.value})")

    # 5. Connect components
    print("\n[5/5] Connecting components...")
    # Connect agent to meridians
    agent_node = FlowNode(
        node_id=p0_agent.agent_id,
        node_type="agent",
        capabilities={FlowType.DATA, FlowType.CONTROL}
    )
    perception_data.connect(agent_node)
    perception_control.connect(agent_node)
    print(f"  - Agent connected to meridians")

    print("\n" + "=" * 60)
    print("P0 Perception Organ initialization complete!")
    print("=" * 60)

    return {
        "skills": [pain_scanner, emotion_watcher, trend_hunter, scene_discover],
        "agent": p0_agent,
        "meridians": [perception_data, perception_control],
        "triggers": p0_triggers
    }


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

async def main():
    """Main example usage."""

    # Initialize the organ
    p0_organ = await initialize_p0_organ()

    print("\n" + "-" * 60)
    print("Example: Manual skill execution")
    print("-" * 60)

    # Get a skill and invoke it
    pain_scanner = p0_organ["skills"][0]

    # Simulate platform data
    test_context = {
        "platform_data": {
            "comments": [
                {"text": "I have a problem with this feature", "platform": "weibo", "timestamp": "2024-01-01"},
                {"text": "This is great!", "platform": "xiaohongshu", "timestamp": "2024-01-01"},
                {"text": "Struggling with this issue", "platform": "douyin", "timestamp": "2024-01-01"},
            ]
        }
    }

    print(f"\nInvoking {pain_scanner.name}...")
    result = await pain_scanner.invoke(test_context)
    print(f"Result: {result}")

    print("\n" + "-" * 60)
    print("Example: Agent execution")
    print("-" * 60)

    # Execute the agent
    agent = p0_organ["agent"]
    print(f"\nExecuting {agent.name}...")
    # Note: In real usage, would need to resolve skill references
    # agent_result = await agent.execute()
    # print(f"Agent result: {agent_result}")

    print("\n" + "-" * 60)
    print("Example: Trigger activation")
    print("-" * 60)

    # Activate a trigger manually
    from open_notebook.skills.living.acupoint_trigger import TriggerRegistry
    trigger = TriggerRegistry.get("__main__.on_daily_sync")
    if trigger:
        print(f"\nActivating trigger: {trigger.name}")
        success = await trigger.activate({"timestamp": "2024-01-01T09:00:00"})
        print(f"Activation result: {success}")


if __name__ == "__main__":
    asyncio.run(main())
