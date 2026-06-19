#!/usr/bin/env python3
"""
元认知挖掘工作流 — Metacognition Miner Workflow
==============================================
整合：AI 深度对话挖掘 + D3.js 力导向图谱可视化
运行后自动打开浏览器，localhost:19800

环境变量：
  DEEPSEEK_API_KEY    DeepSeek API 密钥（可选，也可在设置页面输入）
"""

import http.server
import io
import json
import os
import sys
import threading
import webbrowser
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# 修复 Windows 终端 GBK 编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ─── 配置 ───────────────────────────────────────────
PORT = 19800
HOST = "127.0.0.1"
DATA_DIR = Path(os.environ.get("METACOG_DATA_DIR", Path.home() / ".metacog_miner"))
DATA_FILE = DATA_DIR / "current_session.json"
SKILL_PATH = Path(__file__).parent / "metacog_skill.md"

# ─── 系统提示词（基于 Skill 框架精简版） ─────────────
from cognitive_partner import (
    COGNITIVE_PARTNER_PROMPT,
    handle_suggest_connections,
    handle_remind,
    handle_summarize,
    handle_search,
    get_discovery_question,
    get_writing_suggestion,
)
SYSTEM_PROMPT = """你是一个元认知挖掘 AI。你的任务是通过深度对话，帮助用户将自身的元认知结构外化并可视化。你是认知地形测绘师。

核心原则：
1. 不怕深。问题可以层层递进，追问"为什么"三次以上。
2. 不评价。你标记认知模式，不评判好坏。
3. 结构化输出。每轮对话后，返回更新的图谱 JSON。
4. 溯因推理。当一个信念被识别，追问其来源。
5. 反例优先。每次识别模式后追问"有没有反例"。

分层挖掘框架：
- 第0层：认知基线（思维风格、思考环境、已知/未知）
- 第1层：认知地形图（思考领域、交叉、回避区）
- 第2层：信念体系（核心信念、来源、冲突）
- 第3层：决策模式（典型过程、关键决策回顾）
- 第4层：认知偏差扫描（对照已知偏差库）
- 第5层：元-元认知（审视自省本身）

每次回复末尾，必须用 ```json 代码块输出更新后的图谱数据，格式：
{
  "nodes": [
    {"id":"n1","label":"标签","type":"domain|belief|decision|bias|strategy|emotion|evidence|source|meta","depth":0,"confidence":"certain|likely|speculative","summary":"描述"}
  ],
  "edges": [
    {"source":"n1","target":"n2","type":"supports|conflicts|derives_from|influences|avoids|corrects|questions","label":"关系"}
  ]
}
注意：每次输出的是完整的 nodes 和 edges 数组（包含之前所有已确认的），不要只输出增量。
只挖掘和提问。如果用户说想停止挖掘或切换到其他话题，尊重用户的决定。"""

# ─── HTML 前端模板 ────────────────────────────────────
HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>元认知挖掘工作流</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#0d1117;color:#c9d1d9;display:flex;height:100vh;overflow:hidden}

