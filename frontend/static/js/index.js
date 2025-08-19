async function loadRobots() {
  const res = await fetch('/api/robots');
  const data = await res.json();
  const grid = document.getElementById('grid');
  grid.innerHTML = '';

  (data.robots || []).forEach(async r => {
    // Lav et kort
    const a = document.createElement('a');
    a.className = 'card';
    a.href = `/robot?id=${encodeURIComponent(r.id)}`;

    // Default status
    let online = false;
    try {
      const statusRes = await fetch(`/api/robots/${r.id}/status`);
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        online = statusData.online;
      }
    } catch (e) {
      online = false;
    }

    // Byg HTML til kortet
    a.innerHTML = `
      <div class="thumb" style="background-image:url('${r.thumbnail || '/static/img/logo.png'}')"></div>
      <div class="card-body">
        <div class="card-title">${r.name}</div>
        <div class="tag">${r.kind}</div>
        <div class="status-indicator">
          <span class="dot ${online ? 'online' : 'offline'}"></span>
          ${online ? 'Online' : 'Offline'}
        </div>
      </div>`;
    
    grid.appendChild(a);
  });
}
loadRobots();
