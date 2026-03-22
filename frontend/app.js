/* ============================================================
   Hire AI Agents — Frontend Demo
   Self-contained SPA that works in mock mode (no backend)
   or connects to a real FastAPI backend.
   ============================================================ */

// ── State ─────────────────────────────────────────────────
const state = {
  apiBase: null,          // null = mock mode
  agents: [],
  tasks: [],
  results: [],
  demoAgentId: null,
  demoTaskId: null,
};

// ── Mock data helpers ──────────────────────────────────────
let _idCounter = 1000;
function mockId() { return 'mock-' + (++_idCounter); }
function now() { return new Date().toISOString(); }

const SEED_AGENTS = [
  {
    id: 'agent-trans', name: 'TranslationAgent',
    description: 'Translates text between languages.',
    endpoint_url: 'http://mock-agent:8001',
    capabilities: ['translate_text'],
    price_per_request: 0.05, avg_latency_ms: 500, success_rate: 0.98,
    task_count: 12, is_active: true, created_at: now(),
  },
  {
    id: 'agent-summ', name: 'SummarizationAgent',
    description: 'Summarizes long documents into concise bullets.',
    endpoint_url: 'http://mock-agent:8001',
    capabilities: ['summarize_text'],
    price_per_request: 0.10, avg_latency_ms: 820, success_rate: 0.95,
    task_count: 7, is_active: true, created_at: now(),
  },
  {
    id: 'agent-class', name: 'ClassificationAgent',
    description: 'Classifies text into predefined categories.',
    endpoint_url: 'http://mock-agent:8001',
    capabilities: ['classify_text'],
    price_per_request: 0.03, avg_latency_ms: 200, success_rate: 0.99,
    task_count: 34, is_active: true, created_at: now(),
  },
];

const SEED_TASKS = [
  {
    id: 'task-1', creator_agent_id: null,
    required_capability: 'translate_text',
    payload: { text: 'Good morning', target_language: 'fr' },
    budget: 0.50, deadline: null, status: 'completed',
    assigned_agent_id: 'agent-trans', created_at: now(), updated_at: now(),
  },
  {
    id: 'task-2', creator_agent_id: 'agent-summ',
    required_capability: 'summarize_text',
    payload: { text: 'Long article text here…' },
    budget: 1.00, deadline: null, status: 'matched',
    assigned_agent_id: 'agent-summ', created_at: now(), updated_at: now(),
  },
  {
    id: 'task-3', creator_agent_id: null,
    required_capability: 'classify_text',
    payload: { text: 'The product is excellent!', categories: ['positive','negative','neutral'] },
    budget: 0.10, deadline: null, status: 'open',
    assigned_agent_id: null, created_at: now(), updated_at: now(),
  },
];

const SEED_RESULTS = [
  {
    id: 'result-1', task_id: 'task-1', agent_id: 'agent-trans',
    success: true, latency_ms: 482,
    result_payload: { translated_text: 'Bonjour' },
    error_message: null, created_at: now(),
  },
];

// ── Mock API layer ─────────────────────────────────────────
// All mock calls return promises to simulate network round-trips

