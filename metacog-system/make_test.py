import json
from pathlib import Path

ROOT = Path(r"D:\ai项目\metacog-distiller")
SYS = ROOT / "metacog-system"

# Load data
know = json.loads((SYS / "knowledge_graph.json").read_text(encoding="utf-8"))
know_json = json.dumps(know, ensure_ascii=False)

# Load D3.js
d3js = (SYS / "d3.v7.min.js").read_text(encoding="utf-8")

# Generate minimal test HTML
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Knowledge Test</title>
<script>{d3js}</script>
<style>
body{{margin:0;background:#111;overflow:hidden}}
svg{{width:100vw;height:100vh}}
.node circle{{stroke-width:2px}}
.node text{{fill:#ccc;font-size:11px;text-anchor:middle}}
.link{{stroke:#555;stroke-opacity:0.4;fill:none}}
#info{{position:fixed;top:10px;left:10px;color:#8af;font-size:13px}}
</style>
</head>
<body>
<div id="info"></div>
<svg id="graph"></svg>
<script>
var data = {know_json};
document.getElementById("info").textContent = "Nodes: " + data.nodes.length;

var svg = d3.select("#graph"),
    W = window.innerWidth, H = window.innerHeight;

var g = svg.append("g");

var sim = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.edges).id(d => d.id).distance(100))
  .force("charge", d3.forceManyBody().strength(-300))
  .force("center", d3.forceCenter(W/2, H/2))
  .force("collision", d3.forceCollide().radius(15));

var link = g.selectAll("line").data(data.edges).join("line")
  .attr("class", "link");

var node = g.selectAll("g").data(data.nodes).join("g")
  .attr("class", d => "node " + d.type)
  .call(d3.drag()
    .on("start", (e,d) => {{ if(!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
    .on("drag", (e,d) => {{ d.fx = e.x; d.fy = e.y; }})
    .on("end", (e,d) => {{ if(!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }}));

node.append("circle").attr("r", 8).attr("fill", d => {{
  var c = {{concept:"#3584e4", tool:"#d2991d", project:"#39d353", skill:"#6e8fff", insight:"#f778ba", fact:"#3fb950", resource:"#a371f7", question:"#f85149"}};
  return c[d.type] || "#666";
}});

node.append("text").text(d => d.label).attr("dy", 22);

sim.on("tick", () => {{
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});

var zoom = d3.zoom().scaleExtent([0.1,8]).on("zoom", e => g.attr("transform", e.transform));
svg.call(zoom);
</script>
</body>
</html>'''

outpath = ROOT / "test.html"
outpath.write_text(html, encoding="utf-8")
print(f"Test HTML created: {outpath} ({len(html)} bytes)")
print(f"D3.js inlined: {len(d3js)} bytes")
print(f"Data nodes: {len(know['nodes'])}")
