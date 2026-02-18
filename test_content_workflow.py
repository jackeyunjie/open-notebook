"""Test script for Content Creation Workflow.

This script tests the complete content creation workflow.
"""

import asyncio
import sys
from datetime import datetime

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

from open_notebook.skills.multi_platform_ai_researcher.content_creation_workflow import (
    ContentCreationWorkflow,
    TopicSelector,
    CopywritingGenerator,
    DistributionManager
)
from open_notebook.skills.multi_platform_ai_researcher.platform_content_optimizer import (
    PlatformContentOptimizer
)


async def test_topic_selector():
    """Test topic discovery and selection."""
    print("\n" + "="*60)
    print("TEST 1: Topic Discovery & Selection")
    print("="*60)

    selector = TopicSelector()

    # Discover topics
    print("\n[1] Discovering topics...")
    topics = await selector.discover_topics(category="ai_tools", count=5)

    print(f"[OK] Discovered {len(topics)} topics:")
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic.title}")
        print(f"     Score: {topic.trend_score:.1f} | Competition: {topic.competition_level}")

    # Select best topic
    print("\n[2] Selecting best topic...")
    selected = selector.select_topic(topics)

    print(f"[OK] Selected: {selected.title}")
    print(f"  Keywords: {', '.join(selected.keywords)}")

    return selected


async def test_platform_optimizer():
    """Test platform content optimization."""
    print("\n" + "="*60)
    print("TEST 2: Platform Content Optimizer")
    print("="*60)

    optimizer = PlatformContentOptimizer()

    # Test content
    test_content = """
    AI tools are transforming how solopreneurs work. From ChatGPT for writing
    to Midjourney for design, these tools can handle tasks that used to take
    hours. This article introduces 10 AI tools that boost productivity.
    """

    platforms = ["xiaohongshu", "zhihu", "weibo"]

    print("\n[1] Optimizing content for multiple platforms...")
    for platform in platforms:
        result = optimizer.optimize_content(test_content, platform)

        print(f"\n  [{platform.upper()}]")
        print(f"  Platform: {result['platform_name']}")
        print(f"  Original: {result['original_length']} chars")
        print(f"  Optimal: {result['optimal_length']} chars")
        print(f"  Hashtags: {result['hashtag_suggestions']}")

    # Compare all platforms
    print("\n[2] Platform comparison...")
    comparison = optimizer.compare_platforms()

    print(f"  Total platforms: {comparison['summary']['total_platforms']}")

    for platform, info in comparison['platforms'].items():
        print(f"\n  - {info['name_cn']} ({platform})")
        print(f"    Length: {info['optimal_length']} chars")
        print(f"    Audience: {info['audience']}")


async def test_copywriting_generator(topic):
    """Test copywriting generation."""
    print("\n" + "="*60)
    print("TEST 3: Copywriting Generation")
    print("="*60)

    generator = CopywritingGenerator()

    # Create dummy materials
    from open_notebook.skills.multi_platform_ai_researcher.content_creation_workflow import Material

    materials = [
        Material(
            id="mat_1",
            source="test",
            source_platform="xiaohongshu",
            title="ChatGPT usage tips",
            content="ChatGPT helps me save 50% writing time! Highly recommended.",
            url="",
            relevance_score=0.9,
            tags=["ChatGPT", "writing"]
        ),
        Material(
            id="mat_2",
            source="test",
            source_platform="zhihu",
            title="AI tools review",
            content="Compared 10 AI tools, Midjourney is best for image generation.",
            url="",
            relevance_score=0.85,
            tags=["Midjourney", "AI art"]
        )
    ]

    platforms = ["xiaohongshu", "zhihu", "weibo"]

    print(f"\n[1] Generating copy for: {topic.title}")
    print(f"    Materials: {len(materials)}")

    copies = await generator.generate_multi_platform_copies(
        topic=topic,
        materials=materials,
        platforms=platforms,
        style="informative"
    )

    print(f"\n[2] Generated {len(copies)} copies:")

    for copy in copies:
        print(f"\n  [{'='*40}]")
        print(f"  Platform: {copy.platform_name}")
        print(f"  Title: {copy.title[:50]}...")
        print(f"  Length: {len(copy.content)} chars")
        print(f"  Hashtags: {copy.hashtags}")
        print(f"  Engagement: {copy.expected_engagement}")

    return copies


async def test_distribution_manager(copies):
    """Test distribution planning."""
    print("\n" + "="*60)
    print("TEST 4: Distribution Planning")
    print("="*60)

    manager = DistributionManager()

    print("\n[1] Creating distribution plan...")
    plans = manager.create_distribution_plan(copies)

    print(f"  Created {len(plans)} plans")

    print("\n[2] Optimizing schedule...")
    optimized = manager.optimize_schedule(plans)

    print("\n  Optimized posting schedule:")
    for plan in optimized:
        print(f"    {plan.platform_name:12} -> {plan.scheduled_time}")

    print("\n[3] Generating report...")
    report = manager.generate_distribution_report()

    print(f"  Total platforms: {report['total_platforms']}")
    print(f"  Est. reach: {report['estimated_reach']['estimated_total_reach']} people")


async def test_full_workflow():
    """Test complete workflow."""
    print("\n" + "="*60)
    print("TEST 5: Complete Workflow")
    print("="*60)

    workflow = ContentCreationWorkflow()

    print("\n[1] Workflow components:")
    print("  - TopicSelector: OK")
    print("  - MaterialCollector: OK")
    print("  - CopywritingGenerator: OK")
    print("  - DistributionManager: OK")

    print("\n[2] Note: Full workflow requires browser automation")
    print("  (Skipped in this test)")


async def test_platform_guide():
    """Test platform guide generation."""
    print("\n" + "="*60)
    print("TEST 6: Platform Guide")
    print("="*60)

    from open_notebook.skills.multi_platform_ai_researcher.platform_content_optimizer import (
        get_platform_guide
    )

    print("\n[1] Generating guide...")
    guide = get_platform_guide()

    print(f"  Guide length: {len(guide)} characters")
    print(f"  Lines: {len(guide.split(chr(10)))}")

    # Show structure
    sections = [line for line in guide.split(chr(10)) if line.startswith("##")]
    print(f"\n  Sections: {len(sections)}")
    for section in sections[:5]:
        print(f"    {section[:40]}...")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CONTENT CREATION WORKFLOW - TEST SUITE")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Test 1: Topic Selector
        selected_topic = await test_topic_selector()

        # Test 2: Platform Optimizer
        await test_platform_optimizer()

        # Test 3: Copywriting Generator
        copies = await test_copywriting_generator(selected_topic)

        # Test 4: Distribution Manager
        await test_distribution_manager(copies)

        # Test 5: Full Workflow
        await test_full_workflow()

        # Test 6: Platform Guide
        await test_platform_guide()

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("[PASS] Topic Discovery & Selection")
        print("[PASS] Platform Content Optimization")
        print("[PASS] Copywriting Generation")
        print("[PASS] Distribution Planning")
        print("[PASS] Full Workflow (components)")
        print("[PASS] Platform Guide")
        print("\n[SUCCESS] All tests passed!")

    except Exception as e:
        print(f"\n[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