const mockApi = {
  async getAgents() { return [...state.agents]; },
  async getAgent(id) { return state.agents.find(a => a.id === id) || null; },
  async createAgent(data) {
    const agent = {
      id: mockId(), task_count: 0, is_active: true, created_at: now(),
      success_rate: 1.0, avg_latency_ms: 0, price_per_request: 0,
      capabilities: [], description: '', ...data,
    };
    state.agents.push(agent);
    return agent;
  },
  async updateAgent(id, data) {
    const idx = state.agents.findIndex(a => a.id === id);
    if (idx === -1) throw new Error('Agent not found');
    state.agents[idx] = { ...state.agents[idx], ...data };
    return state.agents[idx];
  },
  async deleteAgent(id) {
    const idx = state.agents.findIndex(a => a.id === id);
    if (idx !== -1) state.agents[idx].is_active = false;
  },

  async getTasks()  { return [...state.tasks]; },
  async getTask(id) { return state.tasks.find(t => t.id === id) || null; },
  async createTask(data) {
    const task = {
      id: mockId(), status: 'open', assigned_agent_id: null,
      created_at: now(), updated_at: now(), payload: {}, budget: null,
      deadline: null, creator_agent_id: null, ...data,
    };
    state.tasks.push(task);
    return task;
  },
  async matchTask(taskId) {
    const task = state.tasks.find(t => t.id === taskId);
    if (!task) throw new Error('Task not found');
    if (task.status !== 'open') throw new Error(`Task is '${task.status}', expected 'open'`);

    // Matching engine (mirrors backend logic)
    let candidates = state.agents.filter(a =>
      a.is_active && a.capabilities.includes(task.required_capability)
    );
    if (task.budget != null) {
      candidates = candidates.filter(a => a.price_per_request <= task.budget);
    }
    if (!candidates.length) throw new Error('No suitable agent found for this task');

    candidates.sort((a, b) =>
      (b.success_rate - a.success_rate) ||
      (a.price_per_request - b.price_per_request) ||
      (a.avg_latency_ms - b.avg_latency_ms)
    );
    task.assigned_agent_id = candidates[0].id;
    task.status = 'matched';
    task.updated_at = now();
    return task;
  },
  async executeTask(taskId) {
    const task = state.tasks.find(t => t.id === taskId);
    if (!task) throw new Error('Task not found');
    if (task.status !== 'matched') throw new Error(`Task is '${task.status}', expected 'matched'`);

    task.status = 'running';
    task.updated_at = now();

    // Simulate agent call
    await sleep(800);

    const agent = state.agents.find(a => a.id === task.assigned_agent_id);
    const latency = Math.round(200 + Math.random() * 800);
    const success = Math.random() < (agent ? agent.success_rate : 0.9);

    let resultPayload = null;
    let errorMsg = null;

    if (success) {
      resultPayload = mockCapabilityResult(task.required_capability, task.payload);
      task.status = 'completed';
    } else {
      errorMsg = 'Simulated execution failure';
      task.status = 'failed';
    }
    task.updated_at = now();

    // Store result
    const result = {
      id: mockId(), task_id: task.id,
      agent_id: task.assigned_agent_id,
      success, latency_ms: latency,
      result_payload: resultPayload,
      error_message: errorMsg,
      created_at: now(),
    };
    state.results.push(result);

    // Update agent reputation
    if (agent) {
      const prev = agent.task_count;
      agent.task_count = prev + 1;
      agent.success_rate = (agent.success_rate * prev + (success ? 1 : 0)) / agent.task_count;
      agent.avg_latency_ms = (agent.avg_latency_ms * prev + latency) / agent.task_count;
    }

    return { success, result: resultPayload, error: errorMsg, latency_ms: latency, task_status: task.status };
  },
  async getResults(taskId) {
    return state.results.filter(r => r.task_id === taskId);
  },
  async getAllResults() { return [...state.results]; },
};

function mockCapabilityResult(cap, payload) {
  if (cap === 'translate_text') {
    const tgt = payload.target_language || 'de';
    const sourceText = typeof payload.text === 'string' && payload.text ? payload.text : 'Hello world';
    const translations = { de: 'Hallo Welt', fr: 'Bonjour le monde', es: 'Hola mundo', it: 'Ciao mondo', ja: 'こんにちは世界' };
    return { translated_text: translations[tgt] || `[${tgt.toUpperCase()}] ${sourceText}` };
  }
  if (cap === 'summarize_text') {
    const text = payload.text || '';
    return { summary: text.slice(0, 80) + (text.length > 80 ? '...' : ''), original_length: text.length };
  }
  if (cap === 'classify_text') {
    const cats = payload.categories || ['positive', 'negative', 'neutral'];
    return { label: cats[0], confidence: 0.91 };
  }
  return { echo: payload };
}

// ── Real API layer ─────────────────────────────────────────
const realApi = {
  async req(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const r = await fetch(state.apiBase + path, opts);
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }
    if (r.status === 204) return null;
    return r.json();
  },
  async getAgents()          { return this.req('GET', '/agents'); },
  async getAgent(id)         { return this.req('GET', `/agents/${id}`); },
  async createAgent(d)       { return this.req('POST', '/agents', d); },
  async updateAgent(id, d)   { return this.req('PATCH', `/agents/${id}`, d); },
  async deleteAgent(id)      { return this.req('DELETE', `/agents/${id}`); },
  async getTasks()            { return this.req('GET', '/tasks'); },
  async getTask(id)           { return this.req('GET', `/tasks/${id}`); },
  async createTask(d)         { return this.req('POST', '/tasks', d); },
  async matchTask(id)         { return this.req('POST', `/tasks/${id}/match`); },
  async executeTask(id)       { return this.req('POST', `/tasks/${id}/execute`); },
  async getResults(taskId)    { return this.req('GET', `/tasks/${taskId}/results`); },
  async getAllResults() {
    const tasks = await this.getTasks();
    const all = await Promise.all(tasks.map(t => this.getResults(t.id)));
    return all.flat();
  },
};

