import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d = json.load(open(r'D:\ai项目\metacog-distiller\metacog-system\ai_capability_graph.json', encoding='utf-8'))
ids = {n['id'] for n in d['nodes']}
print('Node IDs:', sorted(ids))
bad = []
for e in d['edges']:
    if e['source'] not in ids or e['target'] not in ids:
        bad.append(e)
print(f'Total edges: {len(d["edges"])}, Bad: {len(bad)}')
for e in bad:
    print(f'  BAD: {e["source"]} -> {e["target"]} ({e.get("label","")})')
