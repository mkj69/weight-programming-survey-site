#!/usr/bin/env python3
"""Handle an "add" or "edit" issue from the site.

add issue body:   url: <link> / category: <wsp|compile|edit|fast|wsl, optional> / tags: <a, b> / star: yes|no
edit issue body:  id: <item id> / star: yes|no / tags: <a, b> / category: <...> / hide: yes
Writes data/overrides.json (edits) or a one-line candidate file that build.py merges (adds).
Prints a short result message for the issue comment.
"""
import json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from rules import score, tags_for, TAG_CAT

UA = {"User-Agent": "Mozilla/5.0 (weight-space-reader)"}


def field(body, name):
    m = re.search(rf"^\s*{name}\s*:\s*(.*)$", body, re.M | re.I)
    return m.group(1).strip() if m else ""


def get(url, raw=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        b = r.read()
        return b.decode("utf-8", "replace") if raw else json.loads(b)


def meta(url):
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9.]+)", url)
    if m:
        x = get(f"https://export.arxiv.org/api/query?id_list={m.group(1)}", raw=True)
        t = re.findall(r"<title>(.*?)</title>", x, re.S)
        a = re.findall(r"<name>(.*?)</name>", x)
        d = re.findall(r"<published>(\d{4}-\d\d-\d\d)", x)
        s = re.findall(r"<summary>(.*?)</summary>", x, re.S)
        return dict(type="paper", title=re.sub(r"\s+", " ", t[-1]).strip(), authors=a[:8], date=d[0] if d else "", arxiv=re.sub(r"v\d+$", "", m.group(1)),
                    abstract=re.sub(r"\s+", " ", s[0]).strip() if s else "", url=f"https://arxiv.org/abs/{m.group(1)}")
    m = re.search(r"(?:x|twitter)\.com/([^/]+)/status/(\d+)", url)
    if m:
        t = get(f"https://api.fxtwitter.com/status/{m.group(2)}")["tweet"]
        text = re.sub(r"https?://\S+", "", t.get("text") or "").strip()
        return dict(type="post", title=f"@{t['author']['screen_name']}: " + text[:110], authors=["@" + t["author"]["screen_name"]],
                    date="", abstract=text, url=f"https://x.com/{m.group(1)}/status/{m.group(2)}")
    m = re.match(r"https://github\.com/([^/]+/[^/#?]+)", url)
    if m:
        r = json.loads(subprocess.run(["gh", "api", f"repos/{m.group(1)}"], capture_output=True, text=True).stdout or "{}")
        return dict(type="code", title=r.get("full_name", m.group(1)), authors=[m.group(1).split("/")[0]], date=(r.get("created_at") or "")[:10],
                    abstract=r.get("description") or "", url=f"https://github.com/{m.group(1)}", stars=r.get("stargazers_count"))
    m = re.match(r"https://huggingface\.co/((?:datasets/|spaces/)?[^/]+/[^/#?]+)", url)
    if m:
        return dict(type="dataset" if m.group(1).startswith("datasets/") else "model", title=m.group(1).split("/", 1)[-1] if m.group(1).startswith(("datasets/", "spaces/")) else m.group(1),
                    authors=[], date="", abstract="", url=url)
    m = re.search(r"news\.ycombinator\.com/item\?id=(\d+)", url)
    if m:
        h = get(f"https://hn.algolia.com/api/v1/items/{m.group(1)}")
        return dict(type="discussion", title=h.get("title") or url, authors=[h.get("author")], date=(h.get("created_at") or "")[:10], abstract="", url=url)
    page = get(url, raw=True)
    t = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', page) or re.search(r"<title[^>]*>(.*?)</title>", page, re.S)
    d = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d\d-\d\d)', page) or re.search(r'article:published_time"[^>]+content="(\d{4}-\d\d-\d\d)', page)
    import html as H
    typ = "video" if "youtube.com" in url or "youtu.be" in url else ("paper" if url.lower().endswith(".pdf") else "blog")
    return dict(type=typ, title=H.unescape(re.sub(r"\s+", " ", t.group(1))).strip() if t else url, authors=[], date=d.group(1) if d else "", abstract="", url=url)


