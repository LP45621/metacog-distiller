#!/usr/bin/env python3
"""
note_graph.py — Atomic Note → Graph Pipeline
=============================================
Scans notes/ for [[wiki-links]], resolves backlinks,
builds graph JSON, and generates a standalone explorer HTML.

Usage:
  python3 note_graph.py                # rebuild graph + explorer HTML
  python3 note_graph.py --search kw    # search notes for keyword
  python3 note_graph.py --serve        # start local HTTP server on :19801
"""
import argparse
import json
import re
import webbrowser
from pathlib import Path

SYS = Path(__file__).resolve().parent
ROOT = SYS.parent
NOTES = ROOT / "notes"
D3JS_PATH = SYS / "d3.v7.min.js"

# ─── Scan notes & resolve [[links]] ──────────────────────────
def scan_notes():
    """Read all .md files, extract frontmatter, [[links]], text."""
    notes = {}  # filename_stem -> note_info
    for f in sorted(NOTES.glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        stem = f.stem  # filename without .md
        # Extract title from frontmatter or first heading
        title = stem
        m = re.search(r'^title:\s*(.+)$', text, re.MULTILINE)
        if m:
            title = m.group(1).strip()
        m2 = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        display = title  # title from frontmatter is authoritative

        # Extract type/confidence from frontmatter
        ntype = "concept"
        m3 = re.search(r'^type:\s*(.+)$', text, re.MULTILINE)
        if m3:
            ntype = m3.group(1).split("|")[0].strip()

        # Extract summary (text after frontmatter, before ## Links)
        body = text
        # Remove frontmatter
        body = re.sub(r'^---\n.*?\n---\n', '', body, flags=re.DOTALL)
        # Remove ## Links and ## Backlinks sections
        body = re.split(r'\n##\s+(?:链接|Links|反向链接|Backlinks)\b', body, maxsplit=1)[0]
        summary = body.strip().lstrip('#').strip()[:300]

        # Find all [[wiki-links]]
        wiki_links = re.findall(r'\[\[([^\]]+)\]\]', text)
        linked_to = []
        for wl in wiki_links:
            # Normalize: try exact match, then case-insensitive
            target_stem = wl.replace(' ', '_').replace('/', '_')
            target_stem = re.sub(r'[\\/*?:"<>|]', '_', target_stem)[:60]
            # Find matching file
            match_file = NOTES / f"{target_stem}.md"
            if match_file.exists():
                linked_to.append(target_stem)
            else:
                # Case-insensitive search
                for nf in NOTES.glob("*.md"):
                    if nf.stem.lower() == target_stem.lower():
                        linked_to.append(nf.stem)
                        break
                else:
                    linked_to.append(target_stem)  # dead link (but track it)

        notes[stem] = {
            "id": stem,
            "label": title,
            "display": display,
            "type": ntype,
            "summary": summary,
            "links": linked_to,
            "file": str(f.relative_to(ROOT)),
            "backlinks": [],  # filled in pass 2
        }

    # Pass 2: resolve backlinks
    for stem, info in notes.items():
        for other_stem, other_info in notes.items():
            if stem in other_info.get("links", []):
                info["backlinks"].append(other_stem)

    # Pass 3: deduplicate links, remove self-refs
    for info in notes.values():
        info["links"] = list(dict.fromkeys(l for l in info["links"] if l != info["id"]))

    return notes


def build_graph_json(notes):
    """Convert notes dict → D3.js-friendly graph JSON with edges as bidirectional pairs."""
    nodes = []
    edges = []
    edge_pairs = set()

    for stem, info in notes.items():
        nodes.append({
            "id": info["id"],
            "label": info["display"],
            "type": info["type"],
            "summary": info["summary"][:200],
            "backlink_count": len(info["backlinks"]),
            "link_count": len(info["links"]),
            "file": info["file"],
        })
        for target in info["links"]:
            pair = tuple(sorted([stem, target]))
            if pair not in edge_pairs:
                edge_pairs.add(pair)
                edges.append({
                    "source": stem,
                    "target": target,
                    "type": "links_to",
                    "label": "双向链接" if stem in notes.get(target, {}).get("links", []) else "单向链接",
                })

    return {"nodes": nodes, "edges": edges}


# ─── Full-text search ────────────────────────────────────
def search_notes(notes, keyword):
    """Search note text for keyword, return matches with context."""
    results = []
    for f in sorted(NOTES.glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        if keyword.lower() in text.lower():
            # Find context snippets
            lines = text.split('\n')
            matches = []
            for i, line in enumerate(lines):
                if keyword.lower() in line.lower():
                    ctx_start = max(0, i-1)
                    ctx_end = min(len(lines), i+2)
                    snippet = '\n'.join(lines[ctx_start:ctx_end])
                    matches.append({"line": i, "snippet": snippet.strip()[:200]})
            stem = f.stem
            results.append({
                "file": str(f.relative_to(ROOT)),
                "title": notes[stem]["display"] if stem in notes else stem,
                "matches": matches,
                "backlinks": notes[stem]["backlinks"] if stem in notes else [],
            })
    return results


# ─── Generate explorer HTML ──────────────────────────────
def build_explorer_html(graph_data, d3js):
    """Generate a self-contained explorer: note list + local graph + search."""
    data_js = json.dumps(graph_data, ensure_ascii=False, separators=(',', ':'))

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>知识图谱浏览器 — Knowledge Graph Explorer</title>
<script>{d3js}</script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;background:#0d1117;color:#c9d1d9;display:flex;height:100vh;overflow:hidden}}

/* ── Left panel: search + note list ── */
#left-panel{{width:340px;min-width:280px;display:flex;flex-direction:column;background:#161b22;border-right:1px solid #30363d;flex-shrink:0}}
#search-area{{padding:12px;border-bottom:1px solid #21262d}}
#search-area input{{width:100%;background:#0d1117;border:1px solid #30363d;border-radius:8px;color:#c9d1d9;padding:8px 12px;font-size:13px;outline:none}}
#search-area input:focus{{border-color:#58a6ff}}
#search-stats{{font-size:11px;color:#484f58;padding:4px 12px 0}}
#note-list{{flex:1;overflow-y:auto;padding:4px 0}}
.note-item{{padding:8px 12px;border-bottom:1px solid #21262d;cursor:pointer;transition:background 0.15s}}
.note-item:hover{{background:#1c2128}}
.note-item .ni-title{{font-size:13px;color:#f0f6fc;font-weight:500}}
.note-item .ni-meta{{font-size:11px;color:#8b949e;margin-top:2px}}
.note-item .ni-type{{display:inline-block;font-size:10px;padding:1px 6px;border-radius:4px;margin-right:4px}}
.note-item .ni-type.concept{{background:#1a5fb4;color:#c9d1d9}}
.note-item .ni-type.meta{{background:#4a2d7a;color:#c9d1d9}}
.note-item .ni-type.tool{{background:#935e00;color:#c9d1d9}}
.note-item .ni-type.skill{{background:#303fa0;color:#c9d1d9}}
.note-item .ni-type.domain{{background:#316dca;color:#c9d1d9}}
.note-item .ni-type.strategy{{background:#6e40c9;color:#c9d1d9}}
.note-item .ni-type.learning{{background:#9e6a03;color:#c9d1d9}}
.note-item .ni-type.question{{background:#8b3a3a;color:#c9d1d9}}
.note-item .ni-type.default{{background:#21262d;color:#8b949e}}
.note-item .ni-badge{{font-size:10px;color:#484f58;margin-left:6px}}

/* ── Center: graph ── */
#graph-panel{{flex:1;position:relative;background:radial-gradient(ellipse at center,#1a1d27 0%,#0d1117 70%)}}
#graph-panel svg{{width:100%;height:100%}}
.node circle{{stroke-width:2px;cursor:pointer;transition:r 0.2s;fill-opacity:0.85}}
.node text{{fill:#c9d1d9;font-size:11px;pointer-events:none;text-anchor:middle;font-family:"PingFang SC","Microsoft YaHei",sans-serif}}
.node.selected circle{{stroke:#f0f6fc;stroke-width:3px;fill-opacity:1}}
.edge{{stroke-opacity:0.35;fill:none}}
.edge.bi{{stroke:#58a6ff;stroke-width:1.8}}
.edge.mono{{stroke:#484f58;stroke-width:1.2;stroke-dasharray:4 3}}

/* ── Right detail panel ── */
#detail-panel{{width:360px;background:#161b22;border-left:1px solid #30363d;display:flex;flex-direction:column;overflow-y:auto;flex-shrink:0}}
#detail-header{{padding:16px;border-bottom:1px solid #21262d}}
#detail-header h2{{font-size:15px;color:#f0f6fc}}
#detail-header .sub{{font-size:11px;color:#484f58;margin-top:4px}}
#detail-body{{padding:16px;flex:1}}
#detail-body .empty{{color:#484f58;text-align:center;margin-top:80px;font-size:14px}}
.detail-summary{{font-size:13px;line-height:1.6;color:#c9d1d9;margin-bottom:12px}}
.link-section{{margin-top:16px}}
.link-section h3{{font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#8b949e;margin-bottom:6px}}
.link-item{{font-size:12px;padding:4px 0;color:#58a6ff;cursor:pointer}}
.link-item:hover{{color:#a371f7}}
.link-item .dir{{color:#484f58;margin-right:4px}}
.link-item.no-links{{color:#484f58;font-style:italic}}

/* ── tools ── */
#graph-tools{{position:absolute;bottom:12px;right:12px;display:flex;gap:4px}}
#graph-tools button{{background:rgba(22,27,34,0.93);border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:5px 10px;font-size:11px;cursor:pointer;font-family:inherit}}
#graph-tools button:hover{{background:#30363d}}

/* ── Search results ── */
.search-result{{padding:6px 12px;font-size:12px;color:#8b949e;border-bottom:1px solid #21262d;cursor:pointer}}
.search-result:hover{{background:#1c2128}}
.search-result .hit{{color:#d2991d}}
.search-result .src{{font-size:10px;color:#484f58}}
</style></head>
<body>
<div id="left-panel">
  <div id="search-area">
    <input id="search-input" placeholder="🔍 搜索笔记..." oninput="doSearch(this.value)">
    <div id="search-stats"></div>
  </div>
  <div id="note-list"></div>
</div>
<div id="graph-panel"><svg></svg>
  <div id="graph-tools">
    <button onclick="focusConnected()">🔗 聚焦关联</button>
    <button onclick="resetView()">↺ 重置</button>
    <button onclick="randomNote()">🎲 随机</button>
  </div>
</div>
<div id="detail-panel">
  <div id="detail-header"><h2>🔍 知识图谱浏览器</h2><div class="sub" id="graph-stats">加载中...</div></div>
  <div id="detail-body"><div class="empty">👆 点击左侧笔记或图谱节点查看详情</div></div>
</div>

<script>
// ═══ Data ═══
var graphData = {data_js};
var nodesMap = {{}};
graphData.nodes.forEach(n => {{ nodesMap[n.id] = n; }});

// ═══ Render note list ═══
function renderNoteList(filter) {{
  var el = document.getElementById('note-list');
  var list = graphData.nodes;
  if (filter) {{
    var f = filter.toLowerCase();
    list = list.filter(n => n.label.toLowerCase().includes(f) || (n.summary||'').toLowerCase().includes(f));
  }}
  document.getElementById('search-stats').textContent = list.length + ' / ' + graphData.nodes.length + ' 笔记';
  el.innerHTML = list.map(n => {{
    var typeClass = ['concept','meta','tool','skill','domain','strategy','learning','question'].includes(n.type) ? n.type : 'default';
    return '<div class="note-item" onclick="selectNote(\\''+n.id+'\\')">' +
      '<div class="ni-title">'+n.label+' <span class="ni-type '+typeClass+'">'+n.type+'</span></div>' +
      '<div class="ni-meta">' + (n.summary||'').slice(0,60) + '' +
      ' <span class="ni-badge">→'+ (n.link_count||0) +' ←'+ (n.backlink_count||0) +'</span></div></div>';
  }}).join('');
}}

function doSearch(val) {{
  renderNoteList(val);
  // Clear detail when search changes
  if (val) document.getElementById('detail-body').innerHTML = '<div class="empty">🔍 搜索结果</div>';
}}

// ═══ D3.js Graph ═══
var svg = d3.select('#graph-panel svg');
var g = svg.append('g');
var zoom = d3.zoom().scaleExtent([0.1,8]).on('zoom', e => g.attr('transform', e.transform));
svg.call(zoom);

var simulation, link, node;

function renderGraph(focusId) {{
  g.selectAll('*').remove();

  var nodes = focusId ? expandLocal(focusId) : graphData.nodes.map(n => ({{...n}}));
  var nodeIds = new Set(nodes.map(n => n.id));
  var edges = graphData.edges
    .filter(e => nodeIds.has(e.source.id || e.source) && nodeIds.has(e.target.id || e.target))
    .map(e => ({{...e}}));

  link = g.append('g').selectAll('line').data(edges).join('line')
    .attr('class', d => {{
      var s = d.source.id || d.source;
      var t = d.target.id || d.target;
      var bidir = graphData.edges.some(e2 => {{
        var s2 = e2.source.id || e2.source;
        var t2 = e2.target.id || e2.target;
        return s2 === t && t2 === s;
      }});
      return 'edge ' + (bidir ? 'bi' : 'mono');
    }});

  node = g.append('g').selectAll('g').data(nodes).join('g')
    .attr('class', 'node')
    .call(d3.drag()
      .on('start', (e,d) => {{ if(!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
      .on('drag', (e,d) => {{ d.fx = e.x; d.fy = e.y; }})
      .on('end', (e,d) => {{ if(!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }})
    )
    .on('click', (e,d) => {{ e.stopPropagation(); selectNote(d.id); }})
    .on('mouseenter', function(e,d) {{ d3.select(this).select('circle').transition().duration(150).attr('r', r(d)+5); }})
    .on('mouseleave', function(e,d) {{ d3.select(this).select('circle').transition().duration(150).attr('r', r(d)); }});

  var colors = {{concept:'#1a5fb4',meta:'#4a2d7a',tool:'#935e00',skill:'#303fa0',domain:'#316dca',strategy:'#6e40c9',learning:'#9e6a03',question:'#8b3a3a',belief:'#9e6a03',bias:'#8b3a3a',emotion:'#b0376b',fact:'#1f6f3b',insight:'#991b4e',project:'#116b63',resource:'#6a2b8a',default:'#21262d'}};
  function r(d) {{ var m = {{concept:12,meta:14,tool:10,skill:11,domain:13,strategy:10,learning:9,question:8,belief:10,bias:9,emotion:8,fact:9,insight:10,project:11,resource:9}}; return (m[d.type]||8) + Math.min(4, (d.backlink_count||0)); }}

  node.append('circle')
    .attr('r', d => r(d))
    .attr('fill', d => colors[d.type]||colors.default)
    .attr('stroke', d => d3.color(colors[d.type]||colors.default).brighter(0.5));

  node.append('text').text(d => d.label).attr('dy', d => r(d)+14);

  if (focusId) {{
    node.attr('opacity', d => d.id === focusId ? 1 : 0.7);
    link.attr('opacity', d => {{
      var s = d.source.id || d.source; var t = d.target.id || d.target;
      return (s === focusId || t === focusId) ? 1 : 0.2;
    }});
  }}

  var W = document.getElementById('graph-panel').clientWidth;
  var H = document.getElementById('graph-panel').clientHeight;

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(130).strength(0.3))
    .force('charge', d3.forceManyBody().strength(-250))
    .force('center', d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide().radius(d => r(d)+20))
    .alphaDecay(0.02)
    .on('tick', () => {{
      link.attr('x1', d=>d.source.x).attr('y1', d=>d.source.y).attr('x2', d=>d.target.x).attr('y2', d=>d.target.y);
      node.attr('transform', d=>'translate('+d.x+','+d.y+')');
    }});

  document.getElementById('graph-stats').textContent = nodes.length + ' 节点 · ' + edges.length + ' 连线';
}}

function expandLocal(focusId) {{
  var connected = new Set([focusId]);
  graphData.edges.forEach(e => {{
    var s = e.source.id || e.source;
    var t = e.target.id || e.target;
    if (s === focusId) connected.add(t);
    if (t === focusId) connected.add(s);
  }});
  return graphData.nodes.filter(n => connected.has(n.id)).map(n => ({{...n}}));
}}

function selectNote(id) {{
  var n = nodesMap[id];
  if (!n) return;

  // Update detail
  var body = document.getElementById('detail-body');
  var connected = graphData.edges.filter(e => {{
    var s = e.source.id || e.source; var t = e.target.id || e.target;
    return s === id || t === id;
  }});

  var html = '<div class="detail-summary">' + (n.summary||'暂无摘要') + '</div>';
  html += '<div class="link-section"><h3>📎 笔记文件</h3><div class="link-item" onclick="openNote(\\''+n.id+'\\')">📄 ' + (n.file||'notes/'+n.id+'.md') + '</div></div>';

  // Outgoing links
  var outLinks = connected.filter(e => (e.source.id||e.source) === id);
  html += '<div class="link-section"><h3>→ 链接 ('+outLinks.length+')</h3>';
  if (outLinks.length) html += outLinks.map(e => {{
    var tgt = nodesMap[e.target.id||e.target];
    return '<div class="link-item" onclick="selectNote(\\''+(e.target.id||e.target)+'\\')">→ '+(tgt?tgt.label:e.target.id||e.target)+'</div>';
  }}).join('');
  else html += '<div class="link-item no-links">暂无向外链接</div>';
  html += '</div>';

  // Incoming backlinks
  var inLinks = connected.filter(e => (e.target.id||e.target) === id);
  html += '<div class="link-section"><h3>← 反向链接 ('+inLinks.length+')</h3>';
  if (inLinks.length) html += inLinks.map(e => {{
    var src = nodesMap[e.source.id||e.source];
    return '<div class="link-item" onclick="selectNote(\\''+(e.source.id||e.source)+'\\')">← '+(src?src.label:e.source.id||e.source)+'</div>';
  }}).join('');
  else html += '<div class="link-item no-links">暂无反向链接</div>';
  html += '</div>';

  body.innerHTML = html;
  document.getElementById('detail-header').innerHTML =
    '<h2>'+n.label+'</h2><div class="sub">类型: '+n.type+' · 链接: →'+outLinks.length+' ←'+inLinks.length+'</div>';

  // Focus graph on this note
  renderGraph(id);
}}

function openNote(id) {{
  var n = nodesMap[id];
  if (n && n.file) {{
    // Open note file (works when served via HTTP)
    window.open('/'+n.file, '_blank');
  }}
}}

function focusConnected() {{
  var sel = document.querySelector('.note-item:hover') || document.querySelector('.note-item');
  if (sel) return;
  // zooms in
  svg.transition().duration(300).call(zoom.scaleBy, 1.4);
}}

function resetView() {{
  svg.transition().duration(400).call(zoom.transform, d3.zoomIdentity);
}}

function randomNote() {{
  var nodes = graphData.nodes;
  var pick = nodes[Math.floor(Math.random() * nodes.length)];
  if (pick) selectNote(pick.id);
}}

// ═══ Init ═══
renderNoteList();
renderGraph();
svg.on('click', () => resetView());

window.addEventListener('resize', () => {{
  if (simulation) {{
    var W = document.getElementById('graph-panel').clientWidth;
    var H = document.getElementById('graph-panel').clientHeight;
    simulation.force('center', d3.forceCenter(W/2, H/2)).alpha(0.3).restart();
  }}
}});
</script></body></html>'''
    return html


# ─── Main ───────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Atomic Note → Graph Pipeline")
    parser.add_argument("--search", type=str, help="Search notes for keyword")
    parser.add_argument("--serve", action="store_true", help="Start local HTTP server")
    args = parser.parse_args()

    notes = scan_notes()
    graph = build_graph_json(notes)

    # Save graph JSON
    out_json = SYS / "note_graph.json"
    out_json.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📊 Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges → {out_json.name}")

    # Generate explorer HTML
    d3js = D3JS_PATH.read_text(encoding="utf-8")
    explorer = build_explorer_html(graph, d3js)
    out_html = ROOT / "knowledge-explorer.html"
    out_html.write_text(explorer, encoding="utf-8")
    print(f"🌐 Explorer → {out_html.relative_to(ROOT)}  ({len(explorer)}B)")

    if args.search:
        results = search_notes(notes, args.search)
        print(f"\n🔍 Search results for '{args.search}':")
        for r in results[:10]:
            print(f"  📄 {r['file']} ({r['title']})")
            for m in r['matches'][:3]:
                print(f"     L{m['line']}: {m['snippet'][:80]}")
        print(f"  ({len(results)} files matched)")

    if args.serve:
        import http.server
        PORT = 19801
        Handler = http.server.SimpleHTTPRequestHandler
        Handler.extensions_map.update({'.md':'text/markdown; charset=utf-8'})
        httpd = http.server.HTTPServer(('127.0.0.1', PORT), Handler)
        print(f"\n🚀 Serving notes at http://127.0.0.1:{PORT}/  (Ctrl+C to stop)")
        print(f"   Open http://127.0.0.1:{PORT}/notes/ to browse notes")
        print(f"   Open http://127.0.0.1:{PORT}/knowledge-explorer.html for graph")
        webbrowser.open(f"http://127.0.0.1:{PORT}/knowledge-explorer.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

    print("\n✅ Done")


if __name__ == "__main__":
    main()