// Active API (mock or real)
const api = new Proxy({}, {
  get(_, key) {
    return state.apiBase ? realApi[key].bind(realApi) : mockApi[key].bind(mockApi);
  }
});

// ── Helpers ────────────────────────────────────────────────
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function fmt(v, decimals = 2) {
  if (v == null) return '—';
  return Number(v).toFixed(decimals);
}

function shortId(id) {
  if (!id) return '';
  return id.length > 14 ? id.slice(0, 7) + '…' + id.slice(-4) : id;
}

function agentName(id) {
  const a = state.agents.find(a => a.id === id);
  return a ? a.name : shortId(id);
}

function capEmoji(cap) {
  if (cap.includes('translat')) return '🌐';
  if (cap.includes('summar'))   return '📝';
  if (cap.includes('classif'))  return '🏷️';
  return '⚡';
}

// ── Toast ──────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  el.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${msg}</span>`;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => {
    el.style.animation = 'fadeOut .3s ease forwards';
    setTimeout(() => el.remove(), 300);
  }, 3500);
}

// ── Tab routing ────────────────────────────────────────────
const TAB_TITLES = { demo: 'Demo Flow', agents: 'Agent Registry', tasks: 'Task Board', results: 'Execution Results' };

function showTab(name) {
  document.querySelectorAll('.nav-item').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `tab-${name}`));
  document.getElementById('topbar-title').textContent = TAB_TITLES[name] || name;
}

// ── Render agents ──────────────────────────────────────────
function renderAgents() {
  const grid = document.getElementById('agents-grid');
  const count = state.agents.length;
  document.getElementById('agents-count').textContent = count;
  document.getElementById('agent-registry-count').textContent = `${count} agent${count !== 1 ? 's' : ''}`;

  if (!count) {
    grid.innerHTML = '<div class="empty-state">No agents registered yet. Click "Register Agent" to add one.</div>';
    return;
  }

  grid.innerHTML = state.agents.map(a => {
    const srClass = a.success_rate >= 0.95 ? 'good' : (a.success_rate >= 0.8 ? 'warn' : '');
    return `
    <div class="agent-card ${a.is_active ? '' : 'inactive'}">
      <div class="agent-card-header">
        <div class="agent-avatar">${capEmoji(a.capabilities[0] || '')}</div>
        <div class="agent-card-title">
          <div class="agent-name">${a.name}</div>
          <div class="agent-desc">${a.description || 'No description'}</div>
        </div>
        <span class="active-badge ${a.is_active ? '' : 'off'}">${a.is_active ? 'active' : 'inactive'}</span>
      </div>
      <div class="caps-list">
        ${a.capabilities.map(c => `<span class="cap-badge">${c}</span>`).join('')}
      </div>
      <div class="agent-metrics">
        <div class="metric">
          <div class="metric-value ${srClass}">${Math.round(a.success_rate * 100)}%</div>
          <div class="metric-label">Success</div>
        </div>
        <div class="metric">
          <div class="metric-value">${Math.round(a.avg_latency_ms)}ms</div>
          <div class="metric-label">Latency</div>
        </div>
        <div class="metric">
          <div class="metric-value">$${fmt(a.price_per_request, 2)}</div>
          <div class="metric-label">Price</div>
        </div>
      </div>
      <div class="agent-card-footer">
        <span>${a.task_count} task${a.task_count !== 1 ? 's' : ''} completed</span>
        <span title="${a.endpoint_url}" style="cursor:help;color:var(--accent-h);font-size:11px">endpoint ↗</span>
      </div>
    </div>`;
  }).join('');
}

