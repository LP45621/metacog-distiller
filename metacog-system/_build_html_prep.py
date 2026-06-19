import json
import base64

workspace = r"D:\ai项目\metacog-distiller\metacog-system"

# Read three JSONs
with open(f"{workspace}/metacog_graph.json", "r", encoding="utf-8") as f:
    metacog = json.load(f)
with open(f"{workspace}/knowledge_graph.json", "r", encoding="utf-8") as f:
    knowledge = json.load(f)
with open(f"{workspace}/learning_graph.json", "r", encoding="utf-8") as f:
    learning = json.load(f)

# Base64 encode knowledge (minified)
knowledge_min = json.dumps(knowledge, ensure_ascii=False, separators=(',', ':'))
knowledge_b64 = base64.b64encode(knowledge_min.encode('utf-8')).decode('ascii')

# Save base64 to file for later use
with open(f"{workspace}/_knowledge_b64.txt", "w", encoding="utf-8") as f:
    f.write(knowledge_b64)

# Save minified JSONs
with open(f"{workspace}/_metacog_min.json", "w", encoding="utf-8") as f:
    json.dump(metacog, f, ensure_ascii=False, separators=(',', ':'))
with open(f"{workspace}/_learning_min.json", "w", encoding="utf-8") as f:
    json.dump(learning, f, ensure_ascii=False, separators=(',', ':'))

print(f"Metacog nodes={len(metacog['nodes'])} edges={len(metacog['edges'])}")
print(f"Knowledge nodes={len(knowledge['nodes'])} edges={len(knowledge['edges'])} b64_len={len(knowledge_b64)}")
print(f"Learning nodes={len(learning['nodes'])} edges={len(learning['edges'])}")
print("Done")
