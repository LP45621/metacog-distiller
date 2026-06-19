#!/usr/bin/env python3
"""build_all.py — Unified builder: note graph + 4 mappers + update build_final_html.
   Run this to rebuild everything after adding/changing notes."""
import json
import subprocess
import sys
from pathlib import Path

SYS = Path(__file__).resolve().parent
ROOT = SYS.parent

print("=" * 55)
print("  🏗️  Metacog Distiller — Unified Builder")
print("=" * 55)

# Step 1: Note graph pipeline
print("\n[1/4] Scanning atomic notes...")
result = subprocess.run(
    [sys.executable, "-X", "utf8", str(SYS / "note_graph.py")],
    capture_output=True, text=True, timeout=60
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:300])

# Step 2: Build existing HTML mappers (metacognition, knowledge, learning)
print("[2/4] Building graph mappers...")
result = subprocess.run(
    [sys.executable, "-X", "utf8", str(SYS / "build_final_html.py")],
    capture_output=True, text=True, timeout=120
)
print(result.stdout.strip())
if result.stderr:
    print("STDERR:", result.stderr[:300])

# Step 3: Generate summary
print("[3/4] Generating analysis report...")
result = subprocess.run(
    [sys.executable, "-X", "utf8", str(SYS / "analyze.py")],
    capture_output=True, text=True, timeout=60
)
print(result.stdout.strip()[:300])

# Step 4: Verification
print("[4/4] Verification...")
note_graph = json.loads((SYS / "note_graph.json").read_text(encoding="utf-8"))
check_files = [
    ROOT / "knowledge-explorer.html",
    ROOT / "metacognition-mapper.html",
    ROOT / "knowledge-mapper.html",
    ROOT / "learning-mapper.html",
]
for f in check_files:
    status = "✅" if f.exists() else "❌"
    size = f.stat().st_size if f.exists() else 0
    print(f"  {status} {f.name} ({size//1024}KB)")

print(f"\n📊 Notes: {len(note_graph['nodes'])} · Edges: {len(note_graph['edges'])}")
print("✅ All builds complete.")
