"""FINAL HTML builder — reads JSON, writes clean HTML from scratch every time."""
import json
from pathlib import Path

ROOT = Path(r"D:\ai项目\metacog-distiller")
SYS = ROOT / "metacog-system"

TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{TITLE}</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#0d1117;color:#c9d1d9;display:flex;height:100vh;overflow:hidden}}
#graph-panel{{flex:1;position:relative;background:radial-gradient(ellipse at center,#1a1d27 0%,#0d1117 70%)}}
#graph-panel svg{{width:100%;height:100%}}
.edge{{stroke-opacity:0.4;fill:none}}
{EDGE_CSS}
.node circle{{stroke-width:2px;cursor:pointer;transition:r 0.2s}}
{NODE_CSS}
.node text{{fill:#c9d1d9;font-size:12px;pointer-events:none;text-anchor:middle}}
.node.selected circle{{stroke:#f0f6fc;stroke-width:3px}}
#sidebar{{width:420px;background:#161b22;border-left:1px solid #30363d;display:flex;flex-direction:column;overflow-y:auto;flex-shrink:0}}
#sidebar-header{{padding:20px;border-bottom:1px solid #21262d}}
#sidebar-header h2{{font-size:16px;color:#f0f6fc}}
#sidebar-header .subtitle{{font-size:12px;color:#8b949e;margin-top:4px}}
#detail-content{{padding:20px;flex:1}}
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
</style></head>
<body>
<div id="graph-panel"><svg></svg>
<div id="legend">{LEGEND}</div>
<div id="graph-tools"><button onclick="zI()">+</button><button onclick="zO()">-</button><button onclick="zR()">&#x21BA;</button></div></div>
<div id="sidebar"><div id="sidebar-header"><h2>{SIDEBAR_TITLE}</h2><div class="subtitle" id="stats">加载中...</div></div>
<div id="detail-content"><div class="empty">&#x1F446; 点击节点查看详细描述</div></div></div>
<script>
{JS_CODE}
var ed = {DATA};
if(ed.nodes&&ed.nodes.length>0){{r(ed)}}
</script></body></html>'''

META_LEGEND = '<h3>节点类型</h3><div class="lr"><span class="ld" style="background:#316dca"></span>领域</div><div class="lr"><span class="ld" style="background:#9e6a03"></span>信念</div><div class="lr"><span class="ld" style="background:#1f6f3b"></span>决策</div><div class="lr"><span class="ld" style="background:#8b3a3a"></span>偏差</div><div class="lr"><span class="ld" style="background:#6e40c9"></span>策略</div><div class="lr"><span class="ld" style="background:#b0376b"></span>情绪</div><div class="lr"><span class="ld" style="background:#4a2d7a"></span>元认知</div><h3 style="margin-top:10px">关系</h3><div class="lr"><span class="ll" style="background:#3fb950"></span>支持</div><div class="lr"><span class="ll" style="background:#f85149"></span>冲突</div><div class="lr"><span class="ll" style="background:#58a6ff"></span>来源</div><div class="lr"><span class="ll" style="background:#d2991d"></span>影响</div>'
KNOW_LEGEND = '<h3>知识类型</h3><div class="lr"><span class="ld" style="background:#1a5fb4"></span>概念</div><div class="lr"><span class="ld" style="background:#1f6f3b"></span>事实</div><div class="lr"><span class="ld" style="background:#935e00"></span>工具</div><div class="lr"><span class="ld" style="background:#6a2b8a"></span>资源</div><div class="lr"><span class="ld" style="background:#991b4e"></span>洞见</div><div class="lr"><span class="ld" style="background:#116b63"></span>项目</div><div class="lr"><span class="ld" style="background:#303fa0"></span>技能</div>'
LEARN_LEGEND = '<h3>学习状态</h3><div class="lr"><span class="ld" style="background:#8b3a3a"></span>多次提问</div><div class="lr"><span class="ld" style="background:#935e00"></span>学习中</div><div class="lr"><span class="ld" style="background:#30363d"></span>待学习</div><div class="lr"><span class="ld" style="background:#1f6f3b"></span>已掌握</div><div class="lr"><span class="ld" style="background:#991b4e"></span>疑问</div>'

JS = '''var svg=d3.select("svg"),g=svg.append("g");
var zoom=d3.zoom().scaleExtent([0.1,8]).on("zoom",function(e){g.attr("transform",e.transform)});svg.call(zoom);
var s,gn=[],ge=[];
var tl={TL};
var rl={RL};
var cl={certain:"确信",likely:"可能",speculative:"推测"};
function nr(d){var m={RADII};return m[d.type]||10}
function r(data){
g.selectAll("*").remove();
gn=data.nodes.map(function(n){return Object.assign({},n)});
ge=data.edges.map(function(e){return Object.assign({},e)});
document.getElementById("stats").textContent="节点 "+gn.length+" · 连线 "+ge.length;
var lk=g.append("g").selectAll("line").data(ge).join("line").attr("class",function(d){return"edge "+(d.type||"influences")}).attr("stroke-width",1.4);
var nd=g.append("g").selectAll("g").data(gn).join("g").attr("class",function(d){return"node "+(d.type||"domain")}).call(d3.drag().on("start",function(e,d){if(!e.active)s.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y}).on("drag",function(e,d){d.fx=e.x;d.fy=e.y}).on("end",function(e,d){if(!e.active)s.alphaTarget(0);d.fx=null;d.fy=null})).on("click",function(e,d){e.stopPropagation();g.selectAll(".node").classed("selected",false);d3.select(this).classed("selected",true);sd(d)});
nd.append("circle").attr("r",nr).on("mouseenter",function(e,d){d3.select(this).transition().duration(150).attr("r",nr(d)+5)}).on("mouseleave",function(e,d){d3.select(this).transition().duration(150).attr("r",nr(d))});
nd.append("text").text(function(d){return d.label});
var W=document.getElementById("graph-panel").clientWidth,H=document.getElementById("graph-panel").clientHeight;
s=d3.forceSimulation(gn).force("link",d3.forceLink(ge).id(function(d){return d.id}).distance(function(d){var ds={LINK_DISTS};return ds[d.type]||160}).strength(0.4)).force("charge",d3.forceManyBody().strength({CHARGE}).distanceMax(600)).force("center",d3.forceCenter(W/2,H/2)).force("collision",d3.forceCollide().radius(function(d){return nr(d)+{COLLIDE}})).alphaDecay(0.015).on("tick",function(){lk.attr("x1",function(d){return d.source.x}).attr("y1",function(d){return d.source.y}).attr("x2",function(d){return d.target.x}).attr("y2",function(d){return d.target.y});nd.attr("transform",function(d){return"translate("+d.x+","+d.y+")"})})}
function sd(d){
var el=document.getElementById("detail-content");
var rs=ge.filter(function(e){return(e.source.id||e.source)===d.id||(e.target.id||e.target)===d.id});
var h="";
h+='<div class="detail-block"><h3>'+tl[d.type]+' · '+cl[d.confidence]+' · 深度'+d.depth+'</h3>';
h+='<p style="font-size:18px;font-weight:600;color:#f0f6fc;margin-bottom:6px;">'+d.label+'</p>';
if(d.summary)h+='<div class="detail-block"><h3>详细描述</h3><p>'+d.summary+'</p></div>';
if(d.wiki_description)h+='<div class="ext-desc"><div class="src">&#x1F4D6; Wikipedia</div>'+d.wiki_description+'</div>';
if(d.baidu_description)h+='<div class="ext-desc"><div class="src">&#x1F50D; Baidu</div>'+d.baidu_description+'</div>';
if(rs.length>0){h+='<div class="detail-block"><h3>关联 ('+rs.length+')</h3>';
for(var i=0;i<rs.length;i++){var e=rs[i];var isSrc=(e.source.id||e.source)===d.id;var oid=isSrc?e.target.id:e.source.id;var o=gn.find(function(n){return n.id===oid});h+='<div class="edge-mini">'+(isSrc?"→":"←")+' <span class="em-label">'+(o?o.label:oid)+'</span> <span style="color:#484f58">'+rl[e.type]+'</span></div>'}h+='</div>'}
el.innerHTML=h;}
svg.on("click",function(){g.selectAll(".node").classed("selected",false);document.getElementById("detail-content").innerHTML='<div class="empty">&#x1F446; 点击节点查看详细描述</div>'});
window.addEventListener("resize",function(){if(s){var W=document.getElementById("graph-panel").clientWidth,H=document.getElementById("graph-panel").clientHeight;s.force("center",d3.forceCenter(W/2,H/2));s.alpha(0.3).restart()}});
function zI(){svg.transition().duration(300).call(zoom.scaleBy,1.3)}
function zO(){svg.transition().duration(300).call(zoom.scaleBy,0.7)}
function zR(){svg.transition().duration(400).call(zoom.transform,d3.zoomIdentity)}'''

def build_meta():
    data = json.loads((SYS / "metacog_graph.json").read_text(encoding="utf-8"))
    js = JS.replace("{TL}", 'domain:"领域",belief:"信念",decision:"决策",bias:"偏差",strategy:"策略",emotion:"情绪",evidence:"证据",source:"来源",meta:"元认知"')
    js = js.replace("{RL}", 'supports:"支持",conflicts:"冲突",derives_from:"来源",influences:"影响",avoids:"回避",corrects:"纠正",questions:"质疑"')
    js = js.replace("{RADII}", 'domain:15,belief:13,decision:12,bias:11,strategy:10,emotion:9,evidence:9,source:9,meta:12')
    js = js.replace("{LINK_DISTS}", 'supports:130,derives_from:150,conflicts:200,influences:170,avoids:180,corrects:140,questions:160')
    js = js.replace("{CHARGE}", '-600')
    js = js.replace("{COLLIDE}", '20')
    # Edge CSS
    edge_css = '.edge.supports{stroke:#3fb950}.edge.conflicts{stroke:#f85149}.edge.derives_from{stroke:#58a6ff}\n.edge.influences{stroke:#d2991d}.edge.avoids{stroke:#484f58;stroke-dasharray:4 3}\n.edge.corrects{stroke:#39d353;stroke-dasharray:6 2}.edge.questions{stroke:#bc8cff;stroke-dasharray:2 4}'
    node_css = '.node.domain circle{fill:#316dca;stroke:#58a6ff}.node.belief circle{fill:#9e6a03;stroke:#d2991d}\n.node.decision circle{fill:#1f6f3b;stroke:#3fb950}.node.bias circle{fill:#8b3a3a;stroke:#f85149}\n.node.strategy circle{fill:#6e40c9;stroke:#a371f7}.node.emotion circle{fill:#b0376b;stroke:#f778ba}\n.node.evidence circle{fill:#3b5e7a;stroke:#79c0ff}.node.source circle{fill:#6e4a2e;stroke:#c69052}\n.node.meta circle{fill:#4a2d7a;stroke:#bc8cff}'
    
    html = TEMPLATE.replace("{TITLE}", "元认知图谱")
    html = html.replace("{EDGE_CSS}", edge_css)
    html = html.replace("{NODE_CSS}", node_css)
    html = html.replace("{LEGEND}", META_LEGEND)
    html = html.replace("{SIDEBAR_TITLE}", "&#x1F9E0; 元认知图谱")
    html = html.replace("{JS_CODE}", js)
    html = html.replace("{DATA}", json.dumps(data, ensure_ascii=False))
    (ROOT / "metacognition-mapper.html").write_text(html, encoding="utf-8")
    return len(html)

def build_know():
    data = json.loads((SYS / "knowledge_graph.json").read_text(encoding="utf-8"))
    js = JS.replace("{TL}", 'concept:"概念",fact:"事实",tool:"工具",resource:"资源",insight:"洞见",question:"问题",project:"项目",skill:"技能"')
    js = js.replace("{RL}", 'relates_to:"相关",depends_on:"依赖",part_of:"组成",example_of:"示例",contrasts_with:"对比",derives_from:"来源",used_in:"使用",prerequisite:"前置"')
    js = js.replace("{RADII}", 'concept:15,tool:13,project:14,skill:12,insight:11,fact:10,resource:10,question:9')
    js = js.replace("{LINK_DISTS}", 'part_of:120,used_in:140,depends_on:160,prerequisite:160,relates_to:200,example_of:180,contrasts_with:220,derives_from:170')
    js = js.replace("{CHARGE}", '-650')
    js = js.replace("{COLLIDE}", '22')
    edge_css = '.edge.relates_to{stroke:#484f58;stroke-dasharray:4 3}.edge.depends_on{stroke:#f85149}\n.edge.part_of{stroke:#58a6ff;stroke-opacity:0.5}.edge.example_of{stroke:#3fb950}\n.edge.contrasts_with{stroke:#d2991d;stroke-dasharray:6 2}.edge.derives_from{stroke:#a371f7}\n.edge.used_in{stroke:#39d353}.edge.prerequisite{stroke:#d2991d}'
    node_css = '.node.concept circle{fill:#1a5fb4;stroke:#3584e4}.node.fact circle{fill:#1f6f3b;stroke:#3fb950}\n.node.tool circle{fill:#935e00;stroke:#d2991d}.node.resource circle{fill:#6a2b8a;stroke:#a371f7}\n.node.insight circle{fill:#991b4e;stroke:#f778ba}.node.question circle{fill:#8b3a3a;stroke:#f85149}\n.node.project circle{fill:#116b63;stroke:#39d353}.node.skill circle{fill:#303fa0;stroke:#6e8fff}'
    
    html = TEMPLATE.replace("{TITLE}", "个人知识图谱")
    html = html.replace("{EDGE_CSS}", edge_css)
    html = html.replace("{NODE_CSS}", node_css)
    html = html.replace("{LEGEND}", KNOW_LEGEND)
    html = html.replace("{SIDEBAR_TITLE}", "&#x1F4DA; 个人知识图谱")
    html = html.replace("{JS_CODE}", js)
    html = html.replace("{DATA}", json.dumps(data, ensure_ascii=False))
    (ROOT / "knowledge-mapper.html").write_text(html, encoding="utf-8")
    return len(html)

def build_learn():
    data = json.loads((SYS / "learning_graph.json").read_text(encoding="utf-8"))
    js = JS.replace("{TL}", 'concept:"概念",fact:"事实",tool:"工具",resource:"资源",insight:"洞见",question:"疑问",project:"项目",skill:"技能"')
    js = js.replace("{RL}", 'relates_to:"相关",depends_on:"依赖",part_of:"组成",example_of:"示例",contrasts_with:"对比",derives_from:"来源",used_in:"使用",prerequisite:"前置",questions:"提问"')
    js = js.replace("{RADII}", 'concept:15,tool:13,project:14,skill:12,insight:11,fact:10,resource:10,question:14')
    js = js.replace("{LINK_DISTS}", 'part_of:120,used_in:140,depends_on:160,prerequisite:160,relates_to:200,example_of:180,contrasts_with:220,derives_from:170,questions:250')
    js = js.replace("{CHARGE}", '-650')
    js = js.replace("{COLLIDE}", '22')
    edge_css = '.edge.relates_to{stroke:#484f58;stroke-dasharray:4 3}.edge.depends_on{stroke:#f85149}\n.edge.part_of{stroke:#58a6ff;stroke-opacity:0.5}.edge.example_of{stroke:#3fb950}\n.edge.contrasts_with{stroke:#d2991d;stroke-dasharray:6 2}.edge.derives_from{stroke:#a371f7}\n.edge.used_in{stroke:#39d353}.edge.prerequisite{stroke:#d2991d}.edge.questions{stroke:#f0883e;stroke-dasharray:3 3}'
    node_css = '.node.asked circle{fill:#8b3a3a;stroke:#f85149}\n.node.learning circle{fill:#935e00;stroke:#d2991d}\n.node.todo circle{fill:#30363d;stroke:#484f58}\n.node.learned circle{fill:#1f6f3b;stroke:#3fb950}\n.node.question circle{fill:#991b4e;stroke:#f778ba}'
    
    html = TEMPLATE.replace("{TITLE}", "学习中图谱")
    html = html.replace("{EDGE_CSS}", edge_css)
    html = html.replace("{NODE_CSS}", node_css)
    html = html.replace("{LEGEND}", LEARN_LEGEND)
    html = html.replace("{SIDEBAR_TITLE}", "&#x1F4D6; 学习中图谱")
    html = html.replace("{JS_CODE}", js)
    html = html.replace("{DATA}", json.dumps(data, ensure_ascii=False))
    (ROOT / "learning-mapper.html").write_text(html, encoding="utf-8")
    return len(html)

m = build_meta()
k = build_know()
l = build_learn()
print(f"Meta: {m}B | Know: {k}B | Learn: {l}B")

# Verify
for name, path in [("Know", ROOT/"knowledge-mapper.html")]:
    h = path.read_text(encoding="utf-8")
    w = "wiki_description" in h and "The RK3568" in h
    print(f"{name} wiki present: {w}")
