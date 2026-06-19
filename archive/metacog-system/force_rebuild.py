"""强制重建三个HTML，数据直接拼接，不用任何搜索替换"""
import json
from pathlib import Path

ROOT = Path(r"D:\ai项目\metacog-distiller")
SYS = ROOT / "metacog-system"

def force_rebuild(html_path, json_path):
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    data_json = json.dumps(data, ensure_ascii=False)
    html = Path(html_path).read_text(encoding="utf-8")
    
    # 找 var ed= 位置
    marker = "var ed="
    idx = html.find(marker)
    if idx < 0:
        print(f"ERROR: {marker} not found in {html_path}")
        return
    
    # 找 var ed= 前面的所有内容
    prefix = html[:idx + len(marker)]
    
    # 找 } 后面紧跟着 if(ed.nodes 或 if(embeddedData.nodes 的位置
    # 从末尾开始找，确保是真正的 JS 代码而不是 JSON 内的字符串
    tail_patterns = ["}if(ed.nodes", "};\nif(ed.nodes", "}if(embeddedData.nodes", "};\nif(embeddedData.nodes"]
    tail_start = -1
    for p in tail_patterns:
        pos = html.rfind(p)
        if pos > idx:
            tail_start = pos + 1  # 跳过 }
            break
    
    if tail_start < 0:
        # 用最后的 ;if 作为退路
        tail_start = html.rfind(";if(ed.nodes")
        if tail_start > idx:
            tail_start += 1
    
    if tail_start < idx:
        print(f"ERROR: tail not found in {html_path}")
        return
    
    suffix = html[tail_start:]
    
    new_html = prefix + data_json + ";\n" + suffix
    Path(html_path).write_text(new_html, encoding="utf-8")
    print(f"Rebuilt {html_path}: {len(new_html)} bytes")

force_rebuild(ROOT / "metacognition-mapper.html", SYS / "metacog_graph.json")
force_rebuild(ROOT / "knowledge-mapper.html", SYS / "knowledge_graph.json")
force_rebuild(ROOT / "learning-mapper.html", SYS / "learning_graph.json")

# 验证
for name in ["metacognition-mapper", "knowledge-mapper", "learning-mapper"]:
    html = (ROOT / f"{name}.html").read_text(encoding="utf-8")
    i = html.find("var ed=")
    print(f"{name}: starts with {repr(html[i+8:i+16])}")