// ── Render tasks ───────────────────────────────────────────
function renderTasks() {
  const count = state.tasks.length;
  document.getElementById('tasks-count').textContent = count;
  document.getElementById('task-board-count').textContent = `${count} task${count !== 1 ? 's' : ''}`;

  ['open','matched','running','completed','failed'].forEach(status => {
    const col = document.getElementById(`cards-${status}`);
    const items = state.tasks.filter(t => t.status === status);
    if (!items.length) {
      col.innerHTML = `<div style="font-size:12px;color:var(--text-dim);padding:8px 2px;">Empty</div>`;
      return;
    }
    col.innerHTML = items.map(t => `
      <div class="task-card">
        <div class="task-card-cap">${t.required_capability}</div>
        <div class="task-card-id">#${shortId(t.id)}</div>
        ${t.budget != null ? `<div class="task-card-budget">Budget: $${fmt(t.budget, 2)}</div>` : ''}
        ${t.assigned_agent_id ? `<div class="task-card-agent">→ ${agentName(t.assigned_agent_id)}</div>` : ''}
      </div>
    `).join('');
  });
}

// ── Render results ─────────────────────────────────────────
function renderResults() {
  const list = document.getElementById('results-list');
  const all = [...state.results].reverse();
  if (!all.length) {
    list.innerHTML = '<div class="empty-state">No results yet. Run the demo flow or execute a task.</div>';
    return;
  }
  list.innerHTML = all.map(r => {
    const task = state.tasks.find(t => t.id === r.task_id);
    const cap = task ? task.required_capability : r.task_id;
    return `
    <div class="result-row">
      <div class="result-status-icon">${r.success ? '✅' : '❌'}</div>
      <div class="result-info">
        <div class="result-title">${cap}</div>
        <div class="result-meta">
          Agent: <strong>${agentName(r.agent_id)}</strong> &nbsp;·&nbsp;
          Task: ${shortId(r.task_id)} &nbsp;·&nbsp;
          ${new Date(r.created_at).toLocaleTimeString()}
        </div>
        ${r.result_payload ? `<div class="result-payload">${JSON.stringify(r.result_payload, null, 2)}</div>` : ''}
        ${r.error_message ? `<div style="font-size:12px;color:var(--danger);margin-top:6px;">Error: ${r.error_message}</div>` : ''}
      </div>
      <div class="result-latency"><span class="ms-val">${r.latency_ms}</span> ms</div>
    </div>`;
  }).join('');
}

// ── Refresh all views ──────────────────────────────────────
function refresh() {
  renderAgents();
  renderTasks();
  renderResults();
}

// ── Demo flow ──────────────────────────────────────────────
function setStepState(n, state_) {
  const el = document.getElementById(`step-${n}`);
  const badge = el.querySelector('.step-status-badge');
  const btn   = document.getElementById(`step-${n}-btn`);
  el.classList.remove('locked', 'active', 'done');
  el.classList.add(state_ === 'done' ? 'done' : state_ === 'running' ? 'active' : '');
  badge.className = `step-status-badge ${state_}`;
  badge.textContent = state_;
  if (btn) btn.disabled = (state_ === 'done' || state_ === 'running' || state_ === 'locked');
}

function setStepResult(n, html, type = 'success') {
  const el = document.getElementById(`step-${n}-result`);
  el.className = `step-result ${type}`;
  el.innerHTML = html;
  el.style.display = 'block';
}

function unlockStep(n) {
  const el = document.getElementById(`step-${n}`);
  el.classList.remove('locked');
  const btn = document.getElementById(`step-${n}-btn`);
  if (btn) btn.disabled = false;
  setStepState(n, 'pending');
}

async function runStep1() {
  setStepState(1, 'running');
  await sleep(600);
  try {
    const agent = await api.createAgent({
      name: 'TranslationAgent',
      description: 'Translates text between languages.',
      endpoint_url: 'http://mock-agent:8001',
      capabilities: ['translate_text'],
      price_per_request: 0.05,
      avg_latency_ms: 500,
      success_rate: 0.98,
    });
    state.demoAgentId = agent.id;
    // Sync state from real API
    if (state.apiBase) {
      state.agents = await api.getAgents();
    }
    refresh();
    setStepState(1, 'done');
    setStepResult(1, `
      <strong>✓ Agent registered</strong><br/>
      id: <code>${agent.id}</code><br/>
      name: <code>${agent.name}</code><br/>
      capabilities: <code>${agent.capabilities.join(', ')}</code>
    `);
    unlockStep(2);
    toast('TranslationAgent registered', 'success');
  } catch (e) {
    setStepState(1, 'failed');
    setStepResult(1, `✕ ${e.message}`, 'error');
    toast(e.message, 'error');
  }
}

