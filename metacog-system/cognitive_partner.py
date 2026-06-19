#!/usr/bin/env python3
"""
cognitive_partner.py — AI Cognitive Partner Module
===================================================
Implements the "AI作为认知伙伴" constitutional principle (P12):
- AI only suggests connections, asks questions, never auto-classifies
- Spaced-repetition reminders (P6: 发现惊喜)
- Context-summary generation (P7: 语境保留)

Integrates with metacog_workflow.py via API endpoints.
"""
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

SYS = Path(__file__).resolve().parent
ROOT = SYS.parent
NOTES = ROOT / "notes"

# ─── Load note graph data ─────────────────────────────
def load_note_graph():
    path = SYS / "note_graph.json"
    if not path.exists():
        return {"nodes": [], "edges": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_notes_text():
    """Load all note files → dict of {stem: {text, title, file}}."""
    notes = {}
    for f in sorted(NOTES.glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        stem = f.stem
        # Extract title
        title = stem
        m = __import__("re").search(r'^title:\s*(.+)$', text, __import__("re").MULTILINE)
        if m:
            title = m.group(1).strip()
        notes[stem] = {"text": text, "title": title, "file": str(f.relative_to(ROOT))}
    return notes


def get_node_by_label_or_id(graph, query):
    """Find node by label or ID (fuzzy match)."""
    q = query.lower()
    for n in graph.get("nodes", []):
        if n["id"].lower() == q or n.get("label", "").lower() == q:
            return n
    # Fuzzy match
    best = None
    for n in graph.get("nodes", []):
        if q in n.get("label", "").lower():
            best = n
    return best


# ─── Connection Suggestion (P6: 发现惊喜) ─────────────
def _get_id(obj):
    """Extract ID from edge source/target (string or {id: ...})."""
    if isinstance(obj, str):
        return obj
    return obj.get("id", "")


def suggest_connections(focus_note_id=None, max_suggestions=5):
    """
    Find latent connections in the graph.
    Principle P6: proactively recommend hidden associations from old notes.
    Uses a simple graph heuristic: nodes with shared neighbors but no direct edge.
    """
    graph = load_note_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if not nodes:
        return []

    # Build adjacency
    adj = {}
    for n in nodes:
        adj[n["id"]] = set()
    for e in edges:
        s = _get_id(e.get("source", ""))
        t = _get_id(e.get("target", ""))
        if s in adj and t in adj:
            adj[s].add(t)
            adj[t].add(s)

    # Find nodes with shared neighbors but no direct edge
    suggestions = []
    candidates = [n for n in nodes if not focus_note_id or n["id"] != focus_note_id]

    for a in candidates:
        for b in candidates:
            if a["id"] >= b["id"]:
                continue
            if b["id"] in adj.get(a["id"], set()):
                continue  # already connected
            shared = adj.get(a["id"], set()) & adj.get(b["id"], set())
            if len(shared) >= 1:  # at least one shared neighbor
                score = len(shared) + len(adj.get(a["id"], set())) + len(adj.get(b["id"], set()))
                suggestions.append({
                    "a": {"id": a["id"], "label": a.get("label", a["id"]), "type": a.get("type", "")},
                    "b": {"id": b["id"], "label": b.get("label", b["id"]), "type": b.get("type", "")},
                    "shared_neighbors": [{"id": sid, "label": next((n.get("label", sid) for n in nodes if n["id"] == sid), sid)} for sid in list(shared)[:5]],
                    "strength": min(10, score),
                    "reason": f"共同关联了 {len(shared)} 个节点" if shared else "高连接度节点间缺少直接链接",
                })

    # Deduplicate and sort by strength
    seen_pairs = set()
    unique = []
    for s in sorted(suggestions, key=lambda x: -x["strength"]):
        pair = frozenset([s["a"]["id"], s["b"]["id"]])
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            unique.append(s)
            if len(unique) >= max_suggestions:
                break

    return unique


# ─── Space Repetition Reminder (P6: 发现惊喜) ─────────
def get_reminder():
    """
    Suggest revisiting old notes based on graph structure.
    P6 principle: '主动推荐旧笔记中隐藏的关联'.
    P12: 'AI只建议连接、提问，不做自动分类'.
    """
    graph = load_note_graph()
    nodes = graph.get("nodes", [])
    if not nodes:
        return None

    # Strategy: pick notes with high backlink count (hub nodes) that haven't been
    # revisited recently. Also pick "isolated" notes (few links) that might benefit
    # from re-examination.
    random.seed(datetime.now().timestamp())

    # Find "forgotten" notes — those with very few connections
    edges = graph.get("edges", [])
    edge_count = {}
    for n in nodes:
        edge_count[n["id"]] = 0
    for e in edges:
        s = _get_id(e.get("source", ""))
        t = _get_id(e.get("target", ""))
        if s in edge_count:
            edge_count[s] += 1
        if t in edge_count:
            edge_count[t] += 1

    # Pick an "interesting" note — high backlinks or low connections
    candidates = []
    for n in nodes:
        bc = n.get("backlink_count", 0)
        lc = n.get("link_count", 0)
        ec = edge_count.get(n["id"], 0)
        # High backlinks = hub node worth revisiting
        # Low connections = isolated note worth re-examining
        if bc >= 3 or ec <= 1:
            candidates.append((n, bc + (10 if ec <= 1 else 0)))

    if not candidates:
        candidates = [(n, 1) for n in nodes]

    # Weighted random selection
    total_w = sum(w for _, w in candidates)
    r = random.uniform(0, total_w)
    cum = 0
    for n, w in candidates:
        cum += w
        if r <= cum:
            # Build a question/reflection prompt
            ec = edge_count.get(n["id"], 0)
            if ec <= 1:
                prompt = f"你之前写过关于「{n.get('label', n['id'])}」的笔记，但这个概念目前还没有与其他知识建立关联。你觉得它和哪些领域有关联？或许可以链接到新的笔记。"
            elif n.get("backlink_count", 0) >= 3:
                prompt = f"「{n.get('label', n['id'])}」是你的知识体系中一个核心概念，有 {n['backlink_count']} 条反向链接。这触发你思考什么？有没有新的角度可以补充？"
            else:
                prompt = f"还记得关于「{n.get('label', n['id'])}」的笔记吗？当时你记录了一些想法，现在有没有新的认识或补充？"

            return {
                "note": {"id": n["id"], "label": n.get("label", n["id"]), "type": n.get("type", "")},
                "prompt": prompt,
                "edge_count": ec,
                "summary": n.get("summary", "")[:200],
            }

    return None


# ─── Context Summary (P7: 语境保留) ──────────────────
def summarize_cluster(focus_note_id, max_depth=1):
    """
    Generate a context summary for a note and its neighborhood.
    P7: '摘录永远带源链接' — every excerpt carries its source link.
    """
    graph = load_note_graph()
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])

    if focus_note_id not in nodes:
        return {"error": f"Note '{focus_note_id}' not found"}

    # BFS to find neighborhood
    visited = {focus_note_id: 0}
    queue = [focus_note_id]
    while queue:
        current = queue.pop(0)
        d = visited[current]
        if d >= max_depth:
            continue
        for e in edges:
            s = _get_id(e.get("source", ""))
            t = _get_id(e.get("target", ""))
            for neighbor in [s, t]:
                if neighbor in nodes and neighbor not in visited:
                    visited[neighbor] = d + 1
                    queue.append(neighbor)

    cluster = [nodes[nid] for nid in sorted(visited.keys(), key=lambda x: visited[x])]
    focus = nodes[focus_note_id]

    # Build summary
    summary_parts = [f"# 📎 语境摘要: {focus.get('label', focus_note_id)}\n"]
    summary_parts.append(f"> 来源节点: `{focus_note_id}` | 类型: {focus.get('type', '?')} | 深度: {max_depth} 层\n")

    for n in cluster:
        label = n.get("label", n["id"])
        ntype = n.get("type", "?")
        summary = (n.get("summary", "") or "")[:150]
        file_path = n.get("file", f"notes/{n['id']}.md")
        edge_info = []
        for e in edges:
            s = _get_id(e.get("source", ""))
            t = _get_id(e.get("target", ""))
            if s == n["id"] and t in visited:
                edge_info.append(f"→ {nodes[t].get('label', t)} ({e.get('type', 'relates_to')})")
            if t == n["id"] and s in visited:
                edge_info.append(f"← {nodes[s].get('label', s)} ({e.get('type', 'relates_to')})")

        summary_parts.append(f"\n## {label} ({ntype})\n")
        if summary:
            summary_parts.append(f"{summary}\n")
        if edge_info:
            summary_parts.append("关联:\n" + "\n".join(edge_info) + "\n")
        summary_parts.append(f"> 源文件: [{file_path}](/{file_path})\n")

    return {
        "focus": {"id": focus_note_id, "label": focus.get("label", focus_note_id)},
        "cluster_size": len(cluster),
        "summary_markdown": "\n".join(summary_parts),
    }


