#!/usr/bin/env python3
"""build_editor.py — Generate the note editor HTML."""
import json
from pathlib import Path

SYS = Path(__file__).resolve().parent
ROOT = SYS.parent
D3JS = (SYS / "d3.v7.min.js").read_text(encoding="utf-8")

# Load note graph data
note_graph = json.loads((SYS / "note_graph.json").read_text(encoding="utf-8"))
data_js = json.dumps(note_graph, ensure_ascii=False, separators=(",", ":"))

# Build note index (id -> file path)
notes_list = []
for n in note_graph["nodes"]:
    notes_list.append({
        "id": n["id"],
        "label": n["label"],
        "type": n["type"],
        "file": n.get("file", f"notes/{n['id']}.md"),
    })
notes_js = json.dumps(notes_list, ensure_ascii=False, separators=(",", ":"))

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>📝 原子笔记编辑器 — Atomic Note Editor</title>
<script>{D3JS}</script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;background:#0d1117;color:#c9d1d9;display:flex;height:100vh;overflow:hidden}}

/* ── Left: editor ── */
#editor-panel{{width:45%;min-width:400px;display:flex;flex-direction:column;background:#161b22;border-right:1px solid #30363d}}
#editor-header{{padding:12px 16px;border-bottom:1px solid #21262d;display:flex;justify-content:space-between;align-items:center}}
#editor-header h1{{font-size:15px;color:#f0f6fc}}
#editor-header .hint{{font-size:11px;color:#484f58}}
#editor-tabs{{display:flex;border-bottom:1px solid #21262d;background:#0d1117}}
.editor-tab{{padding:8px 16px;font-size:12px;cursor:pointer;color:#8b949e;border-bottom:2px solid transparent}}
.editor-tab.active{{color:#f0f6fc;border-bottom-color:#58a6ff}}
#editor-textarea{{flex:1;font-family:'Cascadia Code','Fira Code','Consolas',monospace;font-size:14px;line-height:1.7;padding:16px;background:#0d1117;color:#c9d1d9;border:none;outline:none;resize:none;tab-size:2}}

/* ── Preview / save status ── */
#editor-footer{{padding:8px 16px;border-top:1px solid #21262d;display:flex;justify-content:space-between;align-items:center;font-size:11px}}
#editor-footer .status{{color:#484f58}}
#editor-footer .status.ok{{color:#3fb950}}
#editor-footer button{{background:#238636;border:none;color:white;border-radius:6px;padding:6px 14px;font-size:12px;cursor:pointer}}
#editor-footer button:hover{{background:#2ea043}}
#editor-footer button.secondary{{background:#21262d;color:#c9d1d9;margin-left:6px}}
#editor-footer button.secondary:hover{{background:#30363d}}

/* ── Right: graph + note list ── */
#right-panel{{flex:1;display:flex;flex-direction:column}}
#graph-panel{{flex:1;position:relative;background:radial-gradient(ellipse at center,#1a1d27 0%,#0d1117 70%);min-height:300px}}
#graph-panel svg{{width:100%;height:100%}}
.edge{{stroke-opacity:0.3;fill:none}}
.edge.bi{{stroke:#58a6ff;stroke-width:1.5}}
.edge.mono{{stroke:#484f58;stroke-width:1;stroke-dasharray:3 2}}
.node circle{{stroke-width:2px;cursor:pointer;transition:r 0.2s;fill-opacity:0.85}}
.node text{{fill:#c9d1d9;font-size:10px;pointer-events:none;text-anchor:middle;font-family:"PingFang SC","Microsoft YaHei",sans-serif}}
.node.highlight circle{{stroke:#f0f6fc;stroke-width:3px;fill-opacity:1}}
.node.faded{{opacity:0.3}}
.edge.faded{{opacity:0.1}}

#link-bar{{padding:8px 16px;background:#0d1117;border-top:1px solid #21262d;font-size:12px;color:#8b949e;display:flex;gap:12px;flex-wrap:wrap}}
#link-bar .linked{{color:#58a6ff}}
#link-bar .lb-section{{flex:1;min-width:120px}}
#link-bar .lb-section h4{{font-size:10px;color:#484f58;text-transform:uppercase;margin-bottom:2px}}
.link-chip{{display:inline-block;background:#1c2128;border:1px solid #30363d;border-radius:4px;padding:2px 8px;font-size:11px;margin:2px;color:#58a6ff;cursor:pointer}}
.link-chip:hover{{border-color:#58a6ff}}

#graph-tools{{position:absolute;bottom:8px;right:8px;display:flex;gap:4px}}
#graph-tools button{{background:rgba(22,27,34,0.93);border:1px solid #30363d;color:#c9d1d9;border-radius:5px;padding:4px 8px;font-size:10px;cursor:pointer}}
#graph-tools button:hover{{background:#30363d}}

#backlinks-panel{{max-height:120px;overflow-y:auto;padding:6px 16px;background:#0d1117;border-top:1px solid #21262d;font-size:11px;color:#8b949e}}
#backlinks-panel a{{color:#58a6ff;text-decoration:none;margin:0 4px}}
#backlinks-panel a:hover{{color:#a371f7}}

/* ── Note list sidebar ── */
#note-sidebar{{position:fixed;right:0;top:0;width:260px;height:100vh;background:#161b22;border-left:1px solid #30363d;display:none;overflow-y:auto;z-index:10}}
#note-sidebar.open{{display:block}}
#note-sidebar h3{{font-size:12px;padding:12px;color:#8b949e;border-bottom:1px solid #21262d}}
.ns-item{{padding:6px 12px;font-size:12px;cursor:pointer;border-bottom:1px solid #21262d;color:#c9d1d9}}
.ns-item:hover{{background:#1c2128}}
.ns-item .ns-type{{font-size:9px;color:#484f58;margin-left:4px}}
.nav-bar{{display:flex;gap:8px;font-size:12px}}
.nav-bar a{{color:#8b949e;text-decoration:none}}
.nav-bar a:hover{{color:#f0f6fc}}
.nav-bar .sep{{color:#30363d}}
</style></head>
<body>
<div id="editor-panel">
  <div id="editor-header">
    <div style="display:flex;justify-content:space-between;align-items:center;width:100%">
      <h1>📝 原子笔记</h1>
      <div class="nav-bar"><a href="index.html">🏠</a><span class="sep">|</span><a href="knowledge-explorer.html">🌐</a><span class="sep">|</span><a href="metacognition-mapper.html">🧠</a></div>
    </div>
    <span class="hint">使用 [[Wiki链接]] 建立关联 · 一笔记一概念</span>
  </div>
  <div id="editor-tabs">
    <div class="editor-tab active" onclick="switchTab('edit',this)">✏️ 编辑</div>
    <div class="editor-tab" onclick="switchTab('preview',this)">👁️ 预览</div>
    <div class="editor-tab" onclick="toggleNoteSidebar()">📚 笔记列表</div>
  </div>
  <textarea id="editor-textarea" placeholder="在此写你的原子笔记...&#10;&#10;使用 [[双链]] 关联其他概念&#10;支持 Markdown 语法&#10;&#10;示例：&#10;# 元认知蒸馏&#10;&#10;从AI对话日志中自动提取用户认知模式的技术。&#10;&#10;参见 [[CodeWhale]]、[[D3.js力导向图]]" oninput="onEdit()"></textarea>
  <div id="editor-footer">
    <span class="status" id="save-status">💡 新建笔记</span>
    <div>
      <button class="secondary" onclick="loadNote()">📂 打开</button>
      <button class="secondary" onclick="toggleNoteSidebar()">📚</button>
      <button onclick="saveNote()">💾 保存</button>
    </div>
  </div>
</div>

<div id="right-panel">
  <div id="graph-panel"><svg></svg>
    <div id="graph-tools">
      <button onclick="toggleNoteSidebar()">📚</button>
      <button onclick="resetGraph()">↺</button>
    </div>
  </div>
  <div id="link-bar">
    <div class="lb-section">
      <h4>🔗 本文链接</h4>
      <span id="current-links"><span style="color:#484f58">输入 [[ 开始链接</span></span>
    </div>
    <div class="lb-section">
      <h4>← 反向链接</h4>
      <span id="backlink-display"><span style="color:#484f58">保存后显示</span></span>
    </div>
  </div>
</div>

<div id="note-sidebar">
  <h3>📚 所有笔记 <span style="color:#484f58;font-weight:normal" id="ns-count"></span></h3>
  <div id="ns-list"></div>
</div>

<script>
// ═══ Data ═══
var graphData = {data_js};
var notesIndex = {notes_js};
var nodesMap = {{}};
graphData.nodes.forEach(n => {{ nodesMap[n.id] = n; }});
var currentFile = null;

// ═══ D3.js graph ═══
var svg = d3.select('#graph-panel svg');
var g = svg.append('g');
var zoom = d3.zoom().scaleExtent([0.1, 8]).on('zoom', e => g.attr('transform', e.transform));
svg.call(zoom);
var sim;

function renderGraph() {{
  g.selectAll('*').remove();
  var nodes = graphData.nodes.map(n => ({{...n}}));
  var edges = graphData.edges.map(e => ({{...e}}));

  var link = g.append('g').selectAll('line').data(edges).join('line')
    .attr('class', d => {{
      var s = d.source.id||d.source, t = d.target.id||d.target;
      var bidir = edges.some(e2 => {{ var s2=e2.source.id||e2.source, t2=e2.target.id||e2.target; return s2===t && t2===s; }});
      return 'edge ' + (bidir?'bi':'mono');
    }});

  var node = g.append('g').selectAll('g').data(nodes).join('g')
    .attr('class', 'node')
    .call(d3.drag()
      .on('start', (e,d) => {{ if(!e.active) sim.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; }})
      .on('drag', (e,d) => {{ d.fx=e.x; d.fy=e.y; }})
      .on('end', (e,d) => {{ if(!e.active) sim.alphaTarget(0); d.fx=null; d.fy=null; }})
    );

  var colors = {{concept:'#1a5fb4',meta:'#4a2d7a',tool:'#935e00',skill:'#303fa0',domain:'#316dca',strategy:'#6e40c9',learning:'#9e6a03',question:'#8b3a3a',belief:'#9e6a03',bias:'#8b3a3a',emotion:'#b0376b',fact:'#1f6f3b',insight:'#991b4e',project:'#116b63',default:'#21262d'}};
  function rd(d) {{ return ({{concept:10,meta:12,tool:9,skill:9,domain:11,strategy:9,learning:8,question:7}}[d.type]||7) + Math.min(3, d.backlink_count||0); }}

  node.append('circle').attr('r', rd).attr('fill', d => colors[d.type]||colors.default).attr('stroke', d => d3.color(colors[d.type]||colors.default).brighter(0.5));
  node.append('text').text(d => d.label).attr('dy', d => rd(d)+12);

  var W = document.getElementById('graph-panel').clientWidth;
  var H = document.getElementById('graph-panel').clientHeight;

  sim = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d=>d.id).distance(120).strength(0.25))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide().radius(d=>rd(d)+15))
    .alphaDecay(0.025)
    .on('tick', () => {{
      link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
      node.attr('transform',d=>'translate('+d.x+','+d.y+')');
    }});
}}

function highlightConnections(id) {{
  g.selectAll('.node').classed('highlight', d=>d.id===id).classed('faded', d=>d.id!==id);
  g.selectAll('.edge').classed('faded', d => {{
    var s=d.source.id||d.source, t=d.target.id||d.target;
    return s!==id && t!==id;
  }});
}}

function resetGraph() {{
  g.selectAll('.node').classed('highlight', false).classed('faded', false);
  g.selectAll('.edge').classed('faded', false);
  svg.transition().duration(400).call(zoom.transform, d3.zoomIdentity);
}}

// ═══ Editor logic ═══
function extractWikiLinks(text) {{
  var re = /\\[\\[([^\\]]+)\\]\\]/g;
  var links = [], m;
  while ((m = re.exec(text)) !== null) {{
    if (links.indexOf(m[1]) === -1) links.push(m[1]);
  }}
  return links;
}}

function extractTitle(text) {{
  var m = text.match(/^#\\s+(.+)$/m);
  return m ? m[1].trim() : '未命名笔记';
}}

function onEdit() {{
  var text = document.getElementById('editor-textarea').value;
  var links = extractWikiLinks(text);
  var title = extractTitle(text);

  // Update link chips
  var el = document.getElementById('current-links');
  if (links.length === 0) {{
    el.innerHTML = '<span style="color:#484f58">输入 [[ 开始链接</span>';
  }} else {{
    el.innerHTML = links.map(l => {{
      var exists = nodesMap[l.replace(/ /g,'_')];
      return '<span class="link-chip" onclick="focusNote(\\''+l.replace(/'/g,"\\\\'")+'\\')">'+l+(exists?'':' ⚠️')+'</span>';
    }}).join(' ');
  }}

  // Live preview: highlight connected nodes
  var linkedIds = links.map(l => l.replace(/ /g,'_'));
  var idsInGraph = linkedIds.filter(id => nodesMap[id]);
  if (idsInGraph.length > 0) {{
    // Dim all, then highlight connected
    g.selectAll('.node').classed('faded', d => idsInGraph.indexOf(d.id) === -1);
    g.selectAll('.edge').classed('faded', d => {{
      var s=d.source.id||d.source, t=d.target.id||d.target;
      return idsInGraph.indexOf(s) === -1 && idsInGraph.indexOf(t) === -1;
    }});
  }} else {{
    resetGraph();
  }}

  updateStatus('preview');
}}

function focusNote(label) {{
  var id = label.replace(/ /g,'_');
  var found = graphData.nodes.filter(n => n.id === id || n.label === label);
  if (found.length > 0) {{
    highlightConnections(found[0].id);
  }}
}}

function saveNote() {{
  var text = document.getElementById('editor-textarea').value;
  var title = extractTitle(text);
  var safeName = title.replace(/[\\\\/*?:"<>|]/g, '_').slice(0, 60);
  if (!safeName) {{ updateStatus('error', '请输入标题'); return; }}

  // Build YAML frontmatter
  var links = extractWikiLinks(text);
  var types = ['concept', 'meta', 'tool', 'skill', 'domain', 'strategy', 'learning', 'question'];
  var ntype = 'concept';
  // Try to detect type
  var tm = text.match(/^type:\\s*(\\w+)$/m);
  if (tm && types.indexOf(tm[1]) !== -1) ntype = tm[1];

  var frontmatter = '---\\ntitle: ' + title + '\\ntype: ' + ntype + '\\nconfidence: likely\\ndepth: 0\\n---\\n\\n';

  // Remove any existing frontmatter
  var body = text.replace(/^---\\n[\\s\\S]*?\\n---\\n/, '');
  body = body.trim();

  var content = frontmatter + body + '\\n';

  // Trigger download (local-first — save to notes/ directory)
  var blob = new Blob([content], {{type: 'text/markdown;charset=utf-8'}});
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = safeName + '.md';
  a.click();
  URL.revokeObjectURL(url);

  currentFile = 'notes/' + safeName + '.md';
  updateStatus('ok', '✅ 已保存: ' + safeName + '.md');
}}

function loadNote() {{
  var input = document.createElement('input');
  input.type = 'file';
  input.accept = '.md,.markdown';
  input.onchange = function(e) {{
    var file = e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(ev) {{
      document.getElementById('editor-textarea').value = ev.target.result;
      currentFile = file.name;
      onEdit();
      updateStatus('ok', '📂 已打开: ' + file.name);
    }};
    reader.readAsText(file, 'UTF-8');
  }};
  input.click();
}}

function updateStatus(type, msg) {{
  var el = document.getElementById('save-status');
  if (type === 'ok') {{ el.className = 'status ok'; el.textContent = msg || '✅ 已保存'; }}
  else if (type === 'error') {{ el.className = 'status'; el.textContent = '❌ ' + msg; }}
  else {{ el.className = 'status'; el.textContent = '💡 ' + (msg || '编辑中...'); }}
}}

// ═══ Tab switch ═══
function switchTab(tab, el) {{
  document.querySelectorAll('.editor-tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  var ta = document.getElementById('editor-textarea');
  if (tab === 'preview') {{
    // Show rendered markdown preview (basic)
    ta.readOnly = true;
  }} else {{
    ta.readOnly = false;
    ta.focus();
  }}
}}

// ═══ Note sidebar ═══
function toggleNoteSidebar() {{
  var sb = document.getElementById('note-sidebar');
  sb.classList.toggle('open');
  if (sb.classList.contains('open')) renderNoteSidebar();
}}

function renderNoteSidebar() {{
  var el = document.getElementById('ns-list');
  document.getElementById('ns-count').textContent = ' (' + notesIndex.length + ')';
  el.innerHTML = notesIndex.map(n => {{
    return '<div class="ns-item" onclick="openNoteFromSidebar(\\''+n.id+'\\',\\''+n.label.replace(/'/g,"\\\\'")+'\\',\\''+(n.file||'')+'\\')">'
      + n.label + ' <span class="ns-type">' + n.type + '</span></div>';
  }}).join('');
}}

function openNoteFromSidebar(id, label, file) {{
  if (file) {{
    // Try to load file content via fetch
    fetch('/' + file)
      .then(r => r.text())
      .then(text => {{
        document.getElementById('editor-textarea').value = text;
        currentFile = file;
        onEdit();
        updateStatus('ok', '📂 ' + label);
      }})
      .catch(() => {{
        // If served as file://, show info
        updateStatus('error', '需通过 HTTP 服务器打开以加载笔记');
        window.open(file, '_blank');
      }});
  }}
  document.getElementById('note-sidebar').classList.remove('open');
  highlightConnections(id);
}}

// ═══ Init ═══
renderGraph();
updateStatus('preview', '开始写你的原子笔记...');
</script></body></html>"""

out = ROOT / "note-editor.html"
out.write_text(HTML, encoding="utf-8")
print(f"✅ Note editor → {out.relative_to(ROOT)} ({len(HTML)//1024}KB)")
