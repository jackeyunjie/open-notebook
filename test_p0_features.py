#!/usr/bin/env python3
"""
P0 功能集成测试 - 一键报告生成器 + 跨文档洞察系统

测试场景:
1. 创建学习指南（Study Guide）
2. 创建文献综述（Literature Review）
3. 创建研究简报（Research Digest）
4. 创建周度趋势报告（Weekly Trends）
5. 创建概念图谱（Concept Map）
6. 跨文档主题分析
7. 矛盾观点检测
8. 研究趋势识别
"""

import asyncio
from open_notebook.skills.one_click_report_generator import (
    create_study_guide,
    create_literature_review,
    create_research_digest,
    create_weekly_trends,
    create_concept_map,
)
from open_notebook.skills.cross_document_insights import (
    analyze_cross_document_themes,
    detect_contradictions,
    identify_research_trends,
    generate_weekly_trends_report,
)


async def main():
    print("=" * 60)
    print("🚀 P0 功能集成测试")
    print("=" * 60)
    
    # 注意：需要真实的 Notebook ID 才能运行
    # 这里使用模拟的 notebook_id
    notebook_id = "notebook:test_001"
    
    print("\n⚠️  注意：以下测试需要真实的 Notebook 数据")
    print(f"   当前使用的 Notebook ID: {notebook_id}")
    print("\n   如果要实际运行，请替换为真实的 Notebook ID\n")
    
    try:
        # Test 1: 创建学习指南
        print("\n📚 Test 1: 创建学习指南...")
        study_guide = await create_study_guide(notebook_id)
        print(f"  ✅ 学习指南已生成：{study_guide['title']}")
        print(f"     - Note ID: {study_guide['note_id']}")
        print(f"     - 覆盖源数量：{study_guide['sources_count']}")
        
        # Test 2: 创建文献综述
        print("\n📖 Test 2: 创建文献综述...")
        lit_review = await create_literature_review(notebook_id)
        print(f"  ✅ 文献综述已生成：{lit_review['title']}")
        print(f"     - Note ID: {lit_review['note_id']}")
        
        # Test 3: 创建研究简报
        print("\n📰 Test 3: 创建研究简报...")
        digest = await create_research_digest(notebook_id)
        print(f"  ✅ 研究简报已生成：{digest['title']}")
        print(f"     - Note ID: {digest['note_id']}")
        
        # Test 4: 创建周度趋势
        print("\n📈 Test 4: 创建周度趋势...")
        trends = await create_weekly_trends(notebook_id)
        print(f"  ✅ 周度趋势已生成：{trends['title']}")
        print(f"     - Note ID: {trends['note_id']}")
        
        # Test 5: 创建概念图谱
        print("\n🗺️  Test 5: 创建概念图谱...")
        concept_map = await create_concept_map(notebook_id)
        print(f"  ✅ 概念图谱已生成：{concept_map['title']}")
        print(f"     - Note ID: {concept_map['note_id']}")
        
        # Test 6: 跨文档主题分析
        print("\n🔍 Test 6: 跨文档主题分析...")
        themes = await analyze_cross_document_themes(notebook_id)
        print(f"  ✅ 主题分析完成")
        print(f"     - 总源数量：{themes['total_sources']}")
        print(f"     - 唯一主题数：{themes['unique_topics']}")
        print(f"     - 共同主题数：{len(themes['common_themes'])}")
        
        # Test 7: 矛盾观点检测
        print("\n⚠️  Test 7: 矛盾观点检测...")
        contradictions = await detect_contradictions(notebook_id)
        print(f"  ✅ 检测到 {len(contradictions)} 处潜在矛盾")
        if contradictions:
            print(f"     - 第一个矛盾主题：{contradictions[0]['topic']}")
        
        # Test 8: 研究趋势识别
        print("\n📊 Test 8: 研究趋势识别...")
        trend_analysis = await identify_research_trends(notebook_id, days=7)
        print(f"  ✅ 趋势分析完成")
        print(f"     - 热门主题数：{len(trend_analysis['trending_topics'])}")
        print(f"     - 新兴主题数：{len(trend_analysis['emerging_topics'])}")
        
        # Test 9: 生成周度趋势报告
        print("\n📝 Test 9: 生成周度趋势报告...")
        weekly_report = await generate_weekly_trends_report(notebook_id)
        report_length = len(weekly_report)
        print(f"  ✅ 周度报告已生成")
        print(f"     - 报告长度：{report_length} 字符")
        
        print("\n" + "=" * 60)
        print("✅ 所有 P0 功能测试通过！")
        print("=" * 60)
        
        return {
            "tests_passed": 9,
            "reports_generated": 5,
            "analyses_completed": 4,
            "status": "success"
        }
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        print("\n💡 提示：请确保 Notebook ID 有效且包含足够的 Source 数据")
        return {
            "tests_passed": 0,
            "error": str(e),
            "status": "failed"
        }


if __name__ == "__main__":
    result = asyncio.run(main())
    
    print("\n\n🎯 测试结果汇总:")
    print(f"  - 通过的测试数：{result.get('tests_passed', 0)}")
    print(f"  - 生成的报告数：{result.get('reports_generated', 0)}")
    print(f"  - 完成的分析数：{result.get('analyses_completed', 0)}")
    print(f"  - 状态：{result.get('status', 'unknown')}")