def main():
    kind, body = sys.argv[1], open(sys.argv[2]).read()
    ov_p = os.path.join(ROOT, "data", "overrides.json")
    ov = json.load(open(ov_p)) if os.path.exists(ov_p) else {}
    star = field(body, "star").lower()
    tags = [t.strip() for t in field(body, "tags").split(",") if t.strip()]
    cats = [c.strip() for c in re.split(r"[,\s]+", field(body, "category")) if c.strip() in TAG_CAT]
    if kind == "settings":
        val = field(body, "daily_updates").lower()
        if val not in ("on", "off"):
            print("Write `daily_updates: on` or `daily_updates: off`.")
            sys.exit(1)
        sp = os.path.join(ROOT, "data", "settings.json")
        st = json.load(open(sp)) if os.path.exists(sp) else {}
        st["daily_updates"] = val
        json.dump(st, open(sp, "w"), indent=1)
        print("Daily updates are now **" + ("paused" if val == "off" else "on") + "**.")
        return
    m = re.search(r"```json\s*(\{.*?\})\s*```", body, re.S)
    if kind == "edit" and m:
        edits = json.loads(m.group(1))
        for iid, e in edits.items():
            o = ov.setdefault(iid, {})
            if "star" in e:
                o["star"] = bool(e["star"])
            if isinstance(e.get("tags"), list):
                o["tags"] = [str(t) for t in e["tags"]][:20]
        json.dump(ov, open(ov_p, "w"), indent=1, ensure_ascii=False)
        subprocess.run([sys.executable, "crawler/build.py", "--inp", "/dev/null"], cwd=ROOT, check=True)
        print(f"Saved edits to {len(edits)} item(s).")
        return
    if kind == "edit":
        iid = field(body, "id")
        o = ov.setdefault(iid, {})
        if star in ("yes", "no"):
            o["star"] = star == "yes"
        if tags:
            o["tags"] = tags
        if cats:
            o["cats"] = cats
        if field(body, "hide").lower() == "yes":
            o["hide"] = True
        json.dump(ov, open(ov_p, "w"), indent=1, ensure_ascii=False)
        subprocess.run([sys.executable, "crawler/build.py", "--inp", "/dev/null"], cwd=ROOT, check=True)
        print(f"Updated `{iid}`.")
        return
    url = field(body, "url")
    if not re.match(r"https?://", url):
        print("No valid `url:` line found.")
        sys.exit(1)
    m = meta(url)
    s = score(m["title"], m.get("abstract"))
    cats = cats or [c for c, v in s.items() if v == 2] or list(s) or ["wsp"]
    tags = tags or tags_for(cats, m["title"], m.get("abstract"))
    rec = dict(m, key="manual:" + url, cats=cats, tags=tags, how="manual")
    p = os.path.join(HERE, "work", "manual.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(json.dumps(rec, ensure_ascii=False) + "\n")
    subprocess.run([sys.executable, "crawler/build.py", "--inp", p], cwd=ROOT, check=True)
    items = json.load(open(os.path.join(ROOT, "data", "items.json")))["items"]
    hit = next((i for i in items if i["u"].rstrip("/") == rec["url"].rstrip("/")), None)
    if hit and star in ("yes", "no"):
        ov.setdefault(hit["id"], {})["star"] = star == "yes"
        json.dump(ov, open(ov_p, "w"), indent=1, ensure_ascii=False)
        subprocess.run([sys.executable, "crawler/build.py", "--inp", "/dev/null"], cwd=ROOT, check=True)
    print(f"Added **{m['title']}** as `{hit['id'] if hit else '?'}` in {', '.join(cats)}." if hit else "Already in the collection.")


if __name__ == "__main__":
    main()
