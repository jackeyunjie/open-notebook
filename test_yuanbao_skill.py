"""Test Yuanbao Converter Skill"""

import sys
sys.path.insert(0, '.')

from skills.yuanbao_converter.skill import convert_and_save

# Test content
test_content = """# 如何高效学习编程

编程是一门需要大量实践的技能。以下是一些高效学习编程的方法：

1. **每天坚持写代码**：保持手感很重要
2. **做项目驱动学习**：通过实际项目巩固知识
3. **阅读优秀代码**：学习他人的编程技巧
4. **写技术博客**：输出倒逼输入
5. **参与开源项目**：与高手交流学习

学习编程没有捷径，但有正确的方法可以让你事半功倍。关键是保持好奇心和持续学习的动力。
"""

print("🔧 Testing Yuanbao Converter Skill...")
print("=" * 50)

try:
    result = convert_and_save(
        content=test_content,
        title="如何高效学习编程",
        add_summary=True
    )
    
    print("\n✅ Success!")
    print(f"Title: {result['title']}")
    print(f"Filename: {result['filename']}")
    print(f"Path: {result['file_path']}")
    print(f"Has Summary: {result['has_summary']}")
    print(f"Message: {result['message']}")
    
except Exception as e:
    print(f"\n❌ Failed: {e}")
    import traceback
    traceback.print_exc()
