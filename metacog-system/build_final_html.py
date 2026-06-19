"""FINAL HTML builder v3 — with robust encoding, no garbled text"""
import json, re, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(r"D:\ai项目\metacog-distiller")
SYS = ROOT / "metacog-system"

# ─── Read D3.js ───
D3JS = (SYS / "d3.v7.min.js").read_text(encoding="utf-8")

# ─── Encoding safeguard ───
def safe_str(s):
    """Strip control chars / replacement chars that break rendering"""
    if not s: return ""
    s = s.replace('\ufffd', '')
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', s)
    return s

def dfs(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))

# ─── Clean all data before embedding ───
def clean_data(data):
    for n in data['nodes']:
        for k in ('label','summary','wiki_description','baidu_description'):
            if k in n and n[k]:
                n[k] = safe_str(n[k])
    return data

# ─── Single build function ───
def build_html(filename, title, legend_html, node_css, edge_css, 
               type_labels, rel_labels, radius_map, link_dists, charge, collide, json_path):
    data = clean_data(json.loads((SYS / json_path).read_text(encoding="utf-8")))
    data_js = dfs(data)
    
    # Build note file map (label → filename) from note_graph if available
    note_file_map = {}
    note_graph_path = SYS / "note_graph.json"
    if note_graph_path.exists():
        try:
            ng = json.loads(note_graph_path.read_text(encoding="utf-8"))
            for n in ng.get("nodes", []):
                if n.get("file"):
                    note_file_map[n["id"]] = n["file"]
        except Exception:
            pass
    note_file_js = json.dumps(note_file_map, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<script>{D3JS}</script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;background:#0d1117;color:#c9d1d9;display:flex;height:100vh;overflow:hidden}}
#graph-panel{{flex:1;position:relative;background:radial-gradient(ellipse at center,#1a1d27 0%,#0d1117 70%)}}
#graph-panel svg{{width:100%;height:100%}}
.edge{{stroke-opacity:0.4;fill:none}}
{edge_css}
.node circle{{stroke-width:2px;cursor:pointer;transition:r 0.2s}}
{node_css}
.node text{{fill:#c9d1d9;font-size:12px;pointer-events:none;text-anchor:middle;font-family:"PingFang SC","Microsoft YaHei",sans-serif}}
.node.selected circle{{stroke:#f0f6fc;stroke-width:3px}}
#sidebar{{width:420px;background:#161b22;border-left:1px solid #30363d;display:flex;flex-direction:column;overflow-y:auto;flex-shrink:0;font-family:"PingFang SC","Microsoft YaHei",sans-serif}}
#sidebar-header{{padding:20px;border-bottom:1px solid #21262d}}
#sidebar-header h2{{font-size:16px;color:#f0f6fc}}
#sidebar-header .subtitle{{font-size:12px;color:#8b949e;margin-top:4px}}
#detail-content{{padding:20px;flex:1;white-space:pre-wrap;word-break:break-word}}
#detail-content .empty{{color:#484f58;font-size:14px;text-align:center;margin-top:100px}}
.detail-block{{margin-bottom:18px}}
.detail-block h3{{font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#8b949e;margin-bottom:6px}}
.detail-block p{{font-size:13px;line-height:1.7;color:#c9d1d9}}
.edge-mini{{font-size:12px;color:#8b949e;padding:3px 0;display:flex;align-items:center;gap:6px}}
.edge-mini .em-label{{color:#c9d1d9}}
.ext-desc{{font-size:12px;color:#8b949e;background:#0d1117;border:1px solid #21262d;border-radius:6px;padding:10px;margin-top:6px;line-height:1.6}}
.ext-desc .src{{color:#d2991d;font-weight:600;font-size:11px;margin-bottom:4px}}
#legend{{position:absolute;top:12px;left:12px;background:rgba(22,27,34,0.93);border:1px solid #30363d;border-radius:8px;padding:10px 14px;font-size:11px;pointer-events:none}}
#legend h3{{font-size:12px;margin-bottom:6px;color:#8b949e}}
.lr{{display:flex;align-items:center;margin:3px 0;gap:6px}}
.ld{{width:9px;height:9px;border-radius:50%;flex-shrink:0}}
.ll{{width:22px;height:2px;flex-shrink:0;border-radius:1px}}
#graph-tools{{position:absolute;bottom:12px;right:12px;display:flex;gap:6px}}
#graph-tools button{{background:rgba(22,27,34,0.93);border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:6px 12px;font-size:11px;cursor:pointer}}
#graph-tools button:hover{{background:#30363d}}
.nav-bar{{display:flex;gap:8px;align-items:center;margin-bottom:4px;font-size:12px}}
.nav-bar a{{color:#8b949e;text-decoration:none}}
.nav-bar a:hover{{color:#f0f6fc}}
.nav-bar .sep{{color:#30363d}}
.node.linked circle{{stroke:#f0f6fc;stroke-width:3px;stroke-opacity:0.9}}
.node.linked text{{font-weight:bold;fill:#f0f6fc}}
.edge.linked{{opacity:0.9;stroke-width:2.5;stroke:#58a6ff}}
</style></head>
<body>
<div id="graph-panel"><svg></svg>
<div id="legend">{legend_html}</div>
<div id="graph-tools"><button onclick="zI()">+</button><button onclick="zO()">-</button><button onclick="zR()">&#x21BA;</button></div></div>
<div id="sidebar"><div id="sidebar-header">
<div class="nav-bar"><a href="index.html">🏠</a><span class="sep">|</span><a href="knowledge-explorer.html">🌐</a><span class="sep">|</span><a href="note-editor.html">📝</a></div>
<h2>{title}</h2><div class="subtitle" id="stats">loading</div><input id="search-box" placeholder="&#x1F50D; 搜索节点..." style="width:100%;margin-top:8px;padding:6px 10px;border-radius:6px;border:1px solid #30363d;background:#0d1117;color:#c9d1d9;font-size:12px;outline:none;font-family:inherit" oninput="searchNodes(this.value)"></div>
<div id="detail-content"><div class="empty">&#x1F446; hover node to view details</div></div></div>
<script>
var svg=d3.select("svg"),g=svg.append("g");
var zoom=d3.zoom().scaleExtent([0.1,8]).on("zoom",function(e){{g.attr("transform",e.transform)}});svg.call(zoom);
var s,gn=[],ge=[];
var tl={dfs(type_labels)};
var rl={dfs(rel_labels)};
var cl={{certain:"certain",likely:"likely",speculative:"speculative"}};
function nr(d){{var m={dfs(radius_map)};return m[d.type]||10}}
function r(data){{
g.selectAll("*").remove();
gn=data.nodes.map(n=>Object.assign({{}},n));
ge=data.edges.map(e=>Object.assign({{}},e));
document.getElementById("stats").textContent=gn.length+" nodes · "+ge.length+" edges";
var lk=g.append("g").selectAll("line").data(ge).join("line").attr("class",d=>"edge "+(d.type||"influences")).attr("stroke-width",1.4);
var nd=g.append("g").selectAll("g").data(gn).join("g").attr("class",d=>"node "+(d.type||"domain")).call(d3.drag().on("start",(e,d)=>{{if(!e.active)s.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y}}).on("drag",(e,d)=>{{d.fx=e.x;d.fy=e.y}}).on("end",(e,d)=>{{if(!e.active)s.alphaTarget(0);d.fx=null;d.fy=null}})).on("mouseenter",function(e,d){{focusNode(d,nd,lk);sd(d)}});
nd.append("circle").attr("r",nr).on("mouseenter",function(e,d){{d3.select(this).transition().duration(150).attr("r",nr(d)+5)}}).on("mouseleave",function(e,d){{d3.select(this).transition().duration(150).attr("r",nr(d))}});
nd.append("text").text(d=>d.label).style("font-family",'"PingFang SC","Microsoft YaHei",sans-serif');
var W=document.getElementById("graph-panel").clientWidth,H=document.getElementById("graph-panel").clientHeight;
s=d3.forceSimulation(gn).force("link",d3.forceLink(ge).id(d=>d.id).distance(d=>{{var ds={dfs(link_dists)};return ds[d.type]||160}}).strength(0.3)).force("charge",d3.forceManyBody().strength({charge}).distanceMax(500)).force("center",d3.forceCenter(W/2,H/2)).force("collision",d3.forceCollide().radius(d=>nr(d)+{collide})).alphaDecay(0.08).on("tick",()=>{{lk.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);nd.attr("transform",d=>"translate("+d.x+","+d.y+")")}})}}
function focusNode(d,nd,lk){{
g.selectAll(".node").classed("linked",false);
g.selectAll(".edge").classed("linked",false);
// Find connected node IDs
var connected=new Set([d.id]);
ge.forEach(e=>{{var s=e.source.id||e.source;var t=e.target.id||e.target;if(s===d.id)connected.add(t);if(t===d.id)connected.add(s)}});
// Highlight connected nodes and edges (leave rest of graph fully visible)
nd.classed("linked",n=>connected.has(n.id)&&n.id!==d.id);
lk.classed("linked",e=>{{var s=e.source.id||e.source;var t=e.target.id||e.target;return s===d.id||t===d.id}});
}}
function sd(d){{
var el=document.getElementById("detail-content");
var rs=ge.filter(e=>(e.source.id||e.source)===d.id||(e.target.id||e.target)===d.id);
var h="";
h+='<div class="detail-block"><h3>'+tl[d.type]+' &middot; '+cl[d.confidence]+' &middot; depth '+d.depth+'</h3>';
h+='<p style="font-size:18px;font-weight:600;color:#f0f6fc;margin-bottom:6px;">'+d.label+'</p>';
if(d.summary)h+='<div class="detail-block"><h3>Description</h3><p>'+d.summary+'</p></div>';
if(d.wiki_description)h+='<div class="ext-desc"><div class="src">&#x1F4D6; Wikipedia</div>'+d.wiki_description+'</div>';
if(d.baidu_description)h+='<div class="ext-desc"><div class="src">&#x1F50D; Baidu</div>'+d.baidu_description+'</div>';
if(rs.length>0){{
var out=rs.filter(e=>(e.source.id||e.source)===d.id);
var inp=rs.filter(e=>(e.target.id||e.target)===d.id&&(e.source.id||e.source)!==d.id);
h+='<div class="detail-block"><h3>→ 向外链接 ('+out.length+')</h3>';
out.forEach(e=>{{var o=gn.find(n=>n.id===e.target.id);h+='<div class="edge-mini">→ <span class="em-label">'+(o?o.label:e.target.id)+'</span> <span style="color:#484f58">'+rl[e.type]+'</span></div>'}});
h+='</div>';
h+='<div class="detail-block"><h3>← 反向链接 ('+inp.length+')</h3>';
inp.forEach(e=>{{var o=gn.find(n=>n.id===e.source.id);h+='<div class="edge-mini">← <span class="em-label">'+(o?o.label:e.source.id)+'</span> <span style="color:#484f58">'+rl[e.type]+'</span></div>'}});
h+='</div>';
}}
el.innerHTML=h;}}
svg.on("click",()=>{{g.selectAll(".node").classed("linked",false);g.selectAll(".edge").classed("linked",false)}});
window.addEventListener("resize",()=>{{if(s){{var W=document.getElementById("graph-panel").clientWidth,H=document.getElementById("graph-panel").clientHeight;s.force("center",d3.forceCenter(W/2,H/2));s.alpha(0.3).restart()}}}});
function zI(){{svg.transition().duration(300).call(zoom.scaleBy,1.3)}}
function zO(){{svg.transition().duration(300).call(zoom.scaleBy,0.7)}}
function zR(){{svg.transition().duration(400).call(zoom.transform,d3.zoomIdentity)}}
var nfm = {note_file_js};
function searchNodes(q){{
q=q.toLowerCase();if(!q){{document.getElementById("detail-content").innerHTML='<div class="empty">&#x1F446; hover node to view details</div>';g.selectAll(".node").classed("linked",false);g.selectAll(".edge").classed("linked",false);return}}
var matches=gn.filter(n=>n.label.toLowerCase().includes(q)||(n.summary||'').toLowerCase().includes(q));
var h='<div class="detail-block"><h3>搜索结果 ('+matches.length+')</h3>';
matches.forEach(n=>{{
h+='<div style="padding:4px 0;border-bottom:1px solid #21262d;cursor:pointer" onclick="sd(gn.find(g=>g.id===\\''+n.id+'\\''))"><span style="color:#58a6ff">'+n.label+'</span><br><span style="font-size:11px;color:#8b949e">'+(n.summary||'').slice(0,80)+'</span></div>';
}});
h+='</div>';document.getElementById("detail-content").innerHTML=h;}}
var ed = {data_js};
if(ed.nodes&&ed.nodes.length>0){{r(ed)}}
</script></body></html>'''
    
    out = ROOT / filename
    out.write_text(html, encoding="utf-8")
    return len(html)

# ═══ BUILD ALL 3 ═══

META_LEGEND = '<h3>Node Types</h3><div class="lr"><span class="ld" style="background:#316dca"></span>Domain</div><div class="lr"><span class="ld" style="background:#9e6a03"></span>Belief</div><div class="lr"><span class="ld" style="background:#1f6f3b"></span>Decision</div><div class="lr"><span class="ld" style="background:#8b3a3a"></span>Bias</div><div class="lr"><span class="ld" style="background:#6e40c9"></span>Strategy</div><div class="lr"><span class="ld" style="background:#b0376b"></span>Emotion</div><div class="lr"><span class="ld" style="background:#4a2d7a"></span>Meta</div>'

m = build_html(
    "metacognition-mapper.html",
    "&#x1F9E0; Metacognition Mapper",
    META_LEGEND,
    '.node.domain circle{fill:#316dca;stroke:#58a6ff}\n.node.belief circle{fill:#9e6a03;stroke:#d2991d}\n.node.decision circle{fill:#1f6f3b;stroke:#3fb950}\n.node.bias circle{fill:#8b3a3a;stroke:#f85149}\n.node.strategy circle{fill:#6e40c9;stroke:#a371f7}\n.node.emotion circle{fill:#b0376b;stroke:#f778ba}\n.node.evidence circle{fill:#3b5e7a;stroke:#79c0ff}\n.node.source circle{fill:#6e4a2e;stroke:#c69052}\n.node.meta circle{fill:#4a2d7a;stroke:#bc8cff}',
    '.edge.supports{stroke:#3fb950}\n.edge.conflicts{stroke:#f85149}\n.edge.derives_from{stroke:#58a6ff}\n.edge.influences{stroke:#d2991d}\n.edge.avoids{stroke:#484f58;stroke-dasharray:4 3}\n.edge.corrects{stroke:#39d353;stroke-dasharray:6 2}\n.edge.questions{stroke:#bc8cff;stroke-dasharray:2 4}',
    {'domain':'Domain','belief':'Belief','decision':'Decision','bias':'Bias','strategy':'Strategy','emotion':'Emotion','evidence':'Evidence','source':'Source','meta':'Meta'},
    {'supports':'supports','conflicts':'conflicts','derives_from':'from','influences':'influences','avoids':'avoids','corrects':'corrects','questions':'questions'},
    {'domain':15,'belief':13,'decision':12,'bias':11,'strategy':10,'emotion':9,'evidence':9,'source':9,'meta':12},
    {'supports':130,'derives_from':150,'conflicts':200,'influences':170,'avoids':180,'corrects':140,'questions':160},
    '-600', '20', 'metacog_graph.json'
)
print(f"Meta: {m}B")

KNOW_LEGEND = '<h3>Knowledge Types</h3><div class="lr"><span class="ld" style="background:#1a5fb4"></span>Concept</div><div class="lr"><span class="ld" style="background:#1f6f3b"></span>Fact</div><div class="lr"><span class="ld" style="background:#935e00"></span>Tool</div><div class="lr"><span class="ld" style="background:#6a2b8a"></span>Resource</div><div class="lr"><span class="ld" style="background:#991b4e"></span>Insight</div><div class="lr"><span class="ld" style="background:#116b63"></span>Project</div><div class="lr"><span class="ld" style="background:#303fa0"></span>Skill</div>'

k = build_html(
    "knowledge-mapper.html",
    "&#x1F4DA; Knowledge Graph",
    KNOW_LEGEND,
    '.node.concept circle{fill:#1a5fb4;stroke:#3584e4}\n.node.fact circle{fill:#1f6f3b;stroke:#3fb950}\n.node.tool circle{fill:#935e00;stroke:#d2991d}\n.node.resource circle{fill:#6a2b8a;stroke:#a371f7}\n.node.insight circle{fill:#991b4e;stroke:#f778ba}\n.node.question circle{fill:#8b3a3a;stroke:#f85149}\n.node.project circle{fill:#116b63;stroke:#39d353}\n.node.skill circle{fill:#303fa0;stroke:#6e8fff}',
    '.edge.relates_to{stroke:#484f58;stroke-dasharray:4 3}\n.edge.depends_on{stroke:#f85149}\n.edge.part_of{stroke:#58a6ff;stroke-opacity:0.5}\n.edge.example_of{stroke:#3fb950}\n.edge.contrasts_with{stroke:#d2991d;stroke-dasharray:6 2}\n.edge.derives_from{stroke:#a371f7}\n.edge.used_in{stroke:#39d353}\n.edge.prerequisite{stroke:#d2991d}',
    {'concept':'Concept','fact':'Fact','tool':'Tool','resource':'Resource','insight':'Insight','question':'Question','project':'Project','skill':'Skill'},
    {'relates_to':'related','depends_on':'depends','part_of':'part of','example_of':'example','contrasts_with':'contrast','derives_from':'from','used_in':'used in','prerequisite':'prereq'},
    {'concept':15,'tool':13,'project':14,'skill':12,'insight':11,'fact':10,'resource':10,'question':9},
    {'part_of':120,'used_in':140,'depends_on':160,'prerequisite':160,'relates_to':200,'example_of':180,'contrasts_with':220,'derives_from':170},
    '-650', '22', 'knowledge_graph.json'
)
print(f"Know: {k}B")

LEARN_LEGEND = '<h3>Learning Status</h3><div class="lr"><span class="ld" style="background:#8b3a3a"></span>Asked</div><div class="lr"><span class="ld" style="background:#935e00"></span>Learning</div><div class="lr"><span class="ld" style="background:#30363d"></span>Todo</div><div class="lr"><span class="ld" style="background:#1f6f3b"></span>Learned</div><div class="lr"><span class="ld" style="background:#991b4e"></span>Question</div>'

l = build_html(
    "learning-mapper.html",
    "&#x1F4D6; Learning Mapper",
    LEARN_LEGEND,
    '.node.asked circle{fill:#8b3a3a;stroke:#f85149}\n.node.learning circle{fill:#935e00;stroke:#d2991d}\n.node.todo circle{fill:#30363d;stroke:#484f58}\n.node.learned circle{fill:#1f6f3b;stroke:#3fb950}\n.node.question circle{fill:#991b4e;stroke:#f778ba}\n.node.concept circle{fill:#1a5fb4;stroke:#3584e4}\n.node.fact circle{fill:#1f6f3b;stroke:#3fb950}\n.node.tool circle{fill:#935e00;stroke:#d2991d}\n.node.resource circle{fill:#6a2b8a;stroke:#a371f7}\n.node.insight circle{fill:#991b4e;stroke:#f778ba}\n.node.project circle{fill:#116b63;stroke:#39d353}\n.node.skill circle{fill:#303fa0;stroke:#6e8fff}',
    '.edge.relates_to{stroke:#484f58;stroke-dasharray:4 3}\n.edge.depends_on{stroke:#f85149}\n.edge.part_of{stroke:#58a6ff;stroke-opacity:0.5}\n.edge.example_of{stroke:#3fb950}\n.edge.contrasts_with{stroke:#d2991d;stroke-dasharray:6 2}\n.edge.derives_from{stroke:#a371f7}\n.edge.used_in{stroke:#39d353}\n.edge.prerequisite{stroke:#d2991d}\n.edge.questions{stroke:#f0883e;stroke-dasharray:3 3}',
    {'concept':'Concept','fact':'Fact','tool':'Tool','resource':'Resource','insight':'Insight','question':'Question','project':'Project','skill':'Skill'},
    {'relates_to':'related','depends_on':'depends','part_of':'part of','example_of':'example','contrasts_with':'contrast','derives_from':'from','used_in':'used in','prerequisite':'prereq','questions':'ask'},
    {'concept':15,'tool':13,'project':14,'skill':12,'insight':11,'fact':10,'resource':10,'question':14},
    {'part_of':120,'used_in':140,'depends_on':160,'prerequisite':160,'relates_to':200,'example_of':180,'contrasts_with':220,'derives_from':170,'questions':250},
    '-650', '22', 'learning_graph.json'
)
print(f"Learn: {l}B")
print("ALL THREE HTMLs REGENERATED with encoding safeguards")
