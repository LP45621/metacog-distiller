"""Add SVG arrow markers to all 4 HTML mappers and rebuild everything"""
import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = Path(r"D:\ai项目\metacog-distiller")
SYS = BASE / "metacog-system"
D3JS = (SYS / "d3.v7.min.js").read_text(encoding="utf-8")

# ─── SVG arrow markers for each edge type ───
def make_markers(edge_colors):
    """Generate SVG <defs> with marker elements for each edge type"""
    markers = '<defs>\n'
    for etype, color in edge_colors.items():
        markers += f'<marker id="arrow-{etype}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M 0 2 L 9 5 L 0 8 z" fill="{color}"/></marker>\n'
    markers += '</defs>\n'
    return markers

def make_arrow_legend(edge_colors, edge_meanings):
    """Generate arrow legend HTML"""
    items = []
    for etype, color in edge_colors.items():
        meaning = edge_meanings.get(etype, etype)
        items.append(f'<div class="lr"><svg width="28" height="14"><defs><marker id="la-{etype}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M 0 2 L 9 5 L 0 8 z" fill="{color}"/></marker></defs><line x1="2" y1="7" x2="24" y2="7" stroke="{color}" stroke-width="2" marker-end="url(#la-{etype})"/></svg> {meaning}</div>')
    return '\n'.join(items)