async function runStep2() {
  setStepState(2, 'running');
  await sleep(400);
  try {
    const task = await api.createTask({
      required_capability: 'translate_text',
      payload: { text: 'Hello world', source_language: 'en', target_language: 'de' },
      budget: 1.00,
    });
    state.demoTaskId = task.id;
    if (state.apiBase) state.tasks = await api.getTasks();
    refresh();
    setStepState(2, 'done');
    setStepResult(2, `
      <strong>✓ Task created</strong><br/>
      id: <code>${task.id}</code><br/>
      status: <code>${task.status}</code><br/>
      capability: <code>${task.required_capability}</code>
    `);
    unlockStep(3);
    toast('Task created', 'success');
  } catch (e) {
    setStepState(2, 'failed');
    setStepResult(2, `✕ ${e.message}`, 'error');
    toast(e.message, 'error');
  }
}

async function runStep3() {
  setStepState(3, 'running');
  await sleep(500);
  try {
    const task = await api.matchTask(state.demoTaskId);
    if (state.apiBase) { state.tasks = await api.getTasks(); state.agents = await api.getAgents(); }
    refresh();
    setStepState(3, 'done');
    const matched_agent = state.agents.find(a => a.id === task.assigned_agent_id) ||
                          { name: shortId(task.assigned_agent_id) };
    setStepResult(3, `
      <strong>✓ Task matched</strong><br/>
      status: <code>${task.status}</code><br/>
      assigned_agent: <code>${matched_agent.name}</code> (${shortId(task.assigned_agent_id)})<br/>
      ranking: success_rate ↓ → price ↑ → latency ↑
    `);
    unlockStep(4);
    toast(`Matched to ${matched_agent.name}`, 'success');
  } catch (e) {
    setStepState(3, 'failed');
    setStepResult(3, `✕ ${e.message}`, 'error');
    toast(e.message, 'error');
  }
}

async function runStep4() {
  setStepState(4, 'running');
  try {
    const result = await api.executeTask(state.demoTaskId);
    if (state.apiBase) {
      state.tasks = await api.getTasks();
      state.agents = await api.getAgents();
      const rs = await api.getResults(state.demoTaskId);
      // merge, dedup
      const ids = new Set(state.results.map(r => r.id));
      rs.forEach(r => { if (!ids.has(r.id)) state.results.push(r); });
    }
    refresh();
    setStepState(4, 'done');
    if (result.success) {
      setStepResult(4, `
        <strong>✓ Task executed successfully</strong><br/>
        task_status: <code>${result.task_status}</code><br/>
        latency_ms: <code>${result.latency_ms}</code><br/>
        result: <code>${JSON.stringify(result.result)}</code>
      `);
      unlockStep(5);
      toast('Execution successful', 'success');
    } else {
      setStepResult(4, `✕ Execution failed: ${result.error}`, 'error');
      toast('Execution failed — try resetting the demo', 'error');
    }
  } catch (e) {
    setStepState(4, 'failed');
    setStepResult(4, `✕ ${e.message}`, 'error');
    toast(e.message, 'error');
  }
}

async function runStep5() {
  setStepState(5, 'running');
  await sleep(300);
  try {
    const results = await api.getResults(state.demoTaskId);
    setStepState(5, 'done');
    const r = results[0] || {};
    setStepResult(5, `
      <strong>✓ Result stored</strong><br/>
      success: <code>${r.success}</code><br/>
      latency_ms: <code>${r.latency_ms}</code><br/>
      result_payload: <code>${JSON.stringify(r.result_payload)}</code>
    `);
    unlockStep(6);
    toast('Result retrieved', 'success');
  } catch (e) {
    setStepState(5, 'failed');
    setStepResult(5, `✕ ${e.message}`, 'error');
    toast(e.message, 'error');
  }
}

async function runStep6() {
  setStepState(6, 'running');
  await sleep(300);
  try {
    const agent = await api.getAgent(state.demoAgentId);
    if (state.apiBase) state.agents = await api.getAgents();
    refresh();
    setStepState(6, 'done');
    setStepResult(6, `
      <strong>✓ Reputation updated</strong><br/>
      task_count: <code>${agent.task_count}</code><br/>
      success_rate: <code>${fmt(agent.success_rate, 4)}</code><br/>
      avg_latency_ms: <code>${fmt(agent.avg_latency_ms, 1)}</code>
    `);
    document.getElementById('demo-complete').style.display = 'block';
    toast('Demo complete! 🎉', 'success');
  } catch (e) {
    setStepState(6, 'failed');
    setStepResult(6, `✕ ${e.message}`, 'error');
    toast(e.message, 'error');
  }
}

