"""Test MindMapGenerator Skill"""
import asyncio
import sys
sys.path.insert(0, '.')

from open_notebook.skills.mindmap_generator import (
    MindMapGenerator, MindMap, MindNode, LayoutType, NodeType
)
from open_notebook.skills.base import SkillConfig, SkillContext

async def test_mindmap_generator():
    print("=" * 70)
    print("Testing MindMapGenerator Skill")
    print("=" * 70)

    # Create config
    config = SkillConfig(
        skill_type='mindmap_generator',
        name='Test MindMap Generator',
        description='Test mind map generation skill',
        parameters={
            'notebook_id': 'notebook:test123',
            'layout': 'radial',
            'max_depth': 4,
            'focus_topic': 'AI Technology',
            'include_sources': True,
            'color_scheme': 'default',
        }
    )

    # Test 1: Validate config
    print('\n[Test 1] Configuration Validation')
    try:
        generator = MindMapGenerator(config)
        print(f'  OK - Layout: {generator.layout.value}')
        print(f'  OK - Max Depth: {generator.max_depth}')
        print(f'  OK - Focus Topic: {generator.focus_topic}')
        print(f'  OK - Include Sources: {generator.include_sources}')
        print(f'  OK - Color Scheme: {generator.color_scheme}')
    except Exception as e:
        print(f'  ERROR: {e}')
        return

    # Test 2: MindNode dataclass
    print('\n[Test 2] MindNode Structure')
    try:
        root_node = MindNode(
            id="root",
            text="AI Technology",
            node_type=NodeType.ROOT,
            emoji="target",
            color="#FF6B6B"
        )
        print(f'  OK - Root node created: {root_node.text}')
        print(f'  OK - Type: {root_node.node_type.value}')
        print(f'  OK - Emoji stored: {root_node.emoji is not None}')

        child_node = MindNode(
            id="root_0",
            text="Machine Learning",
            node_type=NodeType.TOPIC,
            parent_id="root",
            emoji="robot",
            color="#4ECDC4",
            notes="Core ML algorithms and techniques"
        )
        print(f'  OK - Child node created: {child_node.text}')
        print(f'  OK - Parent: {child_node.parent_id}')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()
        return

    # Test 3: MindMap structure and serialization
    print('\n[Test 3] MindMap Structure and Serialization')
    try:
        mindmap = MindMap(
            title="AI Technology Overview",
            layout=LayoutType.RADIAL,
            root_node="root",
            nodes={"root": root_node, "root_0": child_node}
        )
        root_node.children.append("root_0")

        print(f'  OK - MindMap created: {mindmap.title}')
        print(f'  OK - Layout: {mindmap.layout.value}')
        print(f'  OK - Node count: {len(mindmap.nodes)}')

        # Test to_dict
        mindmap_dict = mindmap.to_dict()
        print(f'  OK - Serialized to dict')
        print(f'  OK - Keys: {list(mindmap_dict.keys())}')
        print(f'  OK - Node count in dict: {mindmap_dict["node_count"]}')

        # Test to_markdown
        markdown = mindmap.to_markdown()
        print(f'  OK - Markdown generated ({len(markdown)} chars)')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 4: Different layout types
    print('\n[Test 4] Testing Different Layout Types')
    layouts = ['radial', 'tree', 'organic', 'fishbone', 'timeline']
    for layout in layouts:
        try:
            config2 = SkillConfig(
                skill_type='mindmap_generator',
                name='Test',
                description=f'Test {layout} layout',
                parameters={
                    'notebook_id': 'notebook:test',
                    'layout': layout,
                    'max_depth': 3,
                }
            )
            gen2 = MindMapGenerator(config2)
            print(f'  OK - Layout {layout}: max_depth={gen2.max_depth}')
        except Exception as e:
            print(f'  ERROR - Layout {layout}: {e}')

    # Test 5: Different node types
    print('\n[Test 5] Testing Node Types')
    node_types = [
        (NodeType.ROOT, "Central Topic"),
        (NodeType.TOPIC, "Main Branch"),
        (NodeType.SUBTOPIC, "Sub Branch"),
        (NodeType.DETAIL, "Fine Detail"),
        (NodeType.QUESTION, "Question"),
        (NodeType.IDEA, "Idea"),
        (NodeType.SOURCE, "Source"),
    ]
    for node_type, text in node_types:
        try:
            node = MindNode(
                id=f"test_{node_type.value}",
                text=text,
                node_type=node_type
            )
            print(f'  OK - {node_type.value}: {node.text}')
        except Exception as e:
            print(f'  ERROR - {node_type.value}: {e}')

    # Test 6: Build complete mind map
    print('\n[Test 6] Building Complete Mind Map')
    try:
        mindmap2 = MindMap(
            title="Project Planning",
            layout=LayoutType.TREE,
            root_node="root"
        )

        # Root
        root = MindNode(
            id="root",
            text="Project X",
            node_type=NodeType.ROOT,
            emoji="rocket",
            color="#FF6B6B"
        )
        mindmap2.nodes["root"] = root

        # Main branches
        branches = [
            ("Planning", NodeType.TOPIC, "#4ECDC4"),
            ("Development", NodeType.TOPIC, "#45B7D1"),
            ("Testing", NodeType.TOPIC, "#96CEB4"),
            ("Deployment", NodeType.TOPIC, "#FFEAA7"),
        ]

        for i, (text, node_type, color) in enumerate(branches):
            node_id = f"root_{i}"
            node = MindNode(
                id=node_id,
                text=text,
                node_type=node_type,
                parent_id="root",
                color=color
            )
            mindmap2.nodes[node_id] = node
            root.children.append(node_id)

            # Add sub-topics
            for j in range(2):
                sub_id = f"{node_id}_{j}"
                sub_node = MindNode(
                    id=sub_id,
                    text=f"Sub-task {j+1}",
                    node_type=NodeType.SUBTOPIC,
                    parent_id=node_id
                )
                mindmap2.nodes[sub_id] = sub_node
                node.children.append(sub_id)

        print(f'  OK - Built mind map with {len(mindmap2.nodes)} nodes')
        print(f'  OK - Root has {len(root.children)} branches')

        # Generate markdown
        md = mindmap2.to_markdown()
        print(f'  OK - Markdown output generated ({len(md)} chars)')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 7: D3 format conversion
    print('\n[Test 7] D3 Format Conversion')
    try:
        generator2 = MindMapGenerator(config)
        d3_data = generator2._convert_to_d3_format(mindmap2)
        print(f'  OK - Converted to D3 format')
        print(f'  OK - Keys: {list(d3_data.keys())}')
        if 'children' in d3_data:
            print(f'  OK - Children count: {len(d3_data["children"])}')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    # Test 8: Default mind map creation
    print('\n[Test 8] Default Mind Map Creation')
    try:
        generator3 = MindMapGenerator(config)
        default_mindmap = generator3._create_default_mindmap("Test Topic")
        print(f'  OK - Default mind map created: {default_mindmap.title}')
        print(f'  OK - Layout: {default_mindmap.layout.value}')
        print(f'  OK - Nodes: {len(default_mindmap.nodes)}')
        print(f'  OK - Root children: {len(default_mindmap.nodes[default_mindmap.root_node].children)}')
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()

    print('\n' + '=' * 70)
    print('MindMapGenerator Skill Test Complete!')
    print('=' * 70)

if __name__ == '__main__':
    asyncio.run(test_mindmap_generator())
