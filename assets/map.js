(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const COLORS = { fast: "#7a5af5", compile: "#1f9e75", edit: "#d2603a", wsl: "#3478d6", wsp: "#c9891a" };
  const ORDER = ["fast", "compile", "edit", "wsl", "wsp"];
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const root = document.documentElement;
  try { const t = localStorage.getItem("theme"); if (t) root.dataset.theme = t; } catch (e) {}
  document.getElementById("theme").onclick = () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
  };

  // Time axis: early decades compressed, 2026 stretched because most recent work falls in its last months.
  const STOPS = [[1990, 0], [2015, 200], [2025, 1900], [2026.7, 2140], [2026.9, 2440]];
  function X(y) {
    for (let i = 1; i < STOPS.length; i++) {
      const [y0, x0] = STOPS[i - 1], [y1, x1] = STOPS[i];
      if (y <= y1) return x0 + ((Math.max(y, y0) - y0) / (y1 - y0)) * (x1 - x0);
    }
    return STOPS[STOPS.length - 1][1];
  }
  const LEFT = 40, TOP = 44, ROWH = 26, GAP = 170;

  fetch("data/map.json").then((r) => r.json()).then((d) => {
    const svg = document.getElementById("map");
    // Place nodes first: within a lane, a node goes to the first row where its label does not collide.
    const pos = {}, rows = {};
    const nodes = d.nodes.slice().sort((a, b) => a.year - b.year);
    for (const n of nodes) {
      const lane = ORDER.indexOf(n.cat), x = LEFT + X(n.year);
      rows[lane] = rows[lane] || [];
      let row = 0;
      while ((rows[lane][row] ?? -1e9) > x - GAP) row++;
      rows[lane][row] = x;
      pos[n.key] = { x, lane, row, n };
    }
    const laneH = ORDER.map((_, i) => 44 + Math.max(1, (rows[i] || []).length) * ROWH + 14);
    const laneY = laneH.reduce((acc, h, i) => (acc.push(i ? acc[i - 1] + laneH[i - 1] : TOP), acc), []);
    for (const k in pos) pos[k].y = laneY[pos[k].lane] + 48 + pos[k].row * ROWH;
    const W = LEFT + X(2026.9) + 200, H = laneY[ORDER.length - 1] + laneH[ORDER.length - 1] + 20;
    svg.setAttribute("width", W); svg.setAttribute("height", H); svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const el = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); (parent || svg).appendChild(e); return e; };

    ORDER.forEach((c, i) => {
      el("rect", { x: 0, y: laneY[i], width: W, height: laneH[i], fill: i % 2 ? "transparent" : "var(--hover)", opacity: 0.6 });
    });
    const axis = el("g", { class: "axis" });
    for (const y of [1990, 2000, 2010, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]) {
      const x = LEFT + X(y);
      el("line", { x1: x, x2: x, y1: TOP - 14, y2: H - 20 }, axis);
      const t = el("text", { x: x + 3, y: TOP - 18 }, axis); t.textContent = y;
    }
    [["Oct", 2026.75], ["Nov", 2026.84]].forEach(([m, y]) => { const t = el("text", { x: LEFT + X(y) + 3, y: TOP - 18 }, axis); t.textContent = m; });
    ORDER.forEach((c, i) => {
      const t = el("text", { x: 14, y: laneY[i] + 22, class: "lane-label", fill: COLORS[c] }); t.textContent = d.categories[c];
    });
    const edges = el("g", {});
    const edgeEls = d.edges.filter(([a, b]) => pos[a] && pos[b]).map(([a, b]) => {
      const p = pos[a], q = pos[b], mx = (p.x + q.x) / 2;
      const e = el("path", { d: `M${p.x},${p.y} C${mx},${p.y} ${mx},${q.y} ${q.x},${q.y}`, class: "edge", stroke: COLORS[q.n.cat] }, edges);
      e.dataset.a = a; e.dataset.b = b; return e;
    });
    const nodeEls = {};
    for (const k in pos) {
      const { x, y, n } = pos[k];
      const g = el("g", { class: "node", tabindex: 0 });
      el("circle", { cx: x, cy: y, r: 6, fill: COLORS[n.cat] }, g);
      const t = el("text", { x: x + 10, y: y + 4 }, g); t.textContent = n.short;
      const tip = el("title", {}, g); tip.textContent = `${n.title} (${Math.floor(n.year)})`;
      g.addEventListener("click", () => select(k));
      g.addEventListener("keydown", (e) => { if (e.key === "Enter") select(k); });
      nodeEls[k] = g;
    }

    document.getElementById("legend").innerHTML = ORDER.map((c) => `<div><span style="background:${COLORS[c]}"></span>${esc(d.categories[c])}</div>`).join("");

    function select(k) {
      const n = pos[k].n;
      const near = new Set([k]);
      edgeEls.forEach((e) => { const on = e.dataset.a === k || e.dataset.b === k; e.classList.toggle("hl", on); if (on) { near.add(e.dataset.a); near.add(e.dataset.b); } });
      for (const j in nodeEls) { nodeEls[j].classList.toggle("dim", !near.has(j)); nodeEls[j].classList.toggle("sel", j === k); }
      const from = d.edges.filter(([a, b]) => b === k).map(([a]) => a).filter((a) => pos[a]);
      const to = d.edges.filter(([a]) => a === k).map(([, b]) => b).filter((b) => pos[b]);
      const link = (j) => `<button type="button" data-k="${j}">${esc(pos[j].n.short)}</button>`;
      document.getElementById("side").innerHTML =
        `<h2>${esc(n.title)}</h2><p class="who">${esc(n.who)} · ${esc(n.date || Math.floor(n.year))}</p><p class="note">${esc(n.note)}</p>` +
        `<p><a href="./#${encodeURIComponent(n.id)}">Read it here</a><a href="${esc(n.url)}" target="_blank" rel="noopener">Original ↗</a></p>` +
        (from.length ? `<p class="rel">Builds on: ${from.map(link).join(", ")}</p>` : "") +
        (to.length ? `<p class="rel">Led to: ${to.map(link).join(", ")}</p>` : "");
      document.querySelectorAll("#side .rel button").forEach((b) => b.addEventListener("click", () => select(b.dataset.k)));
    }
    document.getElementById("scroll").scrollLeft = 1e6;
  });
})();