function resetDemo() {
  // Reset steps UI
  [1,2,3,4,5,6].forEach(n => {
    const el = document.getElementById(`step-${n}`);
    el.classList.remove('active','done');
    if (n > 1) el.classList.add('locked');
    const badge = el.querySelector('.step-status-badge');
    badge.className = 'step-status-badge pending';
    badge.textContent = 'pending';
    const btn = document.getElementById(`step-${n}-btn`);
    if (btn) btn.disabled = (n > 1);
    const result = document.getElementById(`step-${n}-result`);
    if (result) { result.style.display = 'none'; result.innerHTML = ''; }
  });
  document.getElementById('demo-complete').style.display = 'none';

  // Reset mock state
  if (!state.apiBase) {
    state.agents = JSON.parse(JSON.stringify(SEED_AGENTS));
    state.tasks  = JSON.parse(JSON.stringify(SEED_TASKS));
    state.results = JSON.parse(JSON.stringify(SEED_RESULTS));
  }
  state.demoAgentId = null;
  state.demoTaskId = null;
  refresh();
  toast('Demo reset', 'info');
}

// ── Modal helpers ──────────────────────────────────────────
function openModal(id)  { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }

// ── Agent form ─────────────────────────────────────────────
async function handleAgentSubmit(e) {
  e.preventDefault();
  const cap = document.getElementById('f-agent-caps').value;
  const data = {
    name: document.getElementById('f-agent-name').value,
    description: document.getElementById('f-agent-desc').value,
    endpoint_url: document.getElementById('f-agent-url').value,
    capabilities: cap.split(',').map(s => s.trim()).filter(Boolean),
    price_per_request: parseFloat(document.getElementById('f-agent-price').value) || 0,
    avg_latency_ms: parseFloat(document.getElementById('f-agent-latency').value) || 0,
  };
  try {
    await api.createAgent(data);
    if (state.apiBase) state.agents = await api.getAgents();
    refresh();
    closeModal('modal-agent');
    document.getElementById('agent-form').reset();
    toast(`${data.name} registered`, 'success');
  } catch (err) {
    toast(err.message, 'error');
  }
}

// ── Task form ──────────────────────────────────────────────
async function handleTaskSubmit(e) {
  e.preventDefault();
  let cap = document.getElementById('f-task-cap').value;
  if (cap === 'custom') cap = document.getElementById('f-task-cap-custom').value.trim();
  if (!cap) { toast('Capability is required', 'error'); return; }

  let payload = {};
  try { payload = JSON.parse(document.getElementById('f-task-payload').value || '{}'); }
  catch { toast('Invalid JSON payload', 'error'); return; }

  const budgetVal = document.getElementById('f-task-budget').value;
  const auto = document.getElementById('f-task-auto').checked;

  const data = {
    required_capability: cap,
    payload,
    budget: budgetVal ? parseFloat(budgetVal) : null,
  };

  try {
    const task = await api.createTask(data);
    if (state.apiBase) state.tasks = await api.getTasks();
    refresh();
    closeModal('modal-task');
    document.getElementById('task-form').reset();
    toast('Task created', 'success');

    if (auto) {
      toast('Matching…', 'info');
      await sleep(600);
      try {
        await api.matchTask(task.id);
        if (state.apiBase) state.tasks = await api.getTasks();
        refresh();
        toast('Matched! Executing…', 'info');
        await sleep(400);
        const result = await api.executeTask(task.id);
        if (state.apiBase) {
          state.tasks = await api.getTasks();
          state.agents = await api.getAgents();
          const rs = await api.getResults(task.id);
          const ids = new Set(state.results.map(r => r.id));
          rs.forEach(r => { if (!ids.has(r.id)) state.results.push(r); });
        }
        refresh();
        if (result.success) {
          toast('Task completed successfully!', 'success');
          showTab('results');
        } else {
          toast('Task execution failed', 'error');
        }
      } catch (matchErr) {
        toast(matchErr.message, 'error');
      }
    } else {
      showTab('tasks');
    }
  } catch (err) {
    toast(err.message, 'error');
  }
}

