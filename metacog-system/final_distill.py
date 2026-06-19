"""Final distillation: update learning graph, regenerate HTMLs, update skills"""
import json
from pathlib import Path

BASE = Path(r"D:\ai项目\metacog-distiller")
SYS = BASE / "metacog-system"

# ─── 1. Update learning graph ───
l = json.loads((SYS / "learning_graph.json").read_text(encoding="utf-8"))
l["nodes"].append({
    "id": "l_k25",
    "label": "Obsidian",
    "type": "tool",
    "depth": 1,
    "confidence": "likely",
    "status": "learning",
    "status_label": "learning",
    "ask_count": 1,
    "summary": "Knowledge management tool, asked but not deeply explored. Possible reference for metacog-distiller design.",
    "wiki_description": "Obsidian is a personal knowledge base app that works on local Markdown files.",
    "baidu_description": "Obsidian 是基于 Markdown 的本地知识管理软件，支持双向链接和图谱视图。"
})
l["nodes"].append({
    "id": "l_k27",
    "label": "Unicode Encoding Safety",
    "type": "skill",
    "depth": 1,
    "confidence": "certain",
    "status": "learned",
    "status_label": "learned",
    "ask_count": 3,
    "summary": "Mastered Unicode control char filtering, CJK font stack config, HTML safe cleaning through this garbled-text debugging session.",
    "wiki_description": "",
    "baidu_description": ""
})
(SYS / "learning_graph.json").write_text(json.dumps(l, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Learning: {len(l['nodes'])} nodes")

# ─── 2. Run HTML builder ───
import subprocess, sys
result = subprocess.run(
    [sys.executable, str(SYS / "build_final_html.py")],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
    timeout=120, cwd=str(SYS)
)
print(result.stdout.strip())
if result.stderr:
    print("STDERR:", result.stderr[:500])

# ─── 3. Verify ───
for name in ["metacognition-mapper", "knowledge-mapper", "learning-mapper"]:
    h = (BASE / f"{name}.html").read_text(encoding="utf-8")
    has_data = "var ed =" in h
    print(f"{name}: {len(h)}B, data={'OK' if has_data else 'MISSING'}")

# ─── 4. Update skill ───
skill_path = Path.home() / ".codewhale" / "skills" / "metacog-distiller" / "SKILL.md"
skill = skill_path.read_text(encoding="utf-8")

tech_section = """
## 🏗️ 项目技术实现

### build_final_html.py 架构

```python
# 核心流程
1. safe_str() 清洗所有节点字段（label/summary/wiki/baidu）
2. clean_data() 批量调用 safe_str
3. json.dumps(ensure_ascii=False) 序列化
4. f-string 嵌入 HTML 模板（CSS用{{}}规避冲突）
5. D3.js 279KB 全文内联（<script>{D3JS}</script>）
6. Path.write_text(encoding='utf-8') 写入
```

### 防乱码管线

| 层级 | 问题 | 措施 |
|------|------|------|
| JSON 源 | 替换字符 \\ufffd 混入 | safe_str: .replace('\\ufffd','') |
| JSON 源 | C1 控制字符(0x80-0x9F) | safe_str: re.sub 过滤 |
| HTML 模板 | CSS/JS 大括号冲突 | CSS: {{}} JS: {} |
| HTML 嵌入 | innerHTML 注入 | 侧边栏用 innerHTML，数据已清洗 |
| 浏览器渲染 | 字体不支持中文 | 指定 PingFang SC + Microsoft YaHei |
| 浏览器渲染 | SVG text 字体 | .style("font-family", "PingFang SC,...") |

### 自动化管道

```
CodeWhale Agent (YOLO/auto)
  └→ automation: metacog-distill-unified (每4h)
       ├→ 阶段1: 读取 observation_log.md
       ├→ 阶段2: 读取 knowledge_log.md
       ├→ 阶段3: 读取 data/deepseek_export.json
       ├→ 阶段4: 联网搜索(如可用)
       └→ 阶段5: build_final_html.py 生成3个HTML到根目录
```

### 项目结构规范

```
D:\\ai项目\\metacog-distiller\\
├── metacognition-mapper.html   ← 双击查看
├── knowledge-mapper.html
├── learning-mapper.html
├── data\\                       ← 原始数据
├── reports\\                    ← 分析报告
└── metacog-system\\             ← 后端
    ├── build_final_html.py      ← HTML生成器
    ├── clean_garbled.py         ← 乱码修复
    ├── update_logs.py           ← 日志追加
    ├── d3.v7.min.js             ← D3离线库
    ├── *_graph.json ×3          ← 图谱数据
    └── *_log.md ×2              ← 观测日志
```

### 诊断与恢复

```bash
# 检查乱码
python clean_garbled.py

# 重建HTML
python build_final_html.py

# 验证
python -c "import json;h=open('knowledge-mapper.html',encoding='utf-8').read();i=h.find('var ed =');e=h.find('}if(ed.nodes',i);d=json.loads(h[i+9:e+1]);print(len(d['nodes']),'nodes')"
```
"""

if "项目技术实现" not in skill:
    skill = skill + tech_section
    skill_path.write_text(skill, encoding="utf-8")
    print("Skill updated with technical implementation details")
else:
    print("Skill already has tech section")

print("\nDONE - All graphs updated, HTMLs regenerated, skill synced")