# ─── Cognitive Partner Prompt (P12) ───────────────────
COGNITIVE_PARTNER_PROMPT = """你是用户的「认知伙伴」(Cognitive Partner)。你的角色不是分类、标记或整理，而是：

1. **提问** — 问好问题，触发思考。不问需要/不需要，而问"为什么""如果""还有呢"
2. **关联** — 当用户提到一个概念时，温和地提醒："这和你之前写的 [[xxx]] 有关联吗？"
3. **反刍** — 定期提醒用户回访旧笔记："你三天前写过 [[yyy]]，现在有新的想法吗？"
4. **不替用户决定** — 从不自动分类、从不替用户归入某个类别。你只建议连接，由用户决定是否建立。

核心原则（12条宪法摘录）：
- 🔗 双向链接：所有关联均双链（建议双向，不强制）
- ✨ 发现惊喜：主动推荐旧笔记中隐藏的关联
- 📎 语境保留：摘录永远带源链接
- 🤖 AI作为认知伙伴：AI只建议连接、提问，不做自动分类
- 🌊 输出自然涌现：密集区域自动触发写作建议

你的所有回复都应该是对话形式——提问、建议、好奇。不要输出 JSON 图谱，不要结构化输出。
除非用户明确要求，否则只做一个好奇的阅读伙伴。

示例回复：
- "你提到了「元认知蒸馏」，这让我想起你之前写的 [[知识蒸馏类比]]。是不是同一个思路的延伸？"
- "我注意到 [[收敛型思维]] 和 [[系统性架构思维]] 之间还没有直接链接，但它们似乎在很多场景下一同出现——你觉得它们有关联吗？"
- "距离你写 [[SPI通信协议]] 已经有一阵子了。这段时间你在嵌入式项目中有没有新的体会？"
"""