// ── API Settings ───────────────────────────────────────────
async function connectApi() {
  const url = document.getElementById('f-api-url').value.trim().replace(/\/$/, '');
  if (!url) { toast('Enter a URL first', 'error'); return; }
  const result = document.getElementById('api-test-result');
  try {
    const r = await fetch(url + '/health');
    const data = await r.json();
    result.className = 'api-test-result ok';
    result.textContent = `✓ Connected — ${JSON.stringify(data)}`;
    result.style.display = 'block';
    state.apiBase = url;

    // Load live data
    state.agents  = await realApi.getAgents.call(realApi);
    state.tasks   = await realApi.getTasks.call(realApi);
    state.results = await realApi.getAllResults.call(realApi);
    refresh();
    updateApiStatus(true);
    toast('Connected to live backend', 'success');
    closeModal('modal-settings');
  } catch (e) {
    result.className = 'api-test-result err';
    result.textContent = `✕ Could not reach ${url}/health — ${e.message}`;
    result.style.display = 'block';
  }
}

function useMockMode() {
  state.apiBase = null;
  state.agents  = JSON.parse(JSON.stringify(SEED_AGENTS));
  state.tasks   = JSON.parse(JSON.stringify(SEED_TASKS));
  state.results = JSON.parse(JSON.stringify(SEED_RESULTS));
  refresh();
  updateApiStatus(false);
  toast('Switched to mock mode', 'info');
  closeModal('modal-settings');
}

function updateApiStatus(online) {
  const dot   = document.getElementById('api-dot');
  const label = document.getElementById('api-label');
  dot.className = 'status-dot ' + (online ? 'online' : 'mock');
  label.textContent = online ? 'Live API' : 'Mock mode';
}

// ── Bootstrap ──────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Load seed data
  state.agents  = JSON.parse(JSON.stringify(SEED_AGENTS));
  state.tasks   = JSON.parse(JSON.stringify(SEED_TASKS));
  state.results = JSON.parse(JSON.stringify(SEED_RESULTS));
  updateApiStatus(false);
  refresh();

  // Tab navigation
  document.querySelectorAll('.nav-item[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => showTab(btn.dataset.tab));
  });
  document.getElementById('go-agents-btn')?.addEventListener('click', () => showTab('agents'));
  document.getElementById('go-tasks-btn')?.addEventListener('click',  () => showTab('tasks'));

  // Topbar quick buttons
  document.getElementById('quick-create-btn').addEventListener('click', () => openModal('modal-task'));
  document.getElementById('reset-btn').addEventListener('click', resetDemo);

  // Demo steps
  document.getElementById('step-1-btn').addEventListener('click', runStep1);
  document.getElementById('step-2-btn').addEventListener('click', runStep2);
  document.getElementById('step-3-btn').addEventListener('click', runStep3);
  document.getElementById('step-4-btn').addEventListener('click', runStep4);
  document.getElementById('step-5-btn').addEventListener('click', runStep5);
  document.getElementById('step-6-btn').addEventListener('click', runStep6);

  // Agent modal
  document.getElementById('add-agent-btn').addEventListener('click', () => openModal('modal-agent'));
  document.getElementById('close-agent-modal').addEventListener('click', () => closeModal('modal-agent'));
  document.getElementById('cancel-agent-modal').addEventListener('click', () => closeModal('modal-agent'));
  document.getElementById('agent-form').addEventListener('submit', handleAgentSubmit);

  // Task modal
  document.getElementById('add-task-btn').addEventListener('click', () => openModal('modal-task'));
  document.getElementById('close-task-modal').addEventListener('click', () => closeModal('modal-task'));
  document.getElementById('cancel-task-modal').addEventListener('click', () => closeModal('modal-task'));
  document.getElementById('task-form').addEventListener('submit', handleTaskSubmit);
  document.getElementById('f-task-cap').addEventListener('change', e => {
    document.getElementById('custom-cap-row').style.display =
      e.target.value === 'custom' ? 'flex' : 'none';
  });

  // Settings modal
  document.getElementById('settings-btn').addEventListener('click', () => openModal('modal-settings'));
  document.getElementById('close-settings-modal').addEventListener('click', () => closeModal('modal-settings'));
  document.getElementById('connect-api-btn').addEventListener('click', connectApi);
  document.getElementById('use-mock-btn').addEventListener('click', useMockMode);

  // Close modals on overlay click
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) overlay.style.display = 'none';
    });
  });

  // Keyboard shortcut
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay').forEach(o => o.style.display = 'none');
    }
  });
});
