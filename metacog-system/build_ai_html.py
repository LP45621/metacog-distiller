"""Generate AI Capability HTML using build_final_html.py pattern with inline D3.js"""
import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = Path(r"D:\ai项目\metacog-distiller")
SYS = BASE / "metacog-system"
D3JS = (SYS / "d3.v7.min.js").read_text(encoding="utf-8")
ai = json.loads((SYS / "ai_capability_graph.json").read_text(encoding="utf-8"))
ai_js = json.dumps(ai, ensure_ascii=False, separators=(',', ':'))

html = f'''<!DOCTYPE html>
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
.node.ai_tool circle{{fill:#e65100;stroke:#ff9800}}
.node.ai_concept circle{{fill:#1565c0;stroke:#42a5f5}}
.node.ai_strategy circle{{fill:#6a1b9a;stroke:#ab47bc}}
.node.ai_skill circle{{fill:#00695c;stroke:#26a69a}}
.node.tool circle{{fill:#e65100;stroke:#ff9800}}
.node.concept circle{{fill:#1565c0;stroke:#42a5f5}}
.node.skill circle{{fill:#00695c;stroke:#26a69a}}
.node.text-label{{fill:#e0e0e0;font-size:12px;pointer-events:none;text-anchor:middle;font-family:"PingFang SC","Microsoft YaHei",sans-serif}}
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
.lr{{display:flex;align-items:center;margin:3px 0;gap:6px}}
.ld{{width:9px;height:9px;border-radius:50%;flex-shrink:0}}
#graph-tools{{position:absolute;bottom:12px;right:12px;display:flex;gap:6px}}
#graph-tools button{{background:rgba(22,27,34,0.93);border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:6px 12px;font-size:11px;cursor:pointer}}
#graph-tools button:hover{{background:#30363d}}
</style></head>
<body>
<div id="graph-panel"><svg></svg>
<div id="legend">
<h3>AI 能力类型</h3>
<div class="lr"><span class="ld" style="background:#e65100"></span>AI 工具</div>
<div class="lr"><span class="ld" style="background:#1565c0"></span>AI 概念</div>
<div class="lr"><span class="ld" style="background:#6a1b9a"></span>AI 策略</div>
<div class="lr"><span class="ld" style="background:#00695c"></span>AI 技能</div>
<h3 style="margin-top:8px">关系</h3>
<div class="lr"><span class="ld" style="background:#58a6ff;border-radius:2px;width:16px;height:3px"></span>组成</div>
<div class="lr"><span class="ld" style="background:#f0883e;border-radius:2px;width:16px;height:3px"></span>依赖</div>
<div class="lr"><span class="ld" style="background:#3fb950;border-radius:2px;width:16px;height:3px"></span>支持</div>
</div>
<div id="graph-tools"><button onclick="zI()">+</button><button onclick="zO()">-</button><button onclick="zR()">&#x21BA;</button></div></div>
<div id="sidebar"><div id="sidebar-header"><h2>&#x1F916; AI 能力图谱</h2><div class="subtitle" id="stats">loading</div></div>
<div id="detail-content"><div class="empty">&#x1F446; hover node to view details</div></div></div>
<script>
var svg=d3.select("svg"),g=svg.append("g");
var zoom=d3.zoom().scaleExtent([0.1,8]).on("zoom",function(e){{g.attr("transform",e.transform)}});svg.call(zoom);
var s,gn=[],ge=[];
var tl={{concept:"AI概念",tool:"AI工具",skill:"AI技能"}};
var rl={{part_of:"组成",depends_on:"依赖",supports:"支持",used_in:"使用",relates_to:"相关",influences:"影响",derives_from:"来源",prerequisite:"前置"}};
var cl={{certain:"确信",likely:"可能",speculative:"推测"}};
function nr(d){{var m={{concept:16,tool:15,skill:13}};return m[d.type]||12}}
function r(data){{
g.selectAll("*").remove();
gn=data.nodes.map(n=>Object.assign({{}},n));
ge=data.edges.map(e=>Object.assign({{}},e));
document.getElementById("stats").textContent=gn.length+" AI nodes · "+ge.length+" links";
var lk=g.append("g").selectAll("line").data(ge).join("line").attr("class",d=>"edge "+(d.type||"relates_to")).attr("stroke-width",1.8);
var nd=g.append("g").selectAll("g").data(gn).join("g").attr("class",d=>"node "+(d.type||"concept")).call(d3.drag().on("start",(e,d)=>{{if(!e.active)s.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y}}).on("drag",(e,d)=>{{d.fx=e.x;d.fy=e.y}}).on("end",(e,d)=>{{if(!e.active)s.alphaTarget(0);d.fx=null;d.fy=null}})).on("mouseenter",function(e,d){{g.selectAll(".node").classed("selected",false);d3.select(this).classed("selected",true);sd(d)}}).on("mouseleave",function(){{g.selectAll(".node").classed("selected",false);}});
nd.append("circle").attr("r",nr).on("mouseenter",function(e,d){{d3.select(this).transition().duration(150).attr("r",nr(d)+5)}}).on("mouseleave",function(e,d){{d3.select(this).transition().duration(150).attr("r",nr(d))}});
nd.append("text").attr("class","text-label").text(d=>d.label).style("font-family",'"PingFang SC","Microsoft YaHei",sans-serif');
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

(BASE / "ai-capability-mapper.html").write_text(html, encoding="utf-8")
print(f"AI Capability HTML: {len(html)}B")
print("Done")
