#!/usr/bin/env python3
"""Verify the generated note_graph.json."""
import json
from collections import Counter

h = json.loads(open("note_graph.json", encoding="utf-8").read())
types = Counter(n["type"] for n in h["nodes"])
print("Node type distribution:")
for t, c in types.most_common():
    print(f"  {t}: {c}")

sorted_nodes = sorted(h["nodes"], key=lambda n: n["backlink_count"], reverse=True)
print("\nTop 10 most linked-to nodes (hub nodes):")
for n in sorted_nodes[:10]:
    print(f"  {n['label']}: {n['backlink_count']} backlinks, {n['link_count']} forward links")

bidirectional = [e for e in h["edges"] if e["label"] == "双向链接"]
monodirectional = [e for e in h["edges"] if e["label"] == "单向链接"]
print(f"\nTotal: {len(h['nodes'])} nodes, {len(h['edges'])} edges")
print(f"  Bidirectional: {len(bidirectional)}")
print(f"  Unidirectional: {len(monodirectional)}")

# Check that knowledge-explorer.html was generated
import os
html_path = "../knowledge-explorer.html"
html_size = os.path.getsize(html_path)
print(f"\n{html_path}: {html_size} bytes ({html_size/1024:.0f} KB)")
print("Data embedded:", "var graphData =" in open(html_path, encoding="utf-8").read())
