"""从知识图谱中拆分 AI 调度能力节点到独立图谱"""
import json
from pathlib import Path

BASE = Path(r"D:\ai项目\metacog-distiller")
SYS = BASE / "metacog-system"

know = json.loads((SYS / "knowledge_graph.json").read_text(encoding="utf-8"))

# ─── 分类所有节点 ───
AI_IDS = {
    # AI 平台 & 工具
    'k1',   # CodeWhale
    'k4',   # Agent体系
    'k6',   # FreeLLMAPI
    'k7',   # mimo
    'k21',  # DeepSeek平台
    'k24',  # 模型选择策略
    'k2',   # 元认知蒸馏（既是概念也是AI调度产物）
    'k5',   # less-tokens（LLM token优化）
}

RENDER_IDS = {
    # 可视化/渲染（留在知识库，但也映射到AI能力作为渲染层）
    'k3',   # D3.js力导向图
    'k26',  # D3.js内联部署
}

HUMAN_IDS = {
    # 用户个人知识 —— 留在知识库不变
    'k8', 'k9', 'k10',
    'k11','k12','k13','k14','k15','k16','k17','k18','k19','k20',
    'k22','k23','k25','k27',
    'k30','k31','k32','k33','k34','k35','k36','k37','k38','k39','k40','k41','k42','k43','k44',
}

# ─── 构建 AI 能力图谱 ───
ai_nodes = []
ai_edges = []
ai_node_ids = set()

# 1. AI 核心节点
for n in know['nodes']:
    if n['id'] in AI_IDS:
        new_n = dict(n)
        new_n['id'] = 'a' + n['id'][1:]  # k1 -> a1
        ai_nodes.append(new_n)
        ai_node_ids.add(n['id'])

# 2. 渲染层节点
for n in know['nodes']:
    if n['id'] in RENDER_IDS:
        new_n = dict(n)
        new_n['id'] = 'a' + n['id'][1:]
        ai_nodes.append(new_n)
        ai_node_ids.add(n['id'])

# 3. 迁移相关连线
id_map = {}
for n in ai_nodes:
    orig_id = 'k' + n['id'][1:]  # a1 -> k1
    id_map[orig_id] = n['id']

for e in know['edges']:
    src = e['source']
    tgt = e['target']
    if src in id_map and tgt in id_map:
        ai_edges.append({
            'source': id_map[src],
            'target': id_map[tgt],
            'type': e['type'],
            'label': e.get('label', '')
        })
    elif src in id_map:
        ai_edges.append({
            'source': id_map[src],
            'target': tgt,
            'type': e['type'],
            'label': e.get('label', '')
        })
    elif tgt in id_map:
        ai_edges.append({
            'source': src,
            'target': id_map[tgt],
            'type': e['type'],
            'label': e.get('label', '')
        })

# 4. 添加 AI 特有的新节点
ai_nodes.append({
    'id': 'a_new_1',
    'label': 'AI 编排管道',
    'type': 'concept',
    'depth': 1,
    'confidence': 'certain',
    'summary': 'CodeWhale agent + skill + automation 三层架构构成完整的 AI 编排管道：agent_open 创建子 agent 并行工作，skill 装载领域知识，automation_create 创建定时任务。实现 AI 监督 AI 的嵌套代理模式。',
    'wiki_description': '',
    'baidu_description': ''
})
ai_nodes.append({
    'id': 'a_new_2', 
    'label': '元认知蒸馏管道',
    'type': 'concept',
    'depth': 1,
    'confidence': 'certain',
    'summary': '5阶段自动化蒸馏：读日志→提取信号→更新图谱→联网补充→生成HTML。通过 CodeWhale automation 每4小时触发，实现从原始对话到可视化图谱的全自动管道。',
    'wiki_description': '',
    'baidu_description': ''
})
ai_edges.append({'source': 'a_new_1', 'target': 'a1', 'type': 'part_of', 'label': 'CodeWhale实现'})
ai_edges.append({'source': 'a_new_1', 'target': 'a4', 'type': 'part_of', 'label': 'Agent体系支撑'})
ai_edges.append({'source': 'a_new_2', 'target': 'a2', 'type': 'part_of', 'label': '蒸馏实现'})
ai_edges.append({'source': 'a_new_2', 'target': 'a_new_1', 'type': 'depends_on', 'label': '蒸馏依赖编排管道'})

# 5. 保存
ai_graph = {
    'user_id': 'mu',
    'created': '2026-06-18T10:00:00',
    'type': 'ai_capability',
    'total_nodes': len(ai_nodes),
    'total_edges': len(ai_edges),
    'nodes': ai_nodes,
    'edges': ai_edges
}
(SYS / "ai_capability_graph.json").write_text(json.dumps(ai_graph, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"AI Capability Graph: {len(ai_nodes)} nodes, {len(ai_edges)} edges")
for n in ai_nodes:
    print(f"  {n['id']}: {n['label']} ({n['type']})")

# ─── 6. 从知识图谱中移除 AI 节点 ───
new_know_nodes = [n for n in know['nodes'] if n['id'] not in AI_IDS]
new_know_edges = [e for e in know['edges'] if e['source'] not in AI_IDS and e['target'] not in AI_IDS]
know['nodes'] = new_know_nodes
know['edges'] = new_know_edges
(SYS / "knowledge_graph.json").write_text(json.dumps(know, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nKnowledge Graph (cleaned): {len(new_know_nodes)} nodes, {len(new_know_edges)} edges")
