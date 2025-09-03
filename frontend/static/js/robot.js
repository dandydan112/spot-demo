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
const feedbackEl = document.getElementById('feedback');
const vizCanvas  = document.getElementById('vizCanvas'); // 3D visualizer canvas

// Sørger for at overlay-canvas følger billedets størrelse
function resizeCanvas(){
  overlay.width = img.clientWidth;
  overlay.height = img.clientHeight;
}
window.addEventListener('resize', resizeCanvas);
img.addEventListener('load', resizeCanvas);

// ------------------ Status ------------------
async function updateStatus(id) {
  try {
    const res = await fetch(`/api/robots/${encodeURIComponent(id)}/status`);
    if (res.ok) {
      const data = await res.json();
      if (data.online) {
        dotEl.classList.replace('offline', 'online');
        statusEl.textContent = 'Online';
      } else {
        dotEl.classList.replace('online', 'offline');
        statusEl.textContent = 'Offline';
      }
    } else {
      throw new Error("Status fetch failed");
    }
  } catch (e) {
    dotEl.classList.replace('online', 'offline');
    statusEl.textContent = 'Offline';
  }
}

// ------------------ Init ------------------
async function init() {
  const id = qs('id');

  // Hent robot-info
  const res = await fetch(`/api/robots/${encodeURIComponent(id)}`);
  const robot = await res.json();
  titleEl.textContent = robot.name || id;

  // Video-stream (MJPEG)
  img.src = robot.endpoints.mjpeg;

  // Websocket til perception (overlays – kan laves senere)
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}${robot.endpoints.perception}`);
  ws.onopen  = () => statusEl.textContent = 'Forbundet';
  ws.onclose = () => statusEl.textContent = 'Lukket';

  // Status loop
  await updateStatus(id);
  setInterval(() => updateStatus(id), 5000);
}

// ------------------ 3D Visualizer ------------------
let scene, camera, renderer, pointCloud, controls;

function init3D() {
  if (!vizCanvas) return;

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(
    75,
    vizCanvas.clientWidth / vizCanvas.clientHeight,
    0.1,
    50
  );
  renderer = new THREE.WebGLRenderer({ canvas: vizCanvas });
  renderer.setSize(vizCanvas.clientWidth, vizCanvas.clientHeight);
  camera.position.z = 3;

  // Orbit controls (brug mus til at rotere/zoome)
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  // Lys
  const light = new THREE.PointLight(0xffffff, 1);
  light.position.set(2, 2, 2);
  scene.add(light);

  // WebSocket til Spot visualizer endpoint
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/api/robots/spot-001/visualizer`);

  ws.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    if (!data.points) return;

    const positions = new Float32Array(data.points.length * 3);
    for (let i = 0; i < data.points.length; i++) {
      positions[i*3 + 0] = data.points[i][0];
      positions[i*3 + 1] = data.points[i][1];
      positions[i*3 + 2] = data.points[i][2];
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({ color: 0x00ff00, size: 0.01 });
    if (pointCloud) scene.remove(pointCloud);
    pointCloud = new THREE.Points(geometry, material);
    scene.add(pointCloud);
  };

  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();
}

// ------------------ View Switch ------------------
function showView(view) {
  const camDiv = document.getElementById("cameraView");
  const vizDiv = document.getElementById("visualizerView");

  if (view === "camera") {
    camDiv.style.display = "block";
    vizDiv.style.display = "none";
  } else if (view === "visualizer") {
    camDiv.style.display = "none";
    vizDiv.style.display = "block";
    if (!scene) init3D();
  }
}

// ------------------ Demo Endpoints ------------------
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

// ------------------ Buttons ------------------
document.getElementById('helloBtn').addEventListener('click', () => {
  callDemo(qs('id'), "hello");
});

document.getElementById('layBtn').addEventListener('click', () => {
  callDemo(qs('id'), "lay");
});

document.getElementById('powerOnBtn').addEventListener('click', () => {
  callDemo(qs('id'), "poweron");
});

document.getElementById('powerOffBtn').addEventListener('click', () => {
  callDemo(qs('id'), "poweroff");
});

document.getElementById('rolloverBtn').addEventListener('click', () => {
  callDemo(qs('id'), "rollover");
});

document.getElementById('standBtn').addEventListener('click', () => {
  callDemo(qs('id'), "stand");
});

document.getElementById('fiducialBtn').addEventListener('click', () => {
  callDemo(qs('id'), "fiducial");
});

document.getElementById('cameraBtn').addEventListener('click', () => {
  showView("camera");
});
document.getElementById('vizBtn').addEventListener('click', () => {
  showView("visualizer");
});

document.getElementById('increaseHeightBtn').addEventListener('click', () => {
  callDemo(qs('id'), "increase_height");
});

document.getElementById('decreaseHeightBtn').addEventListener('click', () => {
  callDemo(qs('id'), "decrease_height");
});

document.getElementById('bodyrollBtn').addEventListener('click', () => {
  callDemo(qs('id'), "bodyroll");
});

document.getElementById('snakeheadBtn').addEventListener('click', () => {
  callDemo(qs('id'), "snakehead");
});

document.getElementById('stopBtn').addEventListener('click', () => {
  callDemo(qs('id'), "stop");
});

document.getElementById('estopBtn').addEventListener('click', () => {
  callDemo(qs('id'), "estop");
});

document.getElementById('wiggleBtn').addEventListener('click', () => {
  callDemo(qs('id'), "wiggle");
});

document.getElementById('selfrightBtn').addEventListener('click', () => {
  callDemo(qs('id'), "selfright");
});

// ------------------ Start ------------------
init();
showView("camera");
