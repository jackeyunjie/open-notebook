"""Test PPTGenerator Skill"""
import asyncio
import sys
sys.path.insert(0, '.')

from open_notebook.skills.ppt_generator import PPTGenerator, Presentation, Slide, SlideLayout, PresentationType
from open_notebook.skills.base import SkillConfig, SkillContext

async def test_ppt_generator():
    print("=" * 70)
    print("Testing PPTGenerator Skill")
    print("=" * 70)

    # Create config
    config = SkillConfig(
        skill_type='ppt_generator',
        name='Test PPT Generator',
        description='Test presentation generation skill',
        parameters={
            'notebook_id': 'notebook:test123',
            'presentation_type': 'research_report',
            'target_audience': 'general',
            'max_slides': 10,
            'theme': 'professional',
            'include_speaker_notes': True,
        }
    )

    # Test 1: Validate config
    print('\n[Test 1] Configuration Validation')
    try:
        generator = PPTGenerator(config)
        print(f'  OK - Presentation Type: {generator.presentation_type.value}')
        print(f'  OK - Target Audience: {generator.target_audience}')
        print(f'  OK - Max Slides: {generator.max_slides}')
        print(f'  OK - Theme: {generator.theme}')
        print(f'  OK - Include Speaker Notes: {generator.include_speaker_notes}')
    except Exception as e:
        print(f'  ERROR: {e}')
        return

    # Test 2: Slide and Presentation dataclasses
    print('\n[Test 2] Slide and Presentation Structure')
    try:
        slide = Slide(
            slide_number=1,
            layout=SlideLayout.TITLE,
            title='Test Title',
            content='Test Content',
            bullet_points=['Point 1', 'Point 2'],
            speaker_notes='Speaker notes here'
        )
        print(f'  OK - Slide created: {slide.title}')
        print(f'  OK - Layout: {slide.layout.value}')
        print(f'  OK - Bullet points: {len(slide.bullet_points)}')

        presentation = Presentation(
            title='Test Presentation',
            subtitle='A test subtitle',
            presentation_type=PresentationType.RESEARCH_REPORT,
            target_audience='general',
            slide_count=5,
            theme='professional',
            slides=[slide]
        )
        print(f'  OK - Presentation created: {presentation.title}')
        print(f'  OK - Type: {presentation.presentation_type.value}')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 3: Export to dict
    print('\n[Test 3] Serialization')
    try:
        slide_dict = slide.to_dict()
        print(f'  OK - Slide serialized')
        print(f'  OK - Keys: {list(slide_dict.keys())}')

        pres_dict = presentation.to_dict()
        print(f'  OK - Presentation serialized')
        print(f'  OK - Keys: {list(pres_dict.keys())}')
        print(f'  OK - Slides count: {pres_dict["slide_count"]}')
    except Exception as e:
        print(f'  ERROR: {e}')

    # Test 4: Different presentation types
    print('\n[Test 4] Testing Different Presentation Types')
    types = ['pitch_deck', 'tutorial', 'research_report', 'case_study']
    for pres_type in types:
        try:
            config2 = SkillConfig(
                skill_type='ppt_generator',
                name='Test',
                description=f'Test {pres_type} type',
                parameters={
                    'notebook_id': 'notebook:test',
                    'presentation_type': pres_type,
                    'max_slides': 8,
                }
            )
            gen2 = PPTGenerator(config2)
            print(f'  OK - Type {pres_type}: max_slides={gen2.max_slides}')
        except Exception as e:
            print(f'  ERROR - Type {pres_type}: {e}')

    # Test 5: Different slide layouts
    print('\n[Test 5] Testing Slide Layouts')
    layouts = [
        SlideLayout.TITLE,
        SlideLayout.CONTENT,
        SlideLayout.TWO_COLUMN,
        SlideLayout.IMAGE,
        SlideLayout.QUOTE,
        SlideLayout.CHART,
        SlideLayout.SECTION,
        SlideLayout.END
    ]
    for layout in layouts:
        try:
            slide = Slide(
                slide_number=1,
                layout=layout,
                title=f'{layout.value.title()} Slide',
                content='Test content'
            )
            print(f'  OK - Layout {layout.value}: {slide.title}')
        except Exception as e:
            print(f'  ERROR - Layout {layout.value}: {e}')

    # Test 6: Mock content planning (without database)
    print('\n[Test 6] Mock Presentation Planning')
    try:
        # Create a simple plan manually
        plan = {
            "title": "AI Research Report",
            "subtitle": "Latest Advances in Artificial Intelligence",
            "slide_plan": [
                {"slide_number": 1, "layout": "title", "title": "AI Research Report", "key_points": []},
                {"slide_number": 2, "layout": "content", "title": "Introduction", "key_points": ["Background", "Objectives"]},
                {"slide_number": 3, "layout": "content", "title": "Methodology", "key_points": ["Data Collection", "Analysis"]},
                {"slide_number": 4, "layout": "chart", "title": "Results", "key_points": ["Key Finding 1", "Key Finding 2"]},
                {"slide_number": 5, "layout": "end", "title": "Conclusion", "key_points": []},
            ]
        }
        print(f'  OK - Plan created: {plan["title"]}')
        print(f'  OK - Slides planned: {len(plan["slide_plan"])}')

        # Simulate slide generation
        slides = []
        for slide_plan in plan["slide_plan"]:
            slide = Slide(
                slide_number=slide_plan["slide_number"],
                layout=SlideLayout(slide_plan["layout"]),
                title=slide_plan["title"],
                content="",
                bullet_points=slide_plan.get("key_points", []),
                speaker_notes=f'Notes for {slide_plan["title"]}' if config.parameters.get('include_speaker_notes') else ""
            )
            slides.append(slide)

        print(f'  OK - Generated {len(slides)} slides')
        for s in slides:
            print(f'    - Slide {s.slide_number}: {s.title} ({s.layout.value})')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    print('\n' + '=' * 70)
    print('PPTGenerator Skill Test Complete!')
    print('=' * 70)

if __name__ == '__main__':
    asyncio.run(test_ppt_generator())
