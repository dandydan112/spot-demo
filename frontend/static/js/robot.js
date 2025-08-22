// Henter query param (fx id fra URL: ?id=spot-001)
function qs(name){ 
  return new URL(location.href).searchParams.get(name); 
}

// HTML elementer
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

//_______________________________________________________________________________________________________________________

let scene, camera, renderer, pointCloud;

function init3D() {
  const canvas = document.getElementById("mapCanvas");
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(75, canvas.clientWidth/canvas.clientHeight, 0.1, 100);
  renderer = new THREE.WebGLRenderer({canvas: canvas});
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  camera.position.z = 2;

  const ws = new WebSocket(`ws://${location.host}/api/robots/spot-001/pointcloud`);
  ws.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    const positions = new Float32Array(data.points.length * 3);
    for (let i=0; i<data.points.length; i++) {
      positions[i*3+0] = data.points[i][0];
      positions[i*3+1] = data.points[i][1];
      positions[i*3+2] = data.points[i][2];
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({color: 0x00ff00, size: 0.02});
    if (pointCloud) scene.remove(pointCloud);
    pointCloud = new THREE.Points(geometry, material);
    scene.add(pointCloud);
  };

  function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
  }
  animate();
}

function showView(view) {
  document.getElementById("cameraView").style.display = (view==="camera") ? "block" : "none";
  document.getElementById("mapView").style.display = (view==="map") ? "block" : "none";
  if (view === "map" && !scene) init3D();
}

/*________________________________________________________________________________________________________________*/

// Generisk funktion til at kalde Spot demo endpoints
async function callDemo(id, action) {
  try {
    const res = await fetch(`/api/robots/${encodeURIComponent(id)}/demo/${action}`, {
      method: 'POST'
    });
    const data = await res.json();
    feedbackEl.textContent = data.message || data.error || "OK";
    feedbackEl.style.color = data.error ? "red" : "green";
  } catch (e) {
    feedbackEl.textContent = "Fejl: " + e.message;
    feedbackEl.style.color = "red";
  }
}

// Event handlers til knapper
document.getElementById('helloBtn').addEventListener('click', () => {
  callDemo(qs('id'), "hello");
});

document.getElementById('layBtn').addEventListener('click', () => {
  callDemo(qs('id'), "lay");
});

document.getElementById('powerOffBtn').addEventListener('click', () => {
  callDemo(qs('id'), "poweroff");
});

init();
