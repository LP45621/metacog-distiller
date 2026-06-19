#!/usr/bin/env python3
"""Metacog Analyzer — 读取三个图谱JSON，输出静态分析图表到 reports/。
   全路径相对：Path(__file__).resolve().parent 定位项目根目录。
   迁移项目到任何位置均可运行。"""

import json, sys, os
from pathlib import Path
from datetime import datetime

# ═══ 路径：全相对 ═══
SYS = Path(__file__).resolve().parent            # metacog-system/ (本脚本所在目录)
ROOT = SYS.parent                                 # metacog-distiller/
REPORTS = ROOT / "reports"                       # 输出目录
REPORTS.mkdir(exist_ok=True)

# ═══ 加载数据 ═══
def load_graph(name):
    path = SYS / f"{name}_graph.json"
    if not path.exists():
        print(f"⚠️ {path} not found, skipping")
        return None
    return json.loads(path.read_text(encoding="utf-8"))

meta = load_graph("metacog")
know = load_graph("knowledge")
learn = load_graph("learning")

# ═══ 图表渲染 ═══
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import networkx as nx
from collections import Counter

# 查找中文字体并全局设置
zh_font_path = None
for f in fm.fontManager.ttflist:
    if any(k in f.name.lower() for k in ['microsoft yahei','simhei','noto sans cjk','pingfang','source han']):
        zh_font_path = f.fname
        break
if zh_font_path:
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = [fm.FontProperties(fname=zh_font_path).get_name()]
else:
    print("Warning: No CJK font found, labels may show as boxes")
plt.rcParams['axes.unicode_minus'] = False

# ═══ 颜色方案 ═══
META_COLORS = {
    'domain':'#316dca','belief':'#9e6a03','decision':'#1f6f3b','bias':'#8b3a3a',
    'strategy':'#6e40c9','emotion':'#b0376b','evidence':'#3b5e7a','source':'#6e4a2e','meta':'#4a2d7a'
}
KNOW_COLORS = {
    'concept':'#1a5fb4','fact':'#1f6f3b','tool':'#935e00','resource':'#6a2b8a',
    'insight':'#991b4e','question':'#8b3a3a','project':'#116b63','skill':'#303fa0'
}
LEARN_COLORS = {'asked':'#f85149','learning':'#d2991d','todo':'#484f58','learned':'#3fb950','question':'#f778ba'}

def build_nx(graph, colors, status_key=None):
    """Convert JSON graph to networkx graph"""
    G = nx.Graph()
    nodes = []
    for n in graph.get("nodes", []):
        nid = n.get("id", "")
        c = n.get(status_key if status_key else "type", "")
        label = n.get("label", "")[:15]
        # Strip emoji for matplotlib compatibility
        label = ''.join(ch for ch in label if ord(ch) < 0x2600 or ord(ch) > 0x27BF)
        label = ''.join(ch for ch in label if ord(ch) < 0x1F000)
        G.add_node(nid, label=label, color=colors.get(c, "#666"),
                   size=max(200, 800 / (n.get("depth", 0) + 1)))
        nodes.append(nid)
    for e in graph.get("edges", []):
        G.add_edge(e.get("source", ""), e.get("target", ""))
    return G

def draw_graph(G, title, ax):
    """Draw a networkx graph on a matplotlib axis"""
    pos = nx.spring_layout(G, k=1.8, iterations=50, seed=42)
    colors = [G.nodes[n].get("color", "#666") for n in G.nodes]
    sizes = [G.nodes[n].get("size", 300) for n in G.nodes]
    labels = {n: G.nodes[n].get("label", n) for n in G.nodes}

    nx.draw_networkx_edges(G, pos, alpha=0.3, edge_color="#555", ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=sizes, alpha=0.9, ax=ax)
    nx.draw_networkx_labels(G, pos, labels, font_size=6, font_family='sans-serif',
                           font_color='white', ax=ax)
    ax.set_title(title, fontsize=14, color='white')
    ax.set_facecolor('#0d1117')
    ax.axis('off')

# ═══ 生成统计 ───
stats_text = f"""Metacog Analysis Report
{'='*50}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Project: metacog-distiller

"""

for name, g in [("元认知", meta), ("知识", know), ("学习中", learn)]:
    if g is None:
        stats_text += f"\n{name}: DATA NOT FOUND\n"
        continue
    nodes = g.get("nodes", [])
    edges = g.get("edges", [])
    types = Counter(n.get("type", "?") for n in nodes)
    confs = Counter(n.get("confidence", "?") for n in nodes)
    deps = Counter(n.get("depth", 0) for n in nodes)
    
    stats_text += f"""
{name}图谱
{'-'*30}
节点: {len(nodes)}  连线: {len(edges)}
类型分布: {dict(types)}
置信度: {dict(confs)}
深度分布: {dict(deps)}
"""
    if name == "学习中":
        statuses = Counter(n.get("status", "?") for n in nodes)
        stats_text += f"学习状态: {dict(statuses)}\n"

stats_path = REPORTS / "analysis_report.txt"
stats_path.write_text(stats_text, encoding="utf-8")
print(stats_text)

# ═══ 绘制图表 ═══
fig = plt.figure(figsize=(28, 10), facecolor='#0d1117')

if meta:
    ax1 = fig.add_subplot(1, 3, 1)
    G1 = build_nx(meta, META_COLORS)
    draw_graph(G1, f"Metacognition ({len(meta['nodes'])} nodes)", ax1)

if know:
    ax2 = fig.add_subplot(1, 3, 2)
    G2 = build_nx(know, KNOW_COLORS)
    draw_graph(G2, f"Knowledge ({len(know['nodes'])} nodes)", ax2)

if learn:
    ax3 = fig.add_subplot(1, 3, 3)
    G3 = build_nx(learn, LEARN_COLORS, status_key="status")
    draw_graph(G3, f"Learning ({len(learn['nodes'])} nodes)", ax3)

plt.tight_layout(pad=3)
img_path = REPORTS / "metacog_analysis.png"
fig.savefig(img_path, dpi=150, facecolor='#0d1117', bbox_inches='tight')
plt.close()
print(f"\n[DONE] Chart: {img_path}")
print(f"[DONE] Report: {stats_path}")
print(f"\nOutputs -> {REPORTS}")
