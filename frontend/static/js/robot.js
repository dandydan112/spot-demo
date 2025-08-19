function qs(name){ 
  return new URL(location.href).searchParams.get(name); 
}

const statusEl = document.getElementById('status');
const titleEl  = document.getElementById('title');
const img = document.getElementById('mjpeg');
const overlay = document.getElementById('overlay');
const ctx = overlay.getContext('2d');

function resizeCanvas(){
  overlay.width = img.clientWidth;
  overlay.height = img.clientHeight;
}
window.addEventListener('resize', resizeCanvas);
img.addEventListener('load', resizeCanvas);

async function init() {
  const id = qs('id');
  const res = await fetch(`/api/robots/${encodeURIComponent(id)}`);
  const robot = await res.json();
  titleEl.textContent = robot.name || id;

  img.src = robot.endpoints.mjpeg;

  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}${robot.endpoints.perception}`);
  ws.onopen  = () => statusEl.textContent = 'Forbundet';
  ws.onclose = () => statusEl.textContent = 'Lukket';
  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    drawOverlay(msg);
  };
}

init();
