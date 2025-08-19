console.log('spot demo ready');

const statusEl = document.getElementById('status');
const btnStart = document.getElementById('btnStart');
const btnStop  = document.getElementById('btnStop');

async function postJson(url, body = {}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const text = await res.text();
  let data = null;
  try { data = JSON.parse(text); } catch { /* ignore */ }
  return { ok: res.ok, status: res.status, data, raw: text };
}

btnStart.onclick = async () => {
  statusEl.textContent = 'Starter demo…';
  const r = await postJson('/demo/start', { kind: 'dance' });
  statusEl.textContent = r.data?.message || `HTTP ${r.status}`;
};

btnStop.onclick = async () => {
  statusEl.textContent = 'Stopper demo…';
  const r = await postJson('/demo/stop');
  statusEl.textContent = r.data?.message || `HTTP ${r.status}`;
};
