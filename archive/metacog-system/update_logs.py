import json, os, glob, re
from pathlib import Path
from collections import Counter
from datetime import datetime

BASE = Path(r"D:\ai项目\metacog-distiller")
SYS = BASE / "metacog-system"
OBS_LOG = SYS / "observation_log.md"
KNOW_LOG = SYS / "knowledge_log.md"

# ─── 1. Read all recent sessions ───
sdir = Path.home() / '.codewhale' / 'sessions'
files = sorted(glob.glob(str(sdir / '*.json')), key=os.path.getmtime, reverse=True)

# Sessions already in observation log (from June 11-13): skip a77d,b8ab,2abc,9a86,3286,bbad,15a8,b48b,5a8a,e35e,43e6
# New sessions since last full distillation: 8b8d6ba4, 15a8a18e, 2294ae06, e7edff7f, 8aadf86c, 64b1ec52
old_ids = {'a77d632a','b8abb401','2abcfa93','9a8699d6','3286e3db','bbad0713',
           '15a8a18e2','b48b40a0','5a8a4fa6','e35e1fec','43e600aa','70f12cfd','adfe7fd6'}

new_data = []
for f in files[:10]:
    fid = os.path.basename(f)[:8]
    # Skip already-processed sessions
    # But 15a8a18e on June 16 is a different session from 15a8a18e on June 12
    mtime = datetime.fromtimestamp(os.path.getmtime(f))
    if mtime < datetime(2026, 6, 13, 18, 0, 0):
        continue
    
    size_kb = os.path.getsize(f) / 1024
    try:
        data = json.load(open(f, 'r', encoding='utf-8'))
        msgs = data if isinstance(data, list) else data.get('messages', data.get('content', []))
        user_first = ""
        for m in (msgs if isinstance(msgs, list) else []):
            if isinstance(m, dict) and m.get('role') == 'user':
                ct = m.get('content', '')
                if isinstance(ct, str):
                    user_first = ct[:150]
                elif isinstance(ct, list):
                    for c2 in ct:
                        if isinstance(c2, dict) and c2.get('type') == 'text':
                            user_first = c2['text'][:150]
                            break
                break
        new_data.append({
            'id': fid,
            'date': mtime.strftime('%m-%d %H:%M'),
            'size_kb': int(size_kb),
            'first_msg': user_first
        })
    except:
        pass

print("New sessions since last distillation:")
for nd in new_data:
    print(f"  {nd['date']} {nd['id']}: {nd['first_msg'][:80]}")

# ─── 2. Append to observation log ───
obs_entry = f"""

---

## 新会话 2026-06-14 ~ 06-18

**数据源**：CodeWhale 6 个新会话，{sum(nd['size_kb'] for nd in new_data)}KB 总计。

"""
for nd in new_data:
    obs_entry += f"- [{nd['date']}] {nd['id'][:8]}: {nd['first_msg'][:100]}\n"

obs_entry += """
### 新增元认知信号

| 信号 | 维度 | 强度 | 证据 |
|------|------|------|------|
| 项目结构优化迭代 | strategy | likely | 多次要求 reorganize/clean/optimize 项目目录结构，从 workspace 迁移到 D 盘固定位置 |
| 自动化依赖 | meta | certain | "更新 HTML 变成自动化流程"——要求一切写入 automation/skill，拒绝手动触发 |
| 编码问题敏感 | tool_use | likely | 发现乱码后要求逐层 debug，并更新 skill 防止再生——质量意识强 |
| 技术栈文档化 | strategy | likely | 要求将 debug 经验和技术细节写入 skill——重视知识沉淀 |

### 已有信号强化

| 信号 | 新证据 |
|------|--------|
| 验证习惯(n6) | "html还是看不了！"——问题不解决持续追问 |
| 完整性需求(n13) | 要求"找出新的历史记录更新三个图谱"——全覆盖 |
| 系统性架构(n10) | 项目从临时目录迁移到固定 D 盘路径——持久化落地 |
| 先查后建(n11) | "obsidian是什么"——在构建知识图谱同时仍在探索已知工具 |

### 知识新增

- **Obsidian**：被问及但未深入，可能作为参考对照
- **AD7606 数据手册阅读**：嵌入式项目持续推进
- **项目迁移模式**：workspace → D:/github/RK... → D:/ai项目/metacog-distiller

---

<!-- 下一轮蒸馏从此行之后开始 -->
"""

with open(OBS_LOG, 'r', encoding='utf-8') as f:
    old_obs = f.read()
old_obs = old_obs.replace('<!-- 下一轮蒸馏从此行之后开始 -->', obs_entry)
with open(OBS_LOG, 'w', encoding='utf-8') as f:
    f.write(old_obs)
print(f"\nObservation log updated: {OBS_LOG}")

# ─── 3. Append to knowledge log ───
know_entry = """

---

## 新会话 2026-06-14 ~ 06-18

### 工具发现
- **Obsidian**：知识管理工具，被问及但未采用——用户选择了自建方案

### 技术实践
- **项目持久化迁移**：workspace → D:/github/RK... → D:/ai项目/metacog-distiller
- **AD7606 SPI 通信**：阅读数据手册，涉及时钟极性/相位、通道配置
- **编码调试经验**：Unicode 控制字符过滤、CJK 字体栈配置、HTML innerHTML 安全清洗

### 架构演进
- **build_final_html.py v3**：f-string 构建 + D3.js 内联 + safe_str 清洗 + CJK 字体栈
- **clean_garbled.py**：批量 JSON 乱码检测修复工具
- **自动化管道**：确认每 4h 自动蒸馏 + HTML 生成全链路

---

<!-- 下一轮知识蒸馏从此行之后开始 -->
"""

with open(KNOW_LOG, 'r', encoding='utf-8') as f:
    old_know = f.read()
old_know = old_know.replace('<!-- 下一轮知识蒸馏从此行之后开始 -->', know_entry)
with open(KNOW_LOG, 'w', encoding='utf-8') as f:
    f.write(old_know)
print(f"Knowledge log updated: {KNOW_LOG}")

print("\nDone - logs updated. Ready for distillation.")
