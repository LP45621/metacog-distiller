import json
h = open(r'D:\ai项目\metacog-distiller\knowledge-mapper.html', encoding='utf-8').read()
idx = h.find('var ed = ')
end = h.find('if(ed.nodes', idx)
js = h[idx+9:end].strip().rstrip(';').rstrip()
try:
    d = json.loads(js)
    w = sum(1 for n in d['nodes'] if n.get('wiki_description',''))
    print(f'OK: {len(d["nodes"])} nodes, wiki={w}')
except Exception as e:
    print(f'FAIL: {e}')
    print('excerpt:', js[:100])