# ═══ BUILD FUNCTION ═══
def build_html(filename, title, legend_html, node_css, edge_css,
               type_labels, rel_labels, radius_map, link_dists, charge, collide, json_path,
               edge_colors, edge_meanings):
    data = json.loads((SYS / json_path).read_text(encoding="utf-8"))
    # safe_str
    import re
    for n in data['nodes']:
        for k in ('label','summary','wiki_description','baidu_description'):
            if k in n and n[k]:
                n[k] = n[k].replace('\ufffd','').replace('\x00','')
    data_js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    markers_svg = make_markers(edge_colors)
    arrow_legend = make_arrow_legend(edge_colors, edge_meanings)
    
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
.legend-section{{margin-top:10px}}
.lr{{display:flex;align-items:center;margin:3px 0;gap:6px}}
.ld{{width:9px;height:9px;border-radius:50%;flex-shrink:0}}
.ll{{width:22px;height:2px;flex-shrink:0;border-radius:1px}}
#graph-tools{{position:absolute;bottom:12px;right:12px;display:flex;gap:6px}}
#graph-tools button{{background:rgba(22,27,34,0.93);border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:6px 12px;font-size:11px;cursor:pointer}}
#graph-tools button:hover{{background:#30363d}}
</style></head>
<body>
<div id="graph-panel"><svg>{markers_svg}</svg>
<div id="legend">{legend_html}
<div class="legend-section"><h3>箭头含义</h3>
{arrow_legend}
</div>
</div>
<div id="graph-tools"><button onclick="zI()">+</button><button onclick="zO()">-</button><button onclick="zR()">&#x21BA;</button></div></div>
<div id="sidebar"><div id="sidebar-header"><h2>{title}</h2><div class="subtitle" id="stats">loading</div></div>
<div id="detail-content"><div class="empty">&#x1F446; hover node to view details</div></div></div>
<script>
var svg=d3.select("svg"),g=svg.append("g");
var zoom=d3.zoom().scaleExtent([0.1,8]).on("zoom",function(e){{g.attr("transform",e.transform)}});svg.call(zoom);
var s,gn=[],ge=[];
var tl={json.dumps(type_labels, ensure_ascii=False)};
var rl={json.dumps(rel_labels, ensure_ascii=False)};
var cl={{"certain":"certain","likely":"likely","speculative":"speculative"}};
function nr(d){{var m={json.dumps(radius_map, ensure_ascii=False)};return m[d.type]||10}}
function r(data){{
g.selectAll("*").remove();
gn=data.nodes.map(n=>Object.assign({{}},n));
ge=data.edges.map(e=>Object.assign({{}},e));
document.getElementById("stats").textContent=gn.length+" nodes · "+ge.length+" edges";
var lk=g.append("g").selectAll("line").data(ge).join("line").attr("class",d=>"edge "+(d.type||"influences")).attr("stroke-width",1.4).attr("marker-end",d=>"url(#arrow-"+(d.type||"influences")+")");
var nd=g.append("g").selectAll("g").data(gn).join("g").attr("class",d=>"node "+(d.type||"domain")).call(d3.drag().on("start",(e,d)=>{{if(!e.active)s.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y}}).on("drag",(e,d)=>{{d.fx=e.x;d.fy=e.y}}).on("end",(e,d)=>{{if(!e.active)s.alphaTarget(0);d.fx=null;d.fy=null}})).on("mouseenter",function(e,d){{g.selectAll(".node").classed("selected",false);d3.select(this).classed("selected",true);sd(d)}}).on("mouseleave",function(){{g.selectAll(".node").classed("selected",false);}});
nd.append("circle").attr("r",nr).on("mouseenter",function(e,d){{d3.select(this).transition().duration(150).attr("r",nr(d)+5)}}).on("mouseleave",function(e,d){{d3.select(this).transition().duration(150).attr("r",nr(d))}});
nd.append("text").text(d=>d.label).style("font-family",'"PingFang SC","Microsoft YaHei",sans-serif');
var W=document.getElementById("graph-panel").clientWidth,H=document.getElementById("graph-panel").clientHeight;
s=d3.forceSimulation(gn).force("link",d3.forceLink(ge).id(d=>d.id).distance(d=>{{var ds={json.dumps(link_dists, ensure_ascii=False)};return ds[d.type]||160}}).strength(0.4)).force("charge",d3.forceManyBody().strength({charge}).distanceMax(600)).force("center",d3.forceCenter(W/2,H/2)).force("collision",d3.forceCollide().radius(d=>nr(d)+{collide})).alphaDecay(0.015).on("tick",()=>{{lk.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);nd.attr("transform",d=>"translate("+d.x+","+d.y+")")}})}}
function sd(d){{
var el=document.getElementById("detail-content");
var rs=ge.filter(e=>(e.source.id||e.source)===d.id||(e.target.id||e.target)===d.id);
var h="";
h+='<div class="detail-block"><h3>'+tl[d.type]+' &middot; '+cl[d.confidence]+' &middot; depth '+d.depth+'</h3>';
h+='<p style="font-size:18px;font-weight:600;color:#f0f6fc;margin-bottom:6px;">'+d.label+'</p>';
if(d.summary)h+='<div class="detail-block"><h3>Description</h3><p>'+d.summary+'</p></div>';
if(d.wiki_description)h+='<div class="ext-desc"><div class="src">&#x1F4D6; Wikipedia</div>'+d.wiki_description+'</div>';
if(d.baidu_description)h+='<div class="ext-desc"><div class="src">&#x1F50D; Baidu</div>'+d.baidu_description+'</div>';
if(rs.length>0){{h+='<div class="detail-block"><h3>Links ('+rs.length+')</h3>';
rs.forEach(e=>{{var isSrc=(e.source.id||e.source)===d.id;var oid=isSrc?e.target.id:e.source.id;var o=gn.find(n=>n.id===oid);h+='<div class="edge-mini">'+(isSrc?">":"<")+' <span class="em-label">'+(o?o.label:oid)+'</span> <span style="color:#484f58">'+rl[e.type]+'</span></div>'}});h+='</div>'}}
el.innerHTML=h;}}
svg.on("click",()=>{{g.selectAll(".node").classed("selected",false);document.getElementById("detail-content").innerHTML='<div class="empty">&#x1F446; hover node</div>'}});
window.addEventListener("resize",()=>{{if(s){{var W=document.getElementById("graph-panel").clientWidth,H=document.getElementById("graph-panel").clientHeight;s.force("center",d3.forceCenter(W/2,H/2));s.alpha(0.3).restart()}}}});
function zI(){{svg.transition().duration(300).call(zoom.scaleBy,1.3)}}
function zO(){{svg.transition().duration(300).call(zoom.scaleBy,0.7)}}
function zR(){{svg.transition().duration(400).call(zoom.transform,d3.zoomIdentity)}}
var ed = {data_js};
if(ed.nodes&&ed.nodes.length>0){{r(ed)}}
</script></body></html>'''
    (BASE / filename).write_text(html, encoding="utf-8")
    return len(html)

# ═══ METACOGNITION ═══
META_EDGE_COLORS = {
    'supports':'#3fb950','conflicts':'#f85149','derives_from':'#58a6ff',
    'influences':'#d2991d','avoids':'#484f58','corrects':'#39d353','questions':'#bc8cff'
}
META_EDGE_MEANINGS = {
    'supports':'支持——A强化/支撑B','conflicts':'冲突——A与B矛盾',
    'derives_from':'来源——B源于A','influences':'影响——A单向影响B',
    'avoids':'回避——A刻意避开B','corrects':'纠正——A修正B的偏差',
    'questions':'质疑——A对B提出疑问'
}

m = build_html("metacognition-mapper.html", "&#x1F9E0; Metacognition",
    '<h3>Node Types</h3><div class="lr"><span class="ld" style="background:#316dca"></span>Domain</div><div class="lr"><span class="ld" style="background:#9e6a03"></span>Belief</div><div class="lr"><span class="ld" style="background:#1f6f3b"></span>Decision</div><div class="lr"><span class="ld" style="background:#8b3a3a"></span>Bias</div><div class="lr"><span class="ld" style="background:#6e40c9"></span>Strategy</div><div class="lr"><span class="ld" style="background:#b0376b"></span>Emotion</div><div class="lr"><span class="ld" style="background:#4a2d7a"></span>Meta</div>',
    '.node.domain circle{fill:#316dca;stroke:#58a6ff}\n.node.belief circle{fill:#9e6a03;stroke:#d2991d}\n.node.decision circle{fill:#1f6f3b;stroke:#3fb950}\n.node.bias circle{fill:#8b3a3a;stroke:#f85149}\n.node.strategy circle{fill:#6e40c9;stroke:#a371f7}\n.node.emotion circle{fill:#b0376b;stroke:#f778ba}\n.node.evidence circle{fill:#3b5e7a;stroke:#79c0ff}\n.node.source circle{fill:#6e4a2e;stroke:#c69052}\n.node.meta circle{fill:#4a2d7a;stroke:#bc8cff}',
    '.edge.supports{stroke:#3fb950}\n.edge.conflicts{stroke:#f85149}\n.edge.derives_from{stroke:#58a6ff}\n.edge.influences{stroke:#d2991d}\n.edge.avoids{stroke:#484f58;stroke-dasharray:4 3}\n.edge.corrects{stroke:#39d353;stroke-dasharray:6 2}\n.edge.questions{stroke:#bc8cff;stroke-dasharray:2 4}',
    {'domain':'Domain','belief':'Belief','decision':'Decision','bias':'Bias','strategy':'Strategy','emotion':'Emotion','evidence':'Evidence','source':'Source','meta':'Meta'},
    {'supports':'supports','conflicts':'conflicts','derives_from':'from','influences':'influences','avoids':'avoids','corrects':'corrects','questions':'questions'},
    {'domain':15,'belief':13,'decision':12,'bias':11,'strategy':10,'emotion':9,'evidence':9,'source':9,'meta':12},
    {'supports':130,'derives_from':150,'conflicts':200,'influences':170,'avoids':180,'corrects':140,'questions':160},
    '-600','20','metacog_graph.json',META_EDGE_COLORS,META_EDGE_MEANINGS)
print(f"Meta: {m}B")

# ═══ KNOWLEDGE ═══
KNOW_EDGE_COLORS = {
    'relates_to':'#484f58','depends_on':'#f85149','part_of':'#58a6ff',
    'example_of':'#3fb950','contrasts_with':'#d2991d','derives_from':'#a371f7',
    'used_in':'#39d353','prerequisite':'#d2991d'
}
KNOW_EDGE_MEANINGS = {
    'relates_to':'相关——一般关联','depends_on':'依赖——A依赖B',
    'part_of':'组成——A是B的一部分','example_of':'示例——A是B的实例',
    'contrasts_with':'对比——A与B形成对比','derives_from':'来源——B源于A',
    'used_in':'使用——A用于B','prerequisite':'前置——A是B的前置条件'
}

k = build_html("knowledge-mapper.html", "&#x1F4DA; Knowledge Graph",
    '<h3>Knowledge Types</h3><div class="lr"><span class="ld" style="background:#1a5fb4"></span>Concept</div><div class="lr"><span class="ld" style="background:#1f6f3b"></span>Fact</div><div class="lr"><span class="ld" style="background:#935e00"></span>Tool</div><div class="lr"><span class="ld" style="background:#6a2b8a"></span>Resource</div><div class="lr"><span class="ld" style="background:#991b4e"></span>Insight</div><div class="lr"><span class="ld" style="background:#116b63"></span>Project</div><div class="lr"><span class="ld" style="background:#303fa0"></span>Skill</div>',
    '.node.concept circle{fill:#1a5fb4;stroke:#3584e4}\n.node.fact circle{fill:#1f6f3b;stroke:#3fb950}\n.node.tool circle{fill:#935e00;stroke:#d2991d}\n.node.resource circle{fill:#6a2b8a;stroke:#a371f7}\n.node.insight circle{fill:#991b4e;stroke:#f778ba}\n.node.question circle{fill:#8b3a3a;stroke:#f85149}\n.node.project circle{fill:#116b63;stroke:#39d353}\n.node.skill circle{fill:#303fa0;stroke:#6e8fff}',
    '.edge.relates_to{stroke:#484f58;stroke-dasharray:4 3}\n.edge.depends_on{stroke:#f85149}\n.edge.part_of{stroke:#58a6ff;stroke-opacity:0.5}\n.edge.example_of{stroke:#3fb950}\n.edge.contrasts_with{stroke:#d2991d;stroke-dasharray:6 2}\n.edge.derives_from{stroke:#a371f7}\n.edge.used_in{stroke:#39d353}\n.edge.prerequisite{stroke:#d2991d}',
    {'concept':'Concept','fact':'Fact','tool':'Tool','resource':'Resource','insight':'Insight','question':'Question','project':'Project','skill':'Skill'},
    {'relates_to':'related','depends_on':'depends','part_of':'part of','example_of':'example','contrasts_with':'contrast','derives_from':'from','used_in':'used in','prerequisite':'prereq'},
    {'concept':15,'tool':13,'project':14,'skill':12,'insight':11,'fact':10,'resource':10,'question':9},
    {'part_of':120,'used_in':140,'depends_on':160,'prerequisite':160,'relates_to':200,'example_of':180,'contrasts_with':220,'derives_from':170},
    '-650','22','knowledge_graph.json',KNOW_EDGE_COLORS,KNOW_EDGE_MEANINGS)
print(f"Know: {k}B")

# ═══ LEARNING ═══
LEARN_EDGE_COLORS = {
    'relates_to':'#484f58','depends_on':'#f85149','part_of':'#58a6ff',
    'example_of':'#3fb950','contrasts_with':'#d2991d','derives_from':'#a371f7',
    'used_in':'#39d353','prerequisite':'#d2991d','questions':'#f0883e'
}
LEARN_EDGE_MEANINGS = {
    'questions':'提问——用户对此有疑问','relates_to':'相关——一般关联',
    'depends_on':'依赖——A依赖B','part_of':'组成——A是B的一部分',
    'prerequisite':'前置——A是B的前置','contrasts_with':'对比——A与B对比',
    'derives_from':'来源——B源于A','used_in':'使用——A用于B'
}

l = build_html("learning-mapper.html", "&#x1F4D6; Learning Mapper",
    '<h3>Learning Status</h3><div class="lr"><span class="ld" style="background:#8b3a3a"></span>Asked</div><div class="lr"><span class="ld" style="background:#935e00"></span>Learning</div><div class="lr"><span class="ld" style="background:#30363d"></span>Todo</div><div class="lr"><span class="ld" style="background:#1f6f3b"></span>Learned</div><div class="lr"><span class="ld" style="background:#991b4e"></span>Question</div>',
    '.node.asked circle{fill:#8b3a3a;stroke:#f85149}\n.node.learning circle{fill:#935e00;stroke:#d2991d}\n.node.todo circle{fill:#30363d;stroke:#484f58}\n.node.learned circle{fill:#1f6f3b;stroke:#3fb950}\n.node.question circle{fill:#991b4e;stroke:#f778ba}\n.node.concept circle{fill:#1a5fb4;stroke:#3584e4}\n.node.fact circle{fill:#1f6f3b;stroke:#3fb950}\n.node.tool circle{fill:#935e00;stroke:#d2991d}\n.node.resource circle{fill:#6a2b8a;stroke:#a371f7}\n.node.insight circle{fill:#991b4e;stroke:#f778ba}\n.node.project circle{fill:#116b63;stroke:#39d353}\n.node.skill circle{fill:#303fa0;stroke:#6e8fff}',
    '.edge.relates_to{stroke:#484f58;stroke-dasharray:4 3}\n.edge.depends_on{stroke:#f85149}\n.edge.part_of{stroke:#58a6ff;stroke-opacity:0.5}\n.edge.example_of{stroke:#3fb950}\n.edge.contrasts_with{stroke:#d2991d;stroke-dasharray:6 2}\n.edge.derives_from{stroke:#a371f7}\n.edge.used_in{stroke:#39d353}\n.edge.prerequisite{stroke:#d2991d}\n.edge.questions{stroke:#f0883e;stroke-dasharray:3 3}',
    {'concept':'Concept','fact':'Fact','tool':'Tool','resource':'Resource','insight':'Insight','question':'Question','project':'Project','skill':'Skill'},
    {'relates_to':'related','depends_on':'depends','part_of':'part of','example_of':'example','contrasts_with':'contrast','derives_from':'from','used_in':'used in','prerequisite':'prereq','questions':'ask'},
    {'concept':15,'tool':13,'project':14,'skill':12,'insight':11,'fact':10,'resource':10,'question':14},
    {'part_of':120,'used_in':140,'depends_on':160,'prerequisite':160,'relates_to':200,'example_of':180,'contrasts_with':220,'derives_from':170,'questions':250},
    '-650','22','learning_graph.json',LEARN_EDGE_COLORS,LEARN_EDGE_MEANINGS)
print(f"Learn: {l}B")

# ═══ AI CAPABILITY ═══
ai = json.loads((SYS / "ai_capability_graph.json").read_text(encoding="utf-8"))
ai_js = json.dumps(ai, ensure_ascii=False, separators=(',',':'))
AI_EDGE_COLORS = {'part_of':'#58a6ff','depends_on':'#f0883e','supports':'#3fb950','used_in':'#39d353','relates_to':'#484f58','influences':'#d2991d','derives_from':'#a371f7','prerequisite':'#d2991d'}
AI_EDGE_MEANINGS = {'part_of':'组成——A是B的组件','depends_on':'依赖——A依赖B','supports':'支持——A增强B','used_in':'用于——A应用于B','relates_to':'相关','influences':'影响','derives_from':'来源','prerequisite':'前置'}
ai_markers = make_markers(AI_EDGE_COLORS)
ai_legend = make_arrow_legend(AI_EDGE_COLORS, AI_EDGE_MEANINGS)

ai_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI 能力图谱</title>
<script>{D3JS}</script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;background:#0d1117;color:#c9d1d9;display:flex;height:100vh;overflow:hidden}}
#graph-panel{{flex:1;position:relative;background:radial-gradient(ellipse at center,#1a1d27 0%,#0d1117 70%)}}
#graph-panel svg{{width:100%;height:100%}}
.edge{{stroke-opacity:0.4;fill:none}}
.edge.part_of{{stroke:#58a6ff;stroke-opacity:0.5}}
.edge.depends_on{{stroke:#f0883e}}
.edge.supports{{stroke:#3fb950}}
.edge.used_in{{stroke:#39d353}}
.edge.relates_to{{stroke:#484f58;stroke-dasharray:4 3}}
.edge.influences{{stroke:#d2991d}}
.edge.derives_from{{stroke:#a371f7}}
.edge.prerequisite{{stroke:#d2991d}}
.edge.example_of{{stroke:#3fb950}}
.edge.contrasts_with{{stroke:#d2991d;stroke-dasharray:6 2}}
.node circle{{stroke-width:2.5px;cursor:pointer;transition:r 0.2s}}
.node.tool circle{{fill:#e65100;stroke:#ff9800}}
.node.concept circle{{fill:#1565c0;stroke:#42a5f5}}
.node.skill circle{{fill:#00695c;stroke:#26a69a}}
.node text{{fill:#e0e0e0;font-size:12px;pointer-events:none;text-anchor:middle;font-family:"PingFang SC","Microsoft YaHei",sans-serif}}
.node.selected circle{{stroke:#ffffff;stroke-width:3px}}
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
.ext-desc .src{{color:#ff9800;font-weight:600;font-size:11px;margin-bottom:4px}}
#legend{{position:absolute;top:12px;left:12px;background:rgba(22,27,34,0.93);border:1px solid #30363d;border-radius:8px;padding:10px 14px;font-size:11px;pointer-events:none}}
#legend h3{{font-size:12px;margin-bottom:6px;color:#8b949e}}
.legend-section{{margin-top:10px}}
.lr{{display:flex;align-items:center;margin:3px 0;gap:6px}}
.ld{{width:9px;height:9px;border-radius:50%;flex-shrink:0}}
#graph-tools{{position:absolute;bottom:12px;right:12px;display:flex;gap:6px}}
#graph-tools button{{background:rgba(22,27,34,0.93);border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:6px 12px;font-size:11px;cursor:pointer}}
#graph-tools button:hover{{background:#30363d}}
</style></head>
<body>
<div id="graph-panel"><svg>{ai_markers}</svg>
<div id="legend">
<h3>AI 能力类型</h3>
<div class="lr"><span class="ld" style="background:#e65100"></span>AI 工具</div>
<div class="lr"><span class="ld" style="background:#1565c0"></span>AI 概念</div>
<div class="lr"><span class="ld" style="background:#00695c"></span>AI 技能</div>
<div class="legend-section"><h3>箭头含义</h3>
{ai_legend}
</div>
</div>
<div id="graph-tools"><button onclick="zI()">+</button><button onclick="zO()">-</button><button onclick="zR()">&#x21BA;</button></div></div>
<div id="sidebar"><div id="sidebar-header"><h2>&#x1F916; AI 能力图谱</h2><div class="subtitle" id="stats">loading</div></div>
<div id="detail-content"><div class="empty">&#x1F446; hover node to view details</div></div></div>
<script>
var svg=d3.select("svg"),g=svg.append("g");
var zoom=d3.zoom().scaleExtent([0.1,8]).on("zoom",function(e){{g.attr("transform",e.transform)}});svg.call(zoom);
var s,gn=[],ge=[];
var tl={{"concept":"AI概念","tool":"AI工具","skill":"AI技能"}};
var rl={{"part_of":"组成","depends_on":"依赖","supports":"支持","used_in":"用于","relates_to":"相关","influences":"影响","derives_from":"来源","prerequisite":"前置"}};
var cl={{"certain":"确信","likely":"可能","speculative":"推测"}};
function nr(d){{var m={{"concept":16,"tool":15,"skill":13}};return m[d.type]||12}}
function r(data){{
g.selectAll("*").remove();
gn=data.nodes.map(n=>Object.assign({{}},n));
ge=data.edges.map(e=>Object.assign({{}},e));
document.getElementById("stats").textContent=gn.length+" AI nodes · "+ge.length+" links";
var lk=g.append("g").selectAll("line").data(ge).join("line").attr("class",d=>"edge "+(d.type||"relates_to")).attr("stroke-width",1.8).attr("marker-end",d=>"url(#arrow-"+(d.type||"relates_to")+")");
var nd=g.append("g").selectAll("g").data(gn).join("g").attr("class",d=>"node "+(d.type||"concept")).call(d3.drag().on("start",(e,d)=>{{if(!e.active)s.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y}}).on("drag",(e,d)=>{{d.fx=e.x;d.fy=e.y}}).on("end",(e,d)=>{{if(!e.active)s.alphaTarget(0);d.fx=null;d.fy=null}})).on("mouseenter",function(e,d){{g.selectAll(".node").classed("selected",false);d3.select(this).classed("selected",true);sd(d)}}).on("mouseleave",function(){{g.selectAll(".node").classed("selected",false);}});
nd.append("circle").attr("r",nr).on("mouseenter",function(e,d){{d3.select(this).transition().duration(150).attr("r",nr(d)+5)}}).on("mouseleave",function(e,d){{d3.select(this).transition().duration(150).attr("r",nr(d))}});
nd.append("text").text(d=>d.label).style("font-family",'"PingFang SC","Microsoft YaHei",sans-serif');
var W=document.getElementById("graph-panel").clientWidth,H=document.getElementById("graph-panel").clientHeight;
s=d3.forceSimulation(gn).force("link",d3.forceLink(ge).id(d=>d.id).distance(180).strength(0.3)).force("charge",d3.forceManyBody().strength(-500).distanceMax(600)).force("center",d3.forceCenter(W/2,H/2)).force("collision",d3.forceCollide().radius(d=>nr(d)+18)).alphaDecay(0.015).on("tick",()=>{{lk.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);nd.attr("transform",d=>"translate("+d.x+","+d.y+")")}})}}
function sd(d){{
var el=document.getElementById("detail-content");
var rs=ge.filter(e=>(e.source.id||e.source)===d.id||(e.target.id||e.target)===d.id);
var h="";
h+='<div class="detail-block"><h3>'+tl[d.type]+' &middot; '+cl[d.confidence]+'</h3>';
h+='<p style="font-size:18px;font-weight:600;color:#f0f6fc;margin-bottom:6px;">'+d.label+'</p>';
if(d.summary)h+='<div class="detail-block"><h3>Description</h3><p>'+d.summary+'</p></div>';
if(d.wiki_description)h+='<div class="ext-desc"><div class="src">Wikipedia</div>'+d.wiki_description+'</div>';
if(d.baidu_description)h+='<div class="ext-desc"><div class="src">Baidu</div>'+d.baidu_description+'</div>';
if(rs.length>0){{h+='<div class="detail-block"><h3>Links ('+rs.length+')</h3>';
rs.forEach(e=>{{var isSrc=(e.source.id||e.source)===d.id;var oid=isSrc?e.target.id:e.source.id;var o=gn.find(n=>n.id===oid);h+='<div class="edge-mini">'+(isSrc?">":"<")+' <span class="em-label">'+(o?o.label:oid)+'</span> <span style="color:#484f58">'+rl[e.type]+'</span></div>'}});h+='</div>'}}
el.innerHTML=h;}}
svg.on("click",()=>{{g.selectAll(".node").classed("selected",false);document.getElementById("detail-content").innerHTML='<div class="empty">&#x1F446; hover node</div>'}});
window.addEventListener("resize",()=>{{if(s){{var W=document.getElementById("graph-panel").clientWidth,H=document.getElementById("graph-panel").clientHeight;s.force("center",d3.forceCenter(W/2,H/2));s.alpha(0.3).restart()}}}});
function zI(){{svg.transition().duration(300).call(zoom.scaleBy,1.3)}}
function zO(){{svg.transition().duration(300).call(zoom.scaleBy,0.7)}}
function zR(){{svg.transition().duration(400).call(zoom.transform,d3.zoomIdentity)}}
var ed = {ai_js};
if(ed.nodes&&ed.nodes.length>0){{r(ed)}}
</script></body></html>'''

(BASE / "ai-capability-mapper.html").write_text(ai_html, encoding="utf-8")
print(f"AI: {len(ai_html)}B")
print("\nALL 4 HTMLs REGENERATED with arrow markers + legend")