/* ── 左侧聊天区 ── */
#chat-panel{width:42%;min-width:380px;display:flex;flex-direction:column;background:#161b22;border-right:1px solid #30363d}
#chat-header{padding:16px 20px;border-bottom:1px solid #21262d;display:flex;justify-content:space-between;align-items:center}
#chat-header h1{font-size:16px;color:#f0f6fc}
#chat-header .depth-badge{font-size:11px;background:#21262d;color:#8b949e;padding:4px 10px;border-radius:12px}
.mode-btn{font-size:11px;padding:3px 10px;border-radius:10px;cursor:pointer;background:#21262d;color:#8b949e;border:1px solid transparent}
.mode-btn.active{background:#1f6f3b;color:#e6edf3;border-color:#3fb950}
.mode-btn:hover{opacity:0.8}
#messages{flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:12px}
.msg{max-width:92%;padding:12px 16px;border-radius:10px;font-size:14px;line-height:1.65;white-space:pre-wrap}
.msg.user{align-self:flex-end;background:#1f6f3b;color:#e6edf3}
.msg.ai{align-self:flex-start;background:#21262d;color:#c9d1d9;border:1px solid #30363d}
.msg.system{align-self:center;background:transparent;color:#8b949e;font-size:12px;text-align:center;padding:6px}
.msg .label{font-size:11px;color:#8b949e;margin-bottom:4px;font-weight:600}
.msg.ai .json-block{margin-top:8px;font-size:11px;color:#58a6ff;background:#0d1117;padding:8px;border-radius:6px;overflow-x:auto;max-height:120px;overflow-y:auto;cursor:pointer}

#input-area{padding:12px 16px;border-top:1px solid #21262d;display:flex;gap:8px}
#user-input{flex:1;background:#0d1117;border:1px solid #30363d;border-radius:8px;color:#c9d1d9;padding:10px 14px;font-size:14px;resize:none;outline:none;font-family:inherit}
#user-input:focus{border-color:#58a6ff}
#send-btn{background:#238636;border:none;color:white;border-radius:8px;padding:10px 20px;font-size:14px;cursor:pointer}
#send-btn:hover{background:#2ea043}
#send-btn:disabled{background:#21262d;color:#484f58;cursor:not-allowed}

/* ── 右侧图谱区 ── */
#graph-panel{flex:1;position:relative;background:radial-gradient(ellipse at center, #1a1d27 0%, #0d1117 70%)}
#graph-panel svg{width:100%;height:100%}
#graph-panel .edge{stroke-opacity:0.55;fill:none}
#graph-panel .edge.supports{stroke:#3fb950}
#graph-panel .edge.conflicts{stroke:#f85149}
#graph-panel .edge.derives_from{stroke:#58a6ff}
#graph-panel .edge.influences{stroke:#d2991d}
#graph-panel .edge.avoids{stroke:#484f58;stroke-dasharray:4 3}
#graph-panel .edge.corrects{stroke:#39d353;stroke-dasharray:6 2}
#graph-panel .edge.questions{stroke:#bc8cff;stroke-dasharray:2 4}
#graph-panel .node circle{stroke-width:2.5px;cursor:pointer;transition:r 0.2s}
#graph-panel .node.domain circle{fill:#316dca;stroke:#58a6ff}
#graph-panel .node.belief circle{fill:#9e6a03;stroke:#d2991d}
#graph-panel .node.decision circle{fill:#1f6f3b;stroke:#3fb950}
#graph-panel .node.bias circle{fill:#8b3a3a;stroke:#f85149}
#graph-panel .node.strategy circle{fill:#6e40c9;stroke:#a371f7}
#graph-panel .node.emotion circle{fill:#b0376b;stroke:#f778ba}
#graph-panel .node.evidence circle{fill:#3b5e7a;stroke:#79c0ff}
#graph-panel .node.source circle{fill:#6e4a2e;stroke:#c69052}
#graph-panel .node.meta circle{fill:#4a2d7a;stroke:#bc8cff}
#graph-panel .node text{fill:#c9d1d9;font-size:12px;pointer-events:none;text-anchor:middle}

/* ── 图谱图例 ── */
#legend{position:absolute;top:12px;left:12px;background:rgba(22,27,34,0.93);border:1px solid #30363d;border-radius:8px;padding:10px 14px;font-size:11px;pointer-events:none}
#legend h3{font-size:12px;margin-bottom:6px;color:#8b949e}
#legend .lr{display:flex;align-items:center;margin:3px 0;gap:6px}
#legend .ld{width:9px;height:9px;border-radius:50%;flex-shrink:0}

/* ── 图谱详情弹窗 ── */
#node-tooltip{position:absolute;background:rgba(22,27,34,0.96);border:1px solid #30363d;border-radius:10px;padding:16px;font-size:13px;max-width:300px;display:none;z-index:10}
#node-tooltip h3{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px}
#node-tooltip .tt-title{font-size:16px;color:#f0f6fc;font-weight:600;margin-bottom:6px}
#node-tooltip .tt-summary{color:#c9d1d9;line-height:1.5;margin-bottom:8px}
#node-tooltip .tt-tag{display:inline-block;background:#21262d;border:1px solid #30363d;border-radius:4px;padding:2px 8px;font-size:11px;margin:2px 3px 2px 0}
#node-tooltip .tt-edges{margin-top:8px;font-size:12px;color:#8b949e}

/* ── 工具栏 ── */
#graph-tools{position:absolute;bottom:12px;right:12px;display:flex;gap:6px}
#graph-tools button{background:rgba(22,27,34,0.93);border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:6px 12px;font-size:11px;cursor:pointer}
#graph-tools button:hover{background:#30363d}

/* ── 设置面板 ── */
#settings-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);display:none;justify-content:center;align-items:center;z-index:100}
#settings-panel{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:28px;width:420px}
#settings-panel h2{font-size:18px;color:#f0f6fc;margin-bottom:16px}
#settings-panel label{display:block;font-size:13px;color:#8b949e;margin:12px 0 4px}
#settings-panel input{width:100%;background:#0d1117;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;padding:10px;font-size:13px}
#settings-panel .btns{display:flex;gap:8px;margin-top:20px;justify-content:flex-end}
#settings-panel button{padding:8px 18px;border-radius:6px;font-size:13px;cursor:pointer;border:none}
#settings-panel .btn-save{background:#238636;color:white}
#settings-panel .btn-cancel{background:#21262d;color:#c9d1d9}
</style>
</head>
<body>

<!-- ── 左侧聊天 ── -->
<div id="chat-panel">
  <div id="chat-header">
    <div>
      <h1>🧠 元认知挖掘器</h1>
      <div style="display:flex;gap:4px;margin-top:6px">
        <span class="mode-btn active" data-mode="mine" onclick="switchMode('mine')">⛏️ 挖掘</span>
        <span class="mode-btn" data-mode="partner" onclick="switchMode('partner')">🤖 认知伙伴</span>
      </div>
    </div>
    <span class="depth-badge" id="depth-badge">第 0 层</span>
  </div>
  <div id="messages">
    <div class="msg system">👋 准备好开始挖掘你的元认知了吗？<br>输入"开始"进入第 0 层。</div>
  </div>
  <div id="input-area">
    <textarea id="user-input" rows="2" placeholder="输入你的想法..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendMessage()}"></textarea>
    <button id="send-btn" onclick="sendMessage()">发送</button>
  </div>
</div>

<!-- ── 右侧图谱 ── -->
<div id="graph-panel">
  <svg></svg>
  <div id="legend">
    <h3>节点类型</h3>
    <div class="lr"><span class="ld" style="background:#316dca"></span>领域</div>
    <div class="lr"><span class="ld" style="background:#9e6a03"></span>信念</div>
    <div class="lr"><span class="ld" style="background:#1f6f3b"></span>决策</div>
    <div class="lr"><span class="ld" style="background:#8b3a3a"></span>认知偏差</div>
    <div class="lr"><span class="ld" style="background:#6e40c9"></span>策略</div>
    <div class="lr"><span class="ld" style="background:#b0376b"></span>情绪</div>
    <div class="lr"><span class="ld" style="background:#4a2d7a"></span>元认知</div>
  </div>
  <div id="node-tooltip"></div>
  <div id="graph-tools">
    <button onclick="zoomIn()">🔍+</button>
    <button onclick="zoomOut()">🔍−</button>
    <button onclick="resetZoom()">↺</button>
  </div>
</div>

<!-- ── 设置弹窗 ── -->
<div id="settings-overlay">
  <div id="settings-panel">
    <h2>⚙️ API 设置</h2>
    <label>DeepSeek API Key</label>
    <input id="api-key-input" type="password" placeholder="sk-...">
    <label>Base URL（默认 DeepSeek）</label>
    <input id="base-url-input" value="https://api.deepseek.com">
    <div class="btns">
      <button class="btn-cancel" onclick="closeSettings()">取消</button>
      <button class="btn-save" onclick="saveSettings()">保存</button>
    </div>
  </div>
</div>

<script>
// ═══════════════════════════════════════
//  前端状态
// ═══════════════════════════════════════
let graphData = {nodes:[],edges:[]};
let currentDepth = 0;
let isWaiting = false;

// ─── 聊天 ───
const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const depthBadge = document.getElementById('depth-badge');

function addMessage(role, text, extra) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  if (role === 'ai') {
    div.innerHTML = '<div class="label">🤖 挖掘 AI</div>' + escapeHtml(text);
  } else if (role === 'user') {
    div.innerHTML = '<div class="label">你</div>' + escapeHtml(text);
  } else {
    div.textContent = text;
  }
  if (extra) div.appendChild(extra);
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

async function sendMessage() {
  if (isWaiting) return;
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = '';
  isWaiting = true;
  sendBtn.disabled = true;

  addMessage('user', text);
  addMessage('system', '⏳ 思考中...');

  try {
    const apiKey = localStorage.getItem('mc_api_key') || '';
    const baseUrl = localStorage.getItem('mc_base_url') || '';
    const headers = {'Content-Type':'application/json'};
    if(apiKey) headers['X-Api-Key'] = apiKey;
    if(baseUrl) headers['X-Base-Url'] = baseUrl;
    const resp = await fetch('/api/chat', {
      method:'POST',
      headers: headers,
      body: JSON.stringify({message:text, graph:graphData})
    });
    const data = await resp.json();
    // 移除"思考中"
    const last = messagesEl.lastChild;
    if (last && last.className.includes('system')) last.remove();

    addMessage('ai', data.reply);

    // 更新图谱
    if (data.graph && data.graph.nodes) {
      graphData = data.graph;
      currentDepth = data.depth || currentDepth;
      depthBadge.textContent = '第 ' + currentDepth + ' 层';
      renderGraph(graphData);
    }
  } catch(e) {
    const last = messagesEl.lastChild;
    if (last && last.className.includes('system')) last.remove();
    addMessage('system', '❌ 连接失败: ' + e.message + '。请确认后端服务在运行。');
  }
  isWaiting = false;
  sendBtn.disabled = false;
  inputEl.focus();
}

// ─── D3.js 图谱 ───
const graphPanel = document.getElementById('graph-panel');
const svg = d3.select('#graph-panel svg');
const g = svg.append('g');
const zoom = d3.zoom().scaleExtent([0.15,6]).on('zoom', e => g.attr('transform', e.transform));
svg.call(zoom);
let simulation;

const nodeColors = {
  domain:{fill:'#316dca',stroke:'#58a6ff'}, belief:{fill:'#9e6a03',stroke:'#d2991d'},
  decision:{fill:'#1f6f3b',stroke:'#3fb950'}, bias:{fill:'#8b3a3a',stroke:'#f85149'},
  strategy:{fill:'#6e40c9',stroke:'#a371f7'}, emotion:{fill:'#b0376b',stroke:'#f778ba'},
  evidence:{fill:'#3b5e7a',stroke:'#79c0ff'}, source:{fill:'#6e4a2e',stroke:'#c69052'},
  meta:{fill:'#4a2d7a',stroke:'#bc8cff'}
};
const typeLabels = {domain:'领域',belief:'信念',decision:'决策',bias:'认知偏差',strategy:'策略',emotion:'情绪',evidence:'证据',source:'来源',meta:'元认知'};
const relLabels = {supports:'支持',conflicts:'冲突',derives_from:'来源',influences:'影响',avoids:'回避',corrects:'纠正',questions:'质疑'};

function nodeRadius(d) {
  const map = {domain:14,belief:12,decision:11,bias:10,strategy:9,emotion:8,evidence:7,source:7,meta:11};
  return map[d.type]||8;
}

function renderGraph(data) {
  g.selectAll('*').remove();
  const nodes = data.nodes.map(n=>({...n}));
  const edges = data.edges.map(e=>({...e}));

  const link = g.append('g').selectAll('line').data(edges).join('line')
    .attr('class',d=>'edge '+(d.type||'influences'))
    .attr('stroke-width',d=>{const w={supports:2.2,conflicts:2.8,derives_from:1.8,influences:2,avoids:1.2,corrects:2.4,questions:2};return w[d.type]||1.5});

  const node = g.append('g').selectAll('g').data(nodes).join('g')
    .attr('class',d=>'node '+(d.type||'domain'))
    .call(d3.drag()
      .on('start',(e,d)=>{if(!e.active)simulation.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y;})
      .on('drag',(e,d)=>{d.fx=e.x;d.fy=e.y;})
      .on('end',(e,d)=>{if(!e.active)simulation.alphaTarget(0);d.fx=null;d.fy=null;})
    )
    .on('click',(e,d)=>{e.stopPropagation();showTooltip(d,edges,nodes,e);});

  node.append('circle').attr('r',nodeRadius)
    .on('mouseenter',function(e,d){d3.select(this).transition().duration(150).attr('r',nodeRadius(d)+4);})
    .on('mouseleave',function(e,d){d3.select(this).transition().duration(150).attr('r',nodeRadius(d));});

  node.append('text').text(d=>d.label).attr('dy',d=>nodeRadius(d)+14);

  const W = graphPanel.clientWidth, H = graphPanel.clientHeight;
  simulation = d3.forceSimulation(nodes)
    .force('link',d3.forceLink(edges).id(d=>d.id).distance(140))
    .force('charge',d3.forceManyBody().strength(-380))
    .force('center',d3.forceCenter(W/2,H/2))
    .force('collision',d3.forceCollide().radius(d=>nodeRadius(d)+16))
    .on('tick',()=>{
      link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
      node.attr('transform',d=>`translate(${d.x},${d.y})`);
    });
}

function showTooltip(d, edges, nodes, event) {
  const tip = document.getElementById('node-tooltip');
  const relEdges = edges.filter(e=>(e.source.id||e.source)===d.id || (e.target.id||e.target)===d.id);
  let html = `<h3>${typeLabels[d.type]||d.type}</h3>`;
  html += `<div class="tt-title">${d.label}</div>`;
  if(d.summary) html += `<div class="tt-summary">${d.summary}</div>`;
  if(d.confidence) html += `<span class="tt-tag">${d.confidence}</span>`;
  html += `<span class="tt-tag">深度 ${d.depth||0}</span>`;
  if(relEdges.length) {
    html += `<div class="tt-edges">关联 ${relEdges.length} 条：`;
    relEdges.forEach(e=>{
      const other = (e.source.id||e.source)===d.id ? (e.target.id||e.target) : (e.source.id||e.source);
      const rn = nodes.find(n=>n.id===other);
      html += `<br> ${(e.source.id||e.source)===d.id?'→':'←'} ${rn?rn.label:other} (${relLabels[e.type]||e.type})`;
    });
    html += '</div>';
  }
  tip.innerHTML = html;
  tip.style.display = 'block';
  const rect = graphPanel.getBoundingClientRect();
  tip.style.left = Math.min(event.clientX-rect.left+12, rect.width-310)+'px';
  tip.style.top = Math.min(event.clientY-rect.top-10, rect.height-200)+'px';
}

svg.on('click',()=>{document.getElementById('node-tooltip').style.display='none';});
window.addEventListener('resize',()=>{
  if(simulation){const W=graphPanel.clientWidth,H=graphPanel.clientHeight;simulation.force('center',d3.forceCenter(W/2,H/2));simulation.alpha(0.3).restart();}
});
function zoomIn(){svg.transition().duration(300).call(zoom.scaleBy,1.4);}
function zoomOut(){svg.transition().duration(300).call(zoom.scaleBy,0.7);}
function resetZoom(){svg.transition().duration(400).call(zoom.transform,d3.zoomIdentity);}

// ─── 设置 ───
function openSettings(){document.getElementById('settings-overlay').style.display='flex';}
function closeSettings(){document.getElementById('settings-overlay').style.display='none';}
function saveSettings(){
  const key = document.getElementById('api-key-input').value.trim();
  const base = document.getElementById('base-url-input').value.trim();
  if(key) localStorage.setItem('mc_api_key', key);
  if(base) localStorage.setItem('mc_base_url', base);
  closeSettings();
  addMessage('system','✅ 设置已保存。');
}
// 加载设置
(function(){
  const key = localStorage.getItem('mc_api_key');
  const base = localStorage.getItem('mc_base_url');
  if(key) document.getElementById('api-key-input').value = key;
  if(base) document.getElementById('base-url-input').value = base;
})();

// Ctrl+, 打开设置
document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.key===','){e.preventDefault();openSettings();}});

// ═══════════════════════════════════════
//  认知伙伴模式 (Cognitive Partner)
// ═══════════════════════════════════════
let currentMode = 'mine'; // 'mine' | 'partner'

function switchMode(mode) {
  currentMode = mode;
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  if (mode === 'partner') {
    addMessage('system', '🤖 认知伙伴模式已激活。我会提问、建议关联、提醒你回访旧笔记。');
    // Trigger a discovery question
    fetchDiscoveryQuestion();
  } else {
    addMessage('system', '⛏️ 切换回元认知挖掘模式。');
  }
}

async function fetchDiscoveryQuestion() {
  try {
    const resp = await fetch('/api/cognitive/question');
    const data = await resp.json();
    if (data && data.question) {
      addMessage('ai', '💡 **发现惊喜**\n\n' + data.question);
    }
  } catch(e) {
    // silent fail — not critical
  }
}

async function triggerReminder() {
  try {
    const resp = await fetch('/api/cognitive/remind');
    const data = await resp.json();
    let msg = '';
    if (data.writing_suggestion && data.writing_suggestion.length > 0) {
      msg += '🌊 **写作建议**\n\n';
      data.writing_suggestion.forEach(s => {
        msg += s.prompt + '\n\n';
      });
    }
    if (data.reminder && data.reminder.prompt) {
      msg += '⏰ **反刍提醒**\n\n' + data.reminder.prompt;
    }
    if (data.discovery_question && data.discovery_question.question) {
      msg += '\n\n✨ **隐藏关联**\n\n' + data.discovery_question.question;
    }
    if (msg) addMessage('ai', msg);
  } catch(e) {}
}

async function triggerSuggestions() {
  try {
    const resp = await fetch('/api/cognitive/suggest');
    const data = await resp.json();
    if (data && data.suggestions && data.suggestions.length > 0) {
      let msg = '🔗 **建议建立连接**\n\n';
      data.suggestions.forEach(s => {
        msg += `「${s.a.label}」↔「${s.b.label}」\n`;
        msg += `   ${s.reason}（强度: ${s.strength}/10）\n\n`;
      });
      addMessage('ai', msg);
    }
  } catch(e) {}
}

// Add cognitive partner button to input area
(function() {
  const inputArea = document.getElementById('input-area');
  const extraBtns = document.createElement('div');
  extraBtns.style.cssText = 'display:flex;gap:4px;margin-top:6px';
  extraBtns.innerHTML = `
    <button style="background:#21262d;border:1px solid #30363d;color:#8b949e;border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer" onclick="triggerReminder()">⏰ 反刍</button>
    <button style="background:#21262d;border:1px solid #30363d;color:#8b949e;border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer" onclick="triggerSuggestions()">🔗 发现</button>
  `;
  inputArea.appendChild(extraBtns);
})();
</script>
</body>
</html>'''

# ─── LLM 集成 ───────────────────────────────────────
import requests

def call_deepseek_api(user_message, graph_data, api_key=None, base_url=None):
    """调用 DeepSeek API 进行元认知挖掘对话"""
    if not api_key:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not base_url:
        base_url = "https://api.deepseek.com"

    if not api_key:
        return None, "⚠️ 未配置 API Key。请按 Ctrl+, 打开设置输入 DeepSeek API Key，或设置环境变量 DEEPSEEK_API_KEY。"

    # 构建消息
    graph_json = json.dumps(graph_data, ensure_ascii=False, indent=2) if graph_data.get("nodes") else "{}"
    context = f"当前图谱数据：\n```json\n{graph_json}\n```\n请基于此继续挖掘。"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": context + "\n\n用户说：" + user_message}
    ]

    try:
        resp = requests.post(
            f"{base_url.rstrip('/')}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            timeout=120
        )
        if resp.status_code != 200:
            return None, f"API 错误 ({resp.status_code}): {resp.text[:300]}"

        content = resp.json()["choices"][0]["message"]["content"]
        return parse_ai_response(content, graph_data)

    except requests.exceptions.ConnectionError:
        return None, "❌ 无法连接到 API 服务器。请检查 Base URL 和网络连接。"
    except Exception as e:
        return None, f"❌ 调用失败: {str(e)}"


def parse_ai_response(content, old_graph):
    """从 AI 回复中提取文本和图谱 JSON"""
    # 尝试提取 JSON 代码块
    text_parts = []
    graph_json = None

    import re
    # 匹配 ```json ... ``` 代码块
    pattern = r'```json\s*\n(.*?)\n```'
    matches = list(re.finditer(pattern, content, re.DOTALL))

    if matches:
        # 取最后一个 JSON 块作为图谱数据
        last_match = matches[-1]
        try:
            graph_json = json.loads(last_match.group(1))
        except json.JSONDecodeError:
            pass
        # 移除 JSON 块得到纯文本
        text = content[:last_match.start()] + content[last_match.end():]
        text = text.strip()
    else:
        text = content

    # 如果没有提取到图谱，保留旧图谱
    if not graph_json or "nodes" not in graph_json:
        graph_json = old_graph

    # 估算当前深度
    nodes = graph_json.get("nodes", [])
    depth = max((n.get("depth", 0) for n in nodes), default=0) if nodes else 0

    return text, graph_json, depth


def get_fallback_reply(user_message, graph_data):
    """无 API 时的后备回复（基于规则）"""
    msg = user_message.strip().lower()
    nodes = graph_data.get("nodes", [])
    depth = max((n.get("depth", 0) for n in nodes), default=0) if nodes else 0

    if msg in ["开始", "start", "go", "好", "好的", "ok", "可以", "来吧"]:
        return (
            "很好，让我们从第 0 层开始——认知基线。\n\n"
            "**第 1 个问题**：用三个词描述你的思维风格。\n"
            "比如：分析型、直觉型、发散型、系统型、跳跃型、实用型……你觉得自己最接近哪种组合？",
            {"nodes": [
                {"id":"n_start","label":"元认知基线","type":"meta","depth":0,"confidence":"certain","summary":"挖掘起点"}
            ], "edges": []},
            0
        )

    # 简单的模式匹配
    if depth <= 0:
        return (
            "收到。让我们继续建立认知基线。\n\n"
            "**下一个问题**：什么时候你觉得'自己在思考'最清晰？\n"
            "什么环境、什么时间段、什么状态下你的思维质量最高？",
            graph_data, 0
        )

    return (
        "我收到了你的消息。不过为了做更深度的挖掘，建议配置 DeepSeek API Key（按 Ctrl+, 打开设置）。\n\n"
        "在没有 AI 的情况下，我可以继续按框架提问：\n"
        "**当前进度**：已挖掘到第 {} 层，共 {} 个节点。\n\n"
        "你想继续挖掘哪个方面？信念体系、决策模式、还是认知偏差扫描？".format(depth, len(nodes)),
        graph_data, depth
    )

# ─── HTTP 请求处理 ────────────────────────────────
class MetacogHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/' or parsed.path == '/index.html':
            self._serve_html()
        elif parsed.path == '/api/data':
            self._serve_json(load_data())
        elif parsed.path == '/api/settings':
            self._serve_json({"has_key": bool(os.environ.get("DEEPSEEK_API_KEY",""))})
        elif parsed.path == '/api/cognitive/suggest':
            params = parse_qs(parsed.query)
            self._serve_json(handle_suggest_connections(params))
        elif parsed.path == '/api/cognitive/remind':
            self._serve_json(handle_remind())
        elif parsed.path == '/api/cognitive/summarize':
            params = parse_qs(parsed.query)
            self._serve_json(handle_summarize(params))
        elif parsed.path == '/api/cognitive/search':
            params = parse_qs(parsed.query)
            self._serve_json(handle_search(params))
        elif parsed.path == '/api/cognitive/question':
            self._serve_json(get_discovery_question() or {})
        elif parsed.path == '/api/cognitive/writing-suggestion':
            self._serve_json(get_writing_suggestion() or [])
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length else b'{}'
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        if parsed.path == '/api/chat':
            self._handle_chat(data)
        elif parsed.path == '/api/save':
            save_data(data.get('graph', {}))
            self._serve_json({"status":"ok"})
        else:
            self.send_error(404)

    def _serve_html(self):
        body = HTML_TEMPLATE.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_json(self, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_chat(self, data):
        user_msg = data.get('message', '')
        old_graph = data.get('graph', {'nodes':[], 'edges':[]})

        # 尝试从请求头中获取 API key（前端可以传）
        api_key = self.headers.get('X-Api-Key', '') or os.environ.get('DEEPSEEK_API_KEY', '')
        base_url = self.headers.get('X-Base-Url', '') or 'https://api.deepseek.com'

        # 如果前端在 localStorage 存了 key，前端会通过请求头传递
        # 这里先用环境变量，后续前端逻辑完善后再支持

        reply, graph, depth = get_fallback_reply(user_msg, old_graph)

        # 尝试调用 AI（如果有 key）
        if api_key:
            ai_reply, ai_graph, ai_depth = call_deepseek_api(user_msg, old_graph, api_key, base_url)
            if ai_reply:
                reply, graph, depth = ai_reply, ai_graph, ai_depth

        # 保存当前图谱
        save_data(graph)

        self._serve_json({
            "reply": reply,
            "graph": graph,
            "depth": depth
        })

    def log_message(self, format, *args):
        # 精简日志
        pass


# ─── 数据持久化 ───────────────────────────────────
def load_data():
    try:
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {"nodes": [], "edges": []}

def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


# ─── 主入口 ───────────────────────────────────────
def main():
    print("=" * 60)
    print("  🧠 元认知挖掘工作流  v1.0")
    print("  Metacognition Miner Workflow")
    print("=" * 60)
    print()
    print(f"  服务地址: http://{HOST}:{PORT}")
    print(f"  数据目录: {DATA_DIR}")
    print()
    print("  提示:")
    print("  - 浏览器会自动打开")
    print("  - 按 Ctrl+, 打开 API 设置")
    print("  - 设置 DEEPSEEK_API_KEY 环境变量或输入 API Key")
    print("  - 关闭此窗口即可停止服务")
    print()

    # 启动服务器
    server = http.server.HTTPServer((HOST, PORT), MetacogHandler)

    # 延迟打开浏览器（可选，失败不影响主服务）
    def open_browser():
        time.sleep(1.5)
        try:
            webbrowser.open(f"http://{HOST}:{PORT}")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
        server.shutdown()


if __name__ == "__main__":
    main()
