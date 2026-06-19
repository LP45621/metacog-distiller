import json, os, glob
from pathlib import Path
from collections import Counter

sdir = Path.home() / '.codewhale' / 'sessions'
files = sorted(glob.glob(str(sdir / '*.json')), key=os.path.getmtime, reverse=True)

print("=== Recent sessions ===")
for f in files[:10]:
    fname = os.path.basename(f)[:8]
    size_kb = os.path.getsize(f) / 1024
    try:
        data = json.load(open(f, 'r', encoding='utf-8'))
        msgs = data if isinstance(data, list) else data.get('messages', data.get('content', []))
        user_msgs = []
        for m in (msgs if isinstance(msgs, list) else []):
            if isinstance(m, dict) and m.get('role') == 'user':
                content = m.get('content', '')
                if isinstance(content, str):
                    user_msgs.append(content[:150])
                elif isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get('type') == 'text':
                            user_msgs.append(c['text'][:150])
                            break
            if len(user_msgs) >= 2:
                break
        
        all_text = ' '.join(user_msgs)
        terms = ['元认知','蒸馏','agent','automation','skill','可视化','html','乱码','编码','debug',
                 'deepseek','嵌入','后台','bug','fix','build','优化','wiki','百度','cmd',
                 'power','shell','端口','服务器','http','exe','pyinstaller','打包']
        found = [t for t in terms if t.lower() in all_text.lower()]
        first_msg = user_msgs[0][:80] if user_msgs else "(no msgs)"
        print(f"{fname} ({size_kb:.0f}KB): {found[:6]}")
        print(f"  -> {first_msg}")
    except Exception as e:
        print(f"{fname}: ERROR {str(e)[:60]}")
