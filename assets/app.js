(function () {
  "use strict";
  const C = window.READER_CONFIG;
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const PAGE = 200;
  let DATA = null, shown = PAGE, current = null, rows = [];
  const byId = {};
  let VIEW = "key";
  const isKey = (it) => it.cl || it.s || (it.rx && it.rx.length >= 2);
  document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => {
    VIEW = b.dataset.v;
    document.querySelectorAll(".tabs button").forEach((x) => x.classList.toggle("on", x === b));
    shown = PAGE; render();
  }));

  const root = document.documentElement;
  try { const t = localStorage.getItem("theme"); if (t) root.dataset.theme = t; } catch (e) {}
  $("theme").onclick = () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
  };

  try { $("force").checked = localStorage.getItem("forceEmbed") === "1"; } catch (e) {}
  $("force").addEventListener("change", () => { try { localStorage.setItem("forceEmbed", $("force").checked ? "1" : "0"); } catch (e) {} if (current) frame(current); });
  $("frame").addEventListener("click", (e) => {
    if (e.target.id === "forceOn") { e.preventDefault(); $("force").checked = true; try { localStorage.setItem("forceEmbed", "1"); } catch (x) {} frame(current); }
  });
  fetch("data/items.json").then((r) => r.json()).then((d) => {
    DATA = d;
    for (const it of d.items) byId[it.id] = it;
    for (const [k, v] of Object.entries(d.categories)) $("cat").insertAdjacentHTML("beforeend", `<option value="${k}">${esc(v)}</option>`);
    for (const t of d.types) $("type").insertAdjacentHTML("beforeend", `<option value="${t}">${esc(t[0].toUpperCase() + t.slice(1))}</option>`);
    fillTags();
    $("updated").textContent = `${d.items.length.toLocaleString()} items · updated ${d.updated}`;
    ["q", "cat", "type", "tag", "sort", "showrx"].forEach((id) => $(id).addEventListener("input", () => { if (id === "cat") fillTags(); shown = PAGE; render(); }));
    render();
    route();
  });

  function fillTags() {
    const cat = $("cat").value, sel = $("tag"), keep = sel.value;
    const tags = cat ? DATA.tags[cat] : [...new Set(Object.values(DATA.tags).flat())].sort();
    sel.innerHTML = '<option value="">All tags</option>' + tags.map((t) => `<option>${esc(t)}</option>`).join("");
    if (tags.includes(keep)) sel.value = keep;
  }

  function filtered() {
    const q = $("q").value.trim().toLowerCase(), cat = $("cat").value, type = $("type").value, tag = $("tag").value, showrx = $("showrx").checked, view = VIEW;
    let xs = DATA.items.filter((it) =>
      (!cat || it.c.includes(cat)) && (!type || it.y === type) && (!tag || it.g.includes(tag)) && (view !== "star" || it.s) && (view !== "key" || isKey(it)) && (showrx || !it.rof || it.s) &&
      (!q || (it.t + " " + (it.a || "") + " " + (it.v || "") + " " + (it.sm || "")).toLowerCase().includes(q)));
    const s = $("sort").value;
    xs.sort(s === "cited" ? (a, b) => (b.n || 0) - (a.n || 0) : s === "old" ? (a, b) => (a.d || "9").localeCompare(b.d || "9") : (a, b) => (b.d || "").localeCompare(a.d || ""));
    return xs;
  }

  function render() {
    rows = filtered();
    $("count").textContent = VIEW === "key" ? `${rows.length} key works · ${DATA.items.length.toLocaleString()} items in all` : `${rows.length.toLocaleString()} of ${DATA.items.length.toLocaleString()}`;
    $("list").innerHTML = rows.slice(0, shown).map((it) => {
      const meta = [it.y, it.d, it.a && it.a.split(",")[0] + (it.a.includes(",") ? " et al." : "")].filter(Boolean).join(" · ");
      return `<li data-id="${esc(it.id)}" class="${current && current.id === it.id ? "on" : ""}${isKey(it) ? " key" : ""}"><div class="t">${it.s ? '<span class="s" title="Starred">★</span>' : ""}<span>${esc(it.t)}</span>${it.cl ? '<span class="cl">Classic</span>' : ""}</div>${it.sm ? `<div class="sm">${esc(it.sm)}</div>` : ""}<div class="m">${esc(meta)}${rxCount(it)}</div></li>`;
    }).join("");
    $("more").hidden = rows.length <= shown;
  }
  function rxCount(it) {
    if (!it.rx) return "";
    const a = it.rx.filter((j) => byId[j] && byId[j].dp === "analysis").length;
    return ` · ${it.rx.length} reaction${it.rx.length > 1 ? "s" : ""}${a ? `, ${a} with analysis` : ""}`;
  }
  $("more").onclick = () => { shown += PAGE; render(); };
  $("list").addEventListener("click", (e) => {
    const li = e.target.closest("li");
    if (!li) return;
    const it = DATA.items.find((x) => x.id === li.dataset.id);
    // Sites that refuse to be embedded open straight away in a new tab (must happen inside the click).
    if (it && it.k === "none" && !forceEmbed()) window.open(it.u, "_blank", "noopener");
    location.hash = encodeURIComponent(li.dataset.id);
  });
  $("back").onclick = () => { document.body.classList.remove("reading"); history.replaceState(null, "", location.pathname); };
  addEventListener("hashchange", route);

  function route() {
    if (!DATA) return;
    const id = decodeURIComponent(location.hash.slice(1));
    const it = DATA.items.find((x) => x.id === id);
    if (it) open(it);
  }

  function open(it) {
    current = it;
    document.body.classList.add("reading");
    $("empty").hidden = true; $("doc").hidden = false;
    $("docTitle").textContent = it.t;
    $("docSub").textContent = [it.a, it.v, it.d].filter(Boolean).join(" · ");
    $("docSum").textContent = it.sm || "";
    $("docHn").hidden = !it.hn;
    $("docHn").onclick = (e) => { e.preventDefault(); hn($("frame"), Object.assign({}, it, { e: it.hn, _host: it })); };
    const cats = it.c.map((c) => DATA.categories[c]);
    $("docTags").innerHTML = (it.cl ? '<span class="chip classic">Classic</span>' : "") + (it.s ? '<span class="chip star">★ Starred</span>' : "") + [...cats, ...it.g].map((t) => `<span class="chip">${esc(t)}</span>`).join("");
    $("docOpen").href = it.u;
    const eb = `id: ${it.id}\nstar: ${it.s ? "yes" : "no"}\ntags: ${it.g.join(", ")}\ncategory: ${it.c.join(", ")}\nhide: no\n`;
    $("docEdit").href = `https://github.com/${C.repo}/issues/new?labels=edit&title=${encodeURIComponent("Edit: " + it.t.slice(0, 80))}&body=${encodeURIComponent(eb)}`;
    frame(it);
    reactions(it);
    comments(it);
    document.querySelectorAll(".list li").forEach((li) => li.classList.toggle("on", li.dataset.id === it.id));
    $("reader").scrollTop = 0;
    document.title = it.t + " · Weight Space Reader";
  }

  function loadScript(src) {
    return new Promise((ok, bad) => {
      if (document.querySelector(`script[src="${src}"]`)) return ok();
      const s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = bad; document.head.appendChild(s);
    });
  }
  const MD = ["https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js", "https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.1.6/purify.min.js"];

  function fallback(f, it, note) {
    f.innerHTML = `<div class="card"><p>${esc(note || "Opened in a new tab. This site does not allow embedding.")}</p><p class="small">If you use a browser extension that lifts embedding limits, you can <a href="#" id="forceOn">embed these sites here</a>.</p>${it.x ? `<p class="abs">${esc(it.x)}</p>` : ""}<p><a href="${esc(it.u)}" target="_blank" rel="noopener">Open again ↗</a></p></div>`;
  }

  async function readme(f, it, url, base) {
    f.innerHTML = '<div class="doc-md"><p class="muted">Loading…</p></div>';
    try {
      await Promise.all(MD.map(loadScript));
      const r = await fetch(url, { headers: { Accept: "application/vnd.github.raw+json" } });
      if (!r.ok) throw new Error(r.status);
      let md = await r.text();
      md = md.replace(/^---\n[\s\S]*?\n---\n/, "");
      if (current !== it) return;
      const html = DOMPurify.sanitize(marked.parse(md, { gfm: true }));
      f.innerHTML = `<div class="doc-md">${html}</div>`;
      f.querySelectorAll("img[src], a[href]").forEach((el) => {
        const k = el.tagName === "IMG" ? "src" : "href", v = el.getAttribute(k);
        if (v && !/^(https?:|#|mailto:|data:)/.test(v)) el.setAttribute(k, base + v.replace(/^\.?\//, ""));
        if (k === "href") { el.target = "_blank"; el.rel = "noopener"; }
      });
    } catch (e) { if (current === it) fallback(f, it, "This page could not be loaded here."); }
  }

  function forceEmbed() { try { return localStorage.getItem("forceEmbed") === "1"; } catch (e) { return false; } }

  async function hn(f, it) {
    f.innerHTML = '<div class="doc-md"><p class="muted">Loading…</p></div>';
    try {
      await loadScript(MD[1]);
      const d = await (await fetch(`https://hn.algolia.com/api/v1/items/${it.e}`)).json();
      if (current !== (it._host || it)) return;
      const when = (t) => new Date(t).toISOString().slice(0, 16).replace("T", " ");
      const walk = (c, depth) => !c.text ? (c.children || []).map((x) => walk(x, depth)).join("") :
        `<div class="hn-c" style="margin-left:${Math.min(depth, 6) * 18}px"><div class="hn-m">${esc(c.author || "")} · ${when(c.created_at)}</div>${DOMPurify.sanitize(c.text)}</div>` + (c.children || []).map((x) => walk(x, depth + 1)).join("");
      const head = `<h1 class="hn-t">${esc(d.title || "")}</h1><p class="hn-m">${d.points || 0} points · ${esc(d.author || "")} · ${when(d.created_at)}${d.url ? ` · <a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(new URL(d.url).hostname)}</a>` : ""}</p>${d.text ? DOMPurify.sanitize(d.text) : ""}`;
      f.innerHTML = `<div class="doc-md hn">${head}${(d.children || []).map((c) => walk(c, 0)).join("")}</div>`;
      f.querySelectorAll("a[href]").forEach((a) => { a.target = "_blank"; a.rel = "noopener"; });
    } catch (e) { if (current === (it._host || it)) fallback(f, it, "This discussion could not be loaded here."); }
  }

  function frame(it) {
    const f = $("frame");
    const k = it.k;
    if (k === "tweet") {
      f.innerHTML = `<div class="tweet"><blockquote class="twitter-tweet" data-dnt="true"><a href="${esc(it.u.replace("x.com", "twitter.com"))}"></a></blockquote></div>`;
      if (window.twttr && twttr.widgets) twttr.widgets.load(f); else loadScript("https://platform.twitter.com/widgets.js");
    } else if (k === "pdf" || k === "frame" || k === "reddit" || k === "youtube") {
      f.innerHTML = `<iframe src="${esc(it.e || it.u)}" loading="lazy" referrerpolicy="no-referrer" allowfullscreen title="${esc(it.t)}"></iframe>`;
    } else if (k === "hn") {
      hn(f, it);
    } else if (k === "none" && forceEmbed()) {
      f.innerHTML = `<iframe src="${esc(it.u)}" loading="lazy" referrerpolicy="no-referrer" title="${esc(it.t)}"></iframe>`;
    } else if (k === "github") {
      const repo = it.e;
      readme(f, it, `https://api.github.com/repos/${repo}/readme`, `https://raw.githubusercontent.com/${repo}/HEAD/`);
    } else if (k === "hf") {
      readme(f, it, `https://huggingface.co/${it.e}/raw/main/README.md`, `https://huggingface.co/${it.e}/resolve/main/`);
    } else {
      fallback(f, it);
    }
  }

  function reactions(it) {
    const box = $("reactions");
    const host = it.rof ? byId[it.rof] : null;
    let html = "";
    if (host) html += `<p class="rx-up">Reacting to <a href="#${encodeURIComponent(host.id)}">${esc(host.t)}</a></p>`;
    if (it.rx && it.rx.length) {
      const row = (j) => { const r = byId[j]; return r ? `<li><a href="#${encodeURIComponent(r.id)}">${esc(r.a || r.t)}</a>${r.sm ? ` — ${esc(r.sm)}` : ""}</li>` : ""; };
      const deep = it.rx.filter((j) => byId[j] && byId[j].dp === "analysis"), short = it.rx.filter((j) => !deep.includes(j));
      html += `<h3>Reactions <span class="muted">${it.rx.length}</span></h3>`;
      if (deep.length) html += `<p class="rx-h">With analysis</p><ul class="rx">${deep.map(row).join("")}</ul>`;
      if (short.length) html += `<details${deep.length ? "" : " open"}><summary class="rx-h">Short reactions (${short.length})</summary><ul class="rx">${short.map(row).join("")}</ul></details>`;
    }
    box.innerHTML = html;
    box.hidden = !html;
  }

  function comments(it) {
    const box = $("giscus");
    box.innerHTML = "";
    if (!C.giscus || !C.giscus.repoId) { box.innerHTML = '<p class="muted">Comments are not set up yet.</p>'; return; }
    const s = document.createElement("script");
    const g = C.giscus;
    const attrs = { src: "https://giscus.app/client.js", "data-repo": C.repo, "data-repo-id": g.repoId, "data-category": g.category, "data-category-id": g.categoryId,
      "data-mapping": "specific", "data-term": it.id, "data-strict": "1", "data-reactions-enabled": "1", "data-emit-metadata": "0",
      "data-input-position": "top", "data-theme": "preferred_color_scheme", "data-lang": "en", crossorigin: "anonymous" };
    for (const [k, v] of Object.entries(attrs)) s.setAttribute(k, v);
    s.async = true;
    box.appendChild(s);
  }

  $("addForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const u = $("addUrl").value.trim();
    if (!/^https?:\/\//.test(u)) { $("addUrl").focus(); return; }
    const body = `url: ${u}\ncategory: \ntags: \nstar: no\n\nLeave category and tags empty to let the crawler guess them.`;
    window.open(`https://github.com/${C.repo}/issues/new?labels=add&title=${encodeURIComponent("Add: " + u)}&body=${encodeURIComponent(body)}`, "_blank", "noopener");
    $("addUrl").value = "";
  });
})();
