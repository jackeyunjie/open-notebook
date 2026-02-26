"""Test VideoGenerator Skill"""
import asyncio
import sys
sys.path.insert(0, '.')

from open_notebook.skills.video_generator import VideoGenerator, VideoScript, VideoScene, VideoStyle
from open_notebook.skills.base import SkillConfig, SkillContext

async def test_video_generator():
    print("=" * 70)
    print("Testing VideoGenerator Skill")
    print("=" * 70)

    # Create config
    config = SkillConfig(
        skill_type='video_generator',
        name='Test Video Generator',
        description='Test video generation skill',
        parameters={
            'notebook_id': 'notebook:test123',
            'video_style': 'educational',
            'target_duration': 60,
            'provider': 'mock',
            'target_audience': 'general',
            'include_narration': True,
            'include_music': True,
        }
    )

    # Test 1: Validate config
    print('\n[Test 1] Configuration Validation')
    try:
        generator = VideoGenerator(config)
        print(f'  OK - Video Style: {generator.video_style.value}')
        print(f'  OK - Target Duration: {generator.target_duration}s')
        print(f'  OK - Provider: {generator.provider.value}')
        print(f'  OK - Target Audience: {generator.target_audience}')
    except Exception as e:
        print(f'  ERROR: {e}')
        return

    # Test 2: Default script generation
    print('\n[Test 2] Default Script Generation')
    try:
        script = generator._create_default_script()
        print(f'  OK - Script Title: {script.title}')
        print(f'  OK - Number of Scenes: {len(script.scenes)}')
        print(f'  OK - Total Duration: {script.target_duration}s')
        print(f'  OK - Style: {script.style.value}')
        print(f'  OK - Music Style: {script.music_style}')

        # Print scene details
        print('\n  Scene Breakdown:')
        for scene in script.scenes:
            print(f'    Scene {scene.scene_number}: {scene.title}')
            print(f'      Duration: {scene.duration}s | Transition: {scene.transition}')
            print(f'      Mood: {scene.music_mood}')
            print(f'      Narration: {scene.narration}')
            print(f'      Visual: {scene.visual_prompt[:60]}...')
            print()
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 3: Mock video generation
    print('[Test 3] Mock Video Generation')
    try:
        from pathlib import Path
        output_dir = Path('./data/test/videos')
        result = await generator._generate_video_mock(script, output_dir)

        if result.success:
            print(f'  OK - Generation successful')
            print(f'  OK - Provider: {result.provider}')
            print(f'  OK - Video Path: {result.video_path}')
            print(f'  OK - Processing Time: {result.processing_time:.2f}s')
            print(f'  OK - Metadata keys: {list(result.metadata.keys())}')
        else:
            print(f'  FAILED: {result.error_message}')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 4: Export to dict
    print('\n[Test 4] Script Serialization')
    try:
        script_dict = script.to_dict()
        print(f'  OK - Serialized successfully')
        print(f'  OK - Keys: {list(script_dict.keys())}')
        if script_dict.get('scenes'):
            print(f'  OK - First scene keys: {list(script_dict["scenes"][0].keys())}')
    except Exception as e:
        print(f'  ERROR: {e}')

    # Test 5: Different video styles
    print('\n[Test 5] Testing Different Video Styles')
    styles = ['educational', 'storytelling', 'news', 'short']
    for style in styles:
        try:
            config2 = SkillConfig(
                skill_type='video_generator',
                name='Test',
                description=f'Test {style} style',
                parameters={
                    'notebook_id': 'notebook:test',
                    'video_style': style,
                    'target_duration': 60,
                    'provider': 'mock',
                }
            )
            gen2 = VideoGenerator(config2)
            script2 = gen2._create_default_script()
            print(f'  OK - Style {style}: {len(script2.scenes)} scenes')
        except Exception as e:
            print(f'  ERROR - Style {style}: {e}')

    print('\n' + '=' * 70)
    print('VideoGenerator Skill Test Complete!')
    print('=' * 70)

if __name__ == '__main__':
    asyncio.run(test_video_generator())
