import json, sys
sys.stdout.reconfigure(encoding='utf-8')
h = open(r'D:\ai项目\metacog-distiller\knowledge-mapper.html', encoding='utf-8').read()
i = h.find('var ed =')
e = h.find('}if(ed.nodes', i)
d = json.loads(h[i+9:e+1])
garbled = sum(1 for n in d['nodes'] if '\ufffd' in n.get('label','') or '\ufffd' in n.get('summary',''))
wiki = sum(1 for n in d['nodes'] if n.get('wiki_description',''))
baidu = sum(1 for n in d['nodes'] if n.get('baidu_description',''))
print(f'{len(d["nodes"])} nodes, garbled={garbled}, wiki={wiki}, baidu={baidu}')
for n in d['nodes']:
    if 'SPI' in n['label']:
        print(f'SPI label: {n["label"]}')
        print(f'SPI summary: {n.get("summary","")[:100]}')
        print(f'SPI wiki: {n.get("wiki_description","")[:100]}')
        break
