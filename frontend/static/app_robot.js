function qs(name){ return new URL(location.href).searchParams.get(name); }

const statusEl = document.getElementById('status');
const titleEl  = document.getElementById('title');
const img = document.getElementById('mjpeg');
const overlay = document.getElementById('overlay');
const ctx = overlay.getContext('2d');

function resizeCanvas(){
  const r = img.getBoundingClientRect();
  overlay.width = r.width; overlay.height = r.height;
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

// function drawOverlay(msg){
//   const [iw, ih] = msg.image_size || [960, 540];
//   const cw = overlay.width, ch = overlay.height;
//   const sx = cw / iw, sy = ch / ih;
//   ctx.clearRect(0,0,cw,ch);
//   ctx.lineWidth = 2 * ((sx+sy)/2);

//   (msg.boxes || []).forEach(b => {
//     const [x,y,w,h] = b.xywh;
//     ctx.strokeStyle = 'lime';
//     ctx.strokeRect(x*sx, y*sy, w*sx, h*sy);
//   });
// }

init();
