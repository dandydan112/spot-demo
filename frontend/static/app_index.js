async function loadRobots() {
  const res = await fetch('/api/robots');
  const data = await res.json();
  const grid = document.getElementById('grid');
  grid.innerHTML = '';

  (data.robots || []).forEach(r => {
    const a = document.createElement('a');
    a.className = 'card';
    a.href = `/robot?id=${encodeURIComponent(r.id)}`;
    a.innerHTML = `
      <div class="thumb" style="background-image:url('${r.thumbnail || '/static/logo.png'}')"></div>
      <div class="card-body">
        <div class="card-title">${r.name}</div>
        <div class="tag">${r.kind}</div>
      </div>`;
    grid.appendChild(a);
  });
}
loadRobots();
