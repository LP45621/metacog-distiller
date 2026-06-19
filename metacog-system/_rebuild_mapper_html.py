import json

# Read original JSON
with open("metacog_graph.json", "r", encoding="utf-8") as f:
    orig = json.load(f)

# Minify
mini = json.dumps(orig, ensure_ascii=False, separators=(",", ":"))

# Read HTML
with open("metacognition-mapper.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Replace line 45 (0-indexed: 44) with new var ed line
prefix = lines[:44]  # lines 1-44 (0-indexed: 0-43)
suffix = lines[45:]  # lines 46-63 (0-indexed: 45-62)

ed_line = "var ed = " + mini + ";\n"

# Reconstruct
out = "".join(prefix) + ed_line + "".join(suffix)

# Write back
with open("metacognition-mapper.html", "w", encoding="utf-8") as f:
    f.write(out)

print(f"Done: {len(out)} bytes, line 45 is {len(ed_line)} chars")
print(f"Nodes: {len(orig['nodes'])}, Edges: {len(orig['edges'])}")
