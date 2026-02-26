"""Test MeetingSummarizer Skill"""
import asyncio
import sys
sys.path.insert(0, '.')

from open_notebook.skills.meeting_summarizer import (
    MeetingSummarizer, MeetingSummary, ActionItem, Decision, MeetingType
)
from open_notebook.skills.base import SkillConfig, SkillContext

async def test_meeting_summarizer():
    print("=" * 70)
    print("Testing MeetingSummarizer Skill")
    print("=" * 70)

    # Create config
    config = SkillConfig(
        skill_type='meeting_summarizer',
        name='Test Meeting Summarizer',
        description='Test meeting summary generation skill',
        parameters={
            'notebook_id': 'notebook:test123',
            'meeting_type': 'review',
            'participants': ['Alice', 'Bob', 'Charlie'],
            'duration_minutes': 60,
            'extract_action_items': True,
            'generate_follow_up': True,
        }
    )

    # Test 1: Validate config
    print('\n[Test 1] Configuration Validation')
    try:
        summarizer = MeetingSummarizer(config)
        print(f'  OK - Meeting Type: {summarizer.meeting_type.value}')
        print(f'  OK - Participants: {summarizer.participants}')
        print(f'  OK - Duration: {summarizer.duration_minutes} min')
        print(f'  OK - Extract Action Items: {summarizer.extract_action_items}')
        print(f'  OK - Generate Follow-up: {summarizer.generate_follow_up}')
    except Exception as e:
        print(f'  ERROR: {e}')
        return

    # Test 2: ActionItem dataclass
    print('\n[Test 2] ActionItem Structure')
    try:
        action = ActionItem(
            description="Complete project documentation",
            owner="Alice",
            deadline="2024-02-01",
            priority="high",
            status="pending",
            source_quote="Alice will complete the docs by next week"
        )
        print(f'  OK - Action item created: {action.description[:30]}...')
        print(f'  OK - Owner: {action.owner}')
        print(f'  OK - Priority: {action.priority}')
        print(f'  OK - Deadline: {action.deadline}')

        action_dict = action.to_dict()
        print(f'  OK - Serialized to dict')
        print(f'  OK - Keys: {list(action_dict.keys())}')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 3: Decision dataclass
    print('\n[Test 3] Decision Structure')
    try:
        decision = Decision(
            topic="Technology Stack",
            decision="Use React for frontend",
            rationale="Team has most experience with React",
            stakeholders=["Alice", "Bob"]
        )
        print(f'  OK - Decision created: {decision.topic}')
        print(f'  OK - Decision: {decision.decision}')
        print(f'  OK - Stakeholders: {decision.stakeholders}')

        decision_dict = decision.to_dict()
        print(f'  OK - Serialized to dict')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 4: MeetingSummary structure
    print('\n[Test 4] MeetingSummary Structure')
    try:
        summary = MeetingSummary(
            title="Weekly Team Review",
            meeting_type=MeetingType.REVIEW,
            date=__import__('datetime').datetime.now(),
            duration_minutes=60,
            participants=['Alice', 'Bob', 'Charlie'],
            key_points=['Progress on feature X', 'Resolved bug Y', 'Updated timeline'],
            action_items=[action],
            decisions=[decision],
            topics=[
                {'subject': 'Feature X', 'duration': 20, 'sentiment': 'positive'},
                {'subject': 'Bug Fixes', 'duration': 15, 'sentiment': 'neutral'},
            ],
            sentiment='positive',
            follow_up_required=True,
            next_meeting='2024-02-08'
        )
        print(f'  OK - Meeting summary created: {summary.title}')
        print(f'  OK - Type: {summary.meeting_type.value}')
        print(f'  OK - Key points: {len(summary.key_points)}')
        print(f'  OK - Action items: {len(summary.action_items)}')
        print(f'  OK - Decisions: {len(summary.decisions)}')
        print(f'  OK - Topics: {len(summary.topics)}')
        print(f'  OK - Sentiment: {summary.sentiment}')

        summary_dict = summary.to_dict()
        print(f'  OK - Serialized to dict')
        print(f'  OK - Keys: {list(summary_dict.keys())}')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 5: Different meeting types
    print('\n[Test 5] Testing Different Meeting Types')
    meeting_types = ['standup', 'review', 'planning', 'brainstorm', 'one_on_one', 'client', 'board']
    for mt in meeting_types:
        try:
            config2 = SkillConfig(
                skill_type='meeting_summarizer',
                name='Test',
                description=f'Test {mt} meeting type',
                parameters={
                    'note_id': 'note:test',
                    'meeting_type': mt,
                    'duration_minutes': 30,
                }
            )
            summarizer2 = MeetingSummarizer(config2)
            print(f'  OK - Type {mt}: duration={summarizer2.duration_minutes}min')
        except Exception as e:
            print(f'  ERROR - Type {mt}: {e}')

    # Test 6: Generate meeting minutes (mock)
    print('\n[Test 6] Meeting Minutes Generation (Mock)')
    try:
        summarizer3 = MeetingSummarizer(config)
        minutes = summarizer3._generate_meeting_minutes(summary)
        print(f'  OK - Meeting minutes generated ({len(minutes)} chars)')
        print(f'  Preview (first 300 chars):')
        for line in minutes.split('\n')[:8]:
            if line.strip():
                print(f'    {line}')
        print('    ...')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 7: Generate follow-up email (mock)
    print('\n[Test 7] Follow-up Email Generation (Mock)')
    try:
        email = summarizer3._generate_follow_up_email(summary)
        print(f'  OK - Follow-up email generated ({len(email)} chars)')
        print(f'  Preview (first 200 chars):')
        for line in email.split('\n')[:5]:
            if line.strip():
                print(f'    {line}')
        print('    ...')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 8: Action items table
    print('\n[Test 8] Action Items Table')
    try:
        # Create multiple action items
        actions = [
            ActionItem("Task 1", "Alice", "2024-02-01", "high"),
            ActionItem("Task 2", "Bob", "2024-02-05", "medium"),
            ActionItem("Task 3", "Charlie", None, "low"),
        ]
        summary2 = MeetingSummary(
            title="Test Meeting",
            meeting_type=MeetingType.STANDUP,
            date=__import__('datetime').datetime.now(),
            duration_minutes=30,
            action_items=actions
        )

        minutes2 = summarizer3._generate_meeting_minutes(summary2)
        has_action_table = "| # |" in minutes2 or "Action" in minutes2
        print(f'  OK - Action items in minutes: {has_action_table}')
        print(f'  OK - Total action items: {len(actions)}')
        for a in actions:
            print(f'    - {a.description} ({a.owner}, {a.priority})')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 9: Empty summary handling
    print('\n[Test 9] Empty Summary Handling')
    try:
        empty_summary = MeetingSummary(
            title="Empty Meeting",
            meeting_type=MeetingType.REVIEW,
            date=__import__('datetime').datetime.now(),
            duration_minutes=0
        )
        print(f'  OK - Empty summary created')
        print(f'  OK - Key points: {len(empty_summary.key_points)}')
        print(f'  OK - Action items: {len(empty_summary.action_items)}')
        print(f'  OK - Decisions: {len(empty_summary.decisions)}')

        empty_dict = empty_summary.to_dict()
        print(f'  OK - Empty summary serialized')
    except Exception as e:
        print(f'  ERROR: {e}')

    print('\n' + '=' * 70)
    print('MeetingSummarizer Skill Test Complete!')
    print('=' * 70)

if __name__ == '__main__':
    asyncio.run(test_meeting_summarizer())
