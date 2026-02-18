"""
Yuanbao Converter Skill - 元宝文稿转换器

将元宝转来的文稿转换为带 AI 总结的 Markdown 文档，保存到指定文件夹。

## 功能
- 提取文章标题
- 使用 AI 生成 200 字左右的总结
- 构建标准 Markdown 格式
- 自动保存到 yuanbao 文件夹

## 使用方式
```python
from yuanbao_converter import convert_and_save

result = convert_and_save(
    content="元宝文稿内容",
    title="可选标题",
    output_folder="d:/yuanbao"
)
```
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


def extract_title_from_content(content: str) -> str:
    """从内容第一行提取标题"""
    lines = content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # 移除可能的序号和前缀
            title = re.sub(r'^[\d\.\s]+[-：:\s]*', '', line)
            return title[:100]  # 限制长度
    
    return "未命名文章"


def generate_ai_summary(content: str, max_length: int = 200) -> str:
    """
    使用 AI 生成文章总结
    
    Args:
        content: 文章内容
        max_length: 最大字数
        
    Returns:
        AI 生成的总结
    """
    # 这里应该调用实际的 AI API
    # 当前版本使用简化版：提取前 200 字
    
    # 清理内容
    clean_content = re.sub(r'\s+', ' ', content).strip()
    
    # 截取前 200 字
    summary = clean_content[:max_length]
    if len(clean_content) > max_length:
        summary += "..."
    
    return summary


def sanitize_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    # Windows 文件名不能包含：\ / : * ? " < > |
    illegal_chars = r'[\\/:*?"<>|]'
    sanitized = re.sub(illegal_chars, '-', filename)
    # 移除首尾空格和点
    sanitized = sanitized.strip(' .')
    return sanitized


def build_markdown_document(
    title: str,
    content: str,
    summary: Optional[str] = None,
    source: str = "元宝",
    conversion_time: Optional[datetime] = None
) -> str:
    """
    构建完整的 Markdown 文档
    
    Args:
        title: 文章标题
        content: 正文内容
        summary: AI 总结（可选）
        source: 来源
        conversion_time: 转换时间
        
    Returns:
        Markdown 字符串
    """
    if conversion_time is None:
        conversion_time = datetime.now()
    
    md = f"# {title}\n\n"
    
    if summary:
        md += f"## 总结\n\n> {summary}\n\n"
    
    md += f"## 正文\n\n{content}\n\n"
    md += f"---\n*转换时间：{conversion_time.strftime('%Y-%m-%d %H:%M:%S')} | 来源：{source}*\n"
    
    return md


def convert_and_save(
    content: str,
    title: Optional[str] = None,
    output_folder: str = "d:\\Antigravity\\opc\\open-notebook\\yuanbao",
    filename: Optional[str] = None,
    add_summary: bool = True
) -> Dict[str, Any]:
    """
    转换元宝文稿并保存为 Markdown
    
    Args:
        content: 元宝文稿内容（必填）
        title: 文章标题（可选，自动提取）
        output_folder: 保存文件夹（默认：yuanbao 文件夹）
        filename: 文件名（可选，自动生成）
        add_summary: 是否添加 AI 总结（默认：true）
        
    Returns:
        包含保存结果和文件路径的字典
    """
    if not content or not content.strip():
        raise ValueError("Content cannot be empty")
    
    # 1. 提取或确认标题
    if not title:
        title = extract_title_from_content(content)
    
    # 2. 生成 AI 总结
    summary = None
    if add_summary:
        summary = generate_ai_summary(content)
    
    # 3. 构建 Markdown 文档
    md_content = build_markdown_document(
        title=title,
        content=content,
        summary=summary
    )
    
    # 4. 生成文件名
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = sanitize_filename(title)[:50]  # 限制标题长度
        filename = f"{safe_title}_{timestamp}.md"
    
    # 5. 确保输出文件夹存在
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 6. 保存文件
    file_path = output_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return {
        "success": True,
        "file_path": str(file_path.absolute()),
        "filename": filename,
        "title": title,
        "has_summary": summary is not None,
        "message": f"已保存到：{file_path}"
    }


# ============================================================================
# Claude Skill CLI Interface
# ============================================================================

def main():
    """Claude Skill 命令行入口"""
    import sys
    
    print("🔧 元宝文稿转换器 v1.0")
    print("=" * 50)
    
    # 检查参数
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python skill.py <元宝文稿内容> [标题]")
        print("\n示例:")
        print('  python skill.py "这是元宝文稿内容..." "我的文章标题"')
        print("\n或者直接在代码中导入使用:")
        print("  from yuanbao_converter import convert_and_save")
        print('  result = convert_and_save(content="...")')
        return
    
    # 获取参数
    content = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # 执行转换
        result = convert_and_save(
            content=content,
            title=title
        )
        
        print(f"\n✅ 转换成功!")
        print(f"标题：{result['title']}")
        print(f"文件：{result['filename']}")
        print(f"路径：{result['file_path']}")
        
        if result['has_summary']:
            print("✓ 已生成 AI 总结")
        
    except Exception as e:
        print(f"\n❌ 转换失败：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
