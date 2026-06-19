#!/usr/bin/env python3
"""Extract atomic Markdown notes from all three graph JSONs.
   One .md per concept with [[wiki-links]] and backlinks resolution."""
import json
import re
from pathlib import Path

SYS = Path(__file__).resolve().parent
ROOT = SYS.parent
NOTES = ROOT / "notes"
NOTES.mkdir(exist_ok=True)

# Load graphs
graphs = {}
for name in ["knowledge", "metacog", "learning"]:
    path = SYS / f"{name}_graph.json"
    if path.exists():
        graphs[name] = json.loads(path.read_text(encoding="utf-8"))

# Collect nodes, dedup by label
all_nodes = {}
for gtype, gdata in graphs.items():
    for n in gdata.get("nodes", []):
        label = n.get("label", "").strip()
        if not label:
            continue
        safe = re.sub(r'[\\/*?:"<>|]', "_", label)[:60]
        if label in all_nodes:
            all_nodes[label]["sources"].append(gtype)
            all_nodes[label]["types"].add(n.get("type", "concept"))
            if len(n.get("summary", "")) > len(all_nodes[label].get("summary", "")):
                all_nodes[label]["summary"] = n.get("summary", "")
        else:
            all_nodes[label] = {
                "id": n.get("id", ""),
                "filename": safe,
                "types": {n.get("type", "concept")},
                "summary": n.get("summary", ""),
                "confidence": n.get("confidence", "likely"),
                "depth": n.get("depth", 0),
                "sources": [gtype],
            }

print(f"Total unique concepts: {len(all_nodes)}")

# Build edge-based link map
link_map = {}  # label -> {linked_label: [rel_types]}
for gdata in graphs.values():
    id_to_label = {n["id"]: n.get("label", "") for n in gdata.get("nodes", []) if n.get("label")}
    for e in gdata.get("edges", []):
        src = id_to_label.get(e.get("source", ""), "")
        tgt = id_to_label.get(e.get("target", ""), "")
        rel = e.get("type", "relates_to")
        if src and tgt:
            link_map.setdefault(src, {}).setdefault(tgt, []).append(rel)

# Write notes
for label, info in all_nodes.items():
    safe_name = info["filename"]
    npath = NOTES / f"{safe_name}.md"

    # Forward links (this → others)
    links_out = link_map.get(label, {})
    fwd = [f"- [[{tgt}]]  — {', '.join(rels)}" for tgt, rels in links_out.items()]

    # Backlinks (others → this)
    bck = []
    for src, tgts in link_map.items():
        if label in tgts:
            bck.append(f"- [[{src}]]  — {', '.join(tgts[label])}")

    content = f"""---
title: {label}
type: {' | '.join(info['types'])}
confidence: {info['confidence']}
depth: {info['depth']}
sources: {' | '.join(info['sources'])}
---

# {label}

{info['summary']}

## 链接 / Links

"""

    if fwd:
        content += "\n".join(fwd) + "\n"
    else:
        content += "*本节点暂无向外链接*\n"

    content += "\n## 反向链接 / Backlinks\n\n"
    if bck:
        content += "\n".join(bck) + "\n"
    else:
        content += "*尚无其他节点链接到此*\n"

    npath.write_text(content, encoding="utf-8")
    print(f"  ✏️  {safe_name}.md — {len(fwd)}→fwd, {len(bck)}←bck")

print(f"\n✅ {len(all_nodes)} atomic notes written to {NOTES}")
