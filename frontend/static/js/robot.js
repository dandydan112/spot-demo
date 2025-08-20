// Henter query param (fx id fra URL: ?id=spot-001)
function qs(name){ 
  return new URL(location.href).searchParams.get(name); 
}

// HTML elementer vi skal arbejde med
const statusEl   = document.getElementById('status');
const dotEl      = document.getElementById('dot');
const titleEl    = document.getElementById('title');
const img        = document.getElementById('mjpeg');
const overlay    = document.getElementById('overlay');
const ctx        = overlay.getContext('2d');
const feedbackEl = document.getElementById('feedback'); // Nyt felt til feedback-tekst

// Sørger for at overlay-canvas følger billedets størrelse
function resizeCanvas(){
  overlay.width = img.clientWidth;
  overlay.height = img.clientHeight;
}
window.addEventListener('resize', resizeCanvas);
img.addEventListener('load', resizeCanvas);

// Henter online/offline status fra backend
async function updateStatus(id) {
  try {
    const res = await fetch(`/api/robots/${encodeURIComponent(id)}/status`);
    if (res.ok) {
      const data = await res.json();
      if (data.online) {
        dotEl.classList.remove('offline');
        dotEl.classList.add('online');
        statusEl.textContent = 'Online';
      } else {
        dotEl.classList.remove('online');
        dotEl.classList.add('offline');
        statusEl.textContent = 'Offline';
      }
    } else {
      throw new Error("Status fetch failed");
    }
  } catch (e) {
    dotEl.classList.remove('online');
    dotEl.classList.add('offline');
    statusEl.textContent = 'Offline';
  }
}

// Initialiserer siden (henter robot info + starter stream + websocket)
async function init() {
  const id = qs('id');

  // Hent robot-info
  const res = await fetch(`/api/robots/${encodeURIComponent(id)}`);
  const robot = await res.json();
  titleEl.textContent = robot.name || id;

  // Sæt video-stream (MJPEG)
  img.src = robot.endpoints.mjpeg;

  // Åben websocket til perception (fx overlays)
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}${robot.endpoints.perception}`);
  ws.onopen  = () => statusEl.textContent = 'Forbundet';
  ws.onclose = () => statusEl.textContent = 'Lukket';
  ws.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    drawOverlay(msg); // TODO: lav drawOverlay senere
  };

  // Kør status-check nu og derefter hvert 5. sekund
  await updateStatus(id);
  setInterval(() => updateStatus(id), 5000);
}

// Event handler til demo-knappen
document.getElementById('helloBtn').addEventListener('click', async () => {
  const id = qs('id');
  try {
    // Kalder backend endpoint for demo
    const res = await fetch(`/api/robots/${encodeURIComponent(id)}/demo/hello`, {
      method: 'POST'
    });
    const data = await res.json();

    // Viser feedback direkte i interfacet i stedet for popup
    feedbackEl.textContent = data.message || "Demo kørt!";
    feedbackEl.style.color = "green";
  } catch (e) {
    feedbackEl.textContent = "Fejl: " + e.message;
    feedbackEl.style.color = "red";
  }
});

init();
