import json, glob, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"D:\ai项目\metacog-distiller\metacog-system"

def is_garbled(text):
    if not text: return False
    if '\ufffd' in text: return True
    # Check for mojibake in CJK range
    for ch in text:
        cp = ord(ch)
        if 0x80 <= cp <= 0xA0:
            return True
    return False

def clean_text(text):
    if not text: return text
    # Remove replacement characters
    text = text.replace('\ufffd', '')
    # Remove C1 control characters (0x80-0x9F)
    text = re.sub('[\x80-\x9f]', '', text)
    return text.strip()

# ─── Scan and fix all JSONs ───
for fname in ['knowledge_graph.json', 'metacog_graph.json', 'learning_graph.json']:
    path = os.path.join(BASE, fname)
    data = json.load(open(path, 'r', encoding='utf-8'))
    
    cleaned = 0
    for n in data['nodes']:
        for field in ['label', 'summary', 'wiki_description', 'baidu_description']:
            if field in n and n[field]:
                old = n[field]
                new = clean_text(old)
                if old != new:
                    n[field] = new
                    cleaned += 1
    
    if cleaned > 0:
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'{fname}: {cleaned} fields cleaned')
    else:
        print(f'{fname}: already clean')

# ─── Re-verify ───
for fname in ['knowledge_graph.json', 'metacog_graph.json', 'learning_graph.json']:
    path = os.path.join(BASE, fname)
    data = json.load(open(path, 'r', encoding='utf-8'))
    garbled = 0
    for n in data['nodes']:
        for field in ['label', 'summary', 'wiki_description', 'baidu_description']:
            if is_garbled(n.get(field, '')):
                garbled += 1
                print(f'  STILL GARBLED: {n["id"]} {field}')
                break
    print(f'{fname}: {len(data["nodes"])} nodes, remaining garbled: {garbled}')

print('DONE')
