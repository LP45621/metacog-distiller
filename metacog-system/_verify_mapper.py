import json, re

# Read HTML
with open("metacognition-mapper.html", "r", encoding="utf-8") as f:
    content = f.read()

# Extract var ed JSON
match = re.search(r'var ed = ({.*?});', content, re.DOTALL)
if match:
    json_str = match.group(1)
    data = json.loads(json_str)
    print(f"VALID: {len(data['nodes'])} nodes, {len(data['edges'])} edges")
    print(f"total_distillations: {data['total_distillations']}")
    print(f"last_distilled: {data['last_distilled']}")
    print(f"created: {data['created']}")
    print(f"user_id: {data['user_id']}")
else:
    print("ERROR: Could not find var ed assignment")
    exit(1)

# Verify against source
with open("metacog_graph.json", "r", encoding="utf-8") as f:
    orig = json.load(f)

# Compare
if data == orig:
    print("MATCH: HTML embedded JSON exactly matches metacog_graph.json")
else:
    print("MISMATCH!")
    # Show differences
    for k in orig:
        if data.get(k) != orig[k]:
            print(f"  Key '{k}' differs")
    exit(1)
