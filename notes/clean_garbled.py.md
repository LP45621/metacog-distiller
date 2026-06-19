---
title: clean_garbled.py
type: tool
confidence: certain
depth: 1
sources: knowledge
---

# clean_garbled.py

【本质】批量JSON乱码检测修复工具，过滤Unicode控制字符和替换字符，确保图谱数据在序列化/渲染时不出现乱码。
【关键参数】语言: Python；核心函数: safe_str()过滤C1控制字符(0x80-0x9F)和替换字符(\ufffd)；输入: JSON图谱文件；输出: 清洗后的JSON。
【项目关联】metacog-system核心工具链组件，与build_final_html.py配合构成防乱码管线。

## 链接 / Links

- [[Python编程]]  — depends_on

## 反向链接 / Backlinks

- [[编码调试经验]]  — produces
