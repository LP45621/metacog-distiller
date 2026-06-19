import json, sys
sys.stdout.reconfigure(encoding='utf-8')
h = open(r'D:\ai项目\metacog-distiller\knowledge-mapper.html','r',encoding='utf-8').read()
# Find var ed boundary
idx = h.find("var ed =")
start = idx + len("var ed =")
close = h.find("};\nif(ed.nodes", start)
if close < 0: close = h.find("}if(ed.nodes", start)
json_str = h[start:close+1]
try:
    d = json.loads(json_str)
    for n in d['nodes'][:5]:
        lbl = n['label']
        s = n.get('summary','')[:60]
        print(f'{n["id"]}: {lbl}')
        print(f'  summary: {s}')
        print(f'  wiki: {n.get("wiki_description","")[:40]}')
    print(f'\nTotal: {len(d["nodes"])} nodes')
except Exception as e:
    print(f'PARSE ERROR: {e}')
    print(json_str[:200])
