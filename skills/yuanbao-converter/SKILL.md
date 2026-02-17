---
name: yuanbao-converter
description: 将元宝转来的文稿转换为带AI总结的Markdown文档，保存到指定文件夹
---

# 元宝文稿转MD

将元宝转来的文稿内容转换为标准Markdown格式，自动生成文章总结，并保存到 `/yuanbao` 文件夹。

## 工作流程

1. 接收元宝文稿内容
2. 提取或确认文章标题
3. 使用AI生成文章总结（200字左右）
4. 构建完整Markdown文档（标题→总结→正文→元信息）
5. 保存到 `d:\Antigravity\opc\open-notebook\yuanbao\` 文件夹

## 输出格式

```markdown
# 文章标题

## 总结

> AI生成的文章总结...

## 正文

[元宝原文内容]

---
*转换时间：2026-02-14 15:30:00 | 来源：元宝*
```

## 参数

- `content`：元宝文稿内容（必填）
- `title`：文章标题（可选，自动提取）
- `output_folder`：保存文件夹（默认：`d:\Antigravity\opc\open-notebook\yuanbao`）
- `filename`：文件名（可选，自动生成）
- `add_summary`：是否添加AI总结（默认：true）

## 示例

### 示例1：基础使用
用户：帮我把这个转成MD保存 [粘贴元宝文稿]

Claude：我将为您转换并保存。

1. 提取标题（或询问确认）
2. 生成AI总结
3. 保存文件到 `d:\Antigravity\opc\open-notebook\yuanbao\文章标题_20260214_153000.md`

### 示例2：指定标题
用户：帮我把这个转成MD，标题叫"如何高效学习编程" [粘贴内容]

Claude：使用指定标题转换并保存。

## 注意事项

1. 文件名自动处理非法字符
2. 自动添加时间戳避免覆盖
3. 如未指定标题，从内容第一行提取
4. 输出文件夹自动创建（如不存在）