# ─── Generate writing suggestion (P11: 输出自然涌现) ─
def get_writing_suggestion():
    """
    P11: Dense graph regions automatically trigger writing suggestions.
    Find the most densely connected cluster and suggest writing about it.
    """
    graph = load_note_graph()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if not nodes or not edges:
        return None

    # Find the node with most connections (dense region)
    conn_count = {n["id"]: 0 for n in nodes}
    for e in edges:
        s = _get_id(e.get("source", ""))
        t = _get_id(e.get("target", ""))
        if s in conn_count:
            conn_count[s] += 1
        if t in conn_count:
            conn_count[t] += 1

    top = sorted(conn_count.items(), key=lambda x: -x[1])[:3]
    suggestions = []
    for nid, count in top:
        n = next((x for x in nodes if x["id"] == nid), None)
        if n and count >= 2:
            suggestions.append({
                "node": {"id": nid, "label": n.get("label", nid), "type": n.get("type", "")},
                "connection_count": count,
                "prompt": f"「{n.get('label', nid)}」在你的知识图谱中有 {count} 条连接，是一个知识密集区域。也许可以写一篇总结笔记，把相关概念串联起来？",
            })

    return suggestions if suggestions else None


# ─── Generate discovery questions (P6) ────────────────
def get_discovery_question():
    """
    P6: 发现惊喜 — ask the user about an unexpected connection.
    """
    suggestions = suggest_connections(focus_note_id=None, max_suggestions=1)
    if suggestions:
        s = suggestions[0]
        return {
            "question": f"我发现「{s['a']['label']}」和「{s['b']['label']}」共享了 {len(s['shared_neighbors'])} 个共同关联节点，但它们之间还没有直接链接。你觉得它们之间有联系吗？",
            "suggestion": s,
        }

    # Fallback: remind about an old note
    reminder = get_reminder()
    if reminder:
        return {"question": reminder["prompt"], "suggestion": None}

    return None


# ─── API handler helpers ──────────────────────────────
def handle_suggest_connections(query_params):
    focus = query_params.get("focus", [None])[0]
    suggestions = suggest_connections(focus_note_id=focus)
    return {"suggestions": suggestions}


def handle_remind():
    reminder = get_reminder()
    suggestion = get_writing_suggestion()
    question = get_discovery_question()
    return {
        "reminder": reminder,
        "writing_suggestion": suggestion,
        "discovery_question": question,
    }


def handle_summarize(query_params):
    note_id = query_params.get("note", [None])[0]
    depth = int(query_params.get("depth", [1])[0])
    if not note_id:
        return {"error": "Missing 'note' parameter"}
    return summarize_cluster(note_id, depth)


def handle_search(query_params):
    q = query_params.get("q", [""])[0]
    if not q:
        return {"results": []}
    notes = load_notes_text()
    results = []
    for stem, info in notes.items():
        if q.lower() in info["text"].lower():
            results.append({
                "id": stem,
                "title": info["title"],
                "file": info["file"],
                "snippet": info["text"][:200],
            })
    return {"results": results, "total": len(results)}
