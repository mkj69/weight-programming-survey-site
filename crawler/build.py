#!/usr/bin/env python3
"""Merge classified items into data/items.json (links and metadata only).

- De-duplicates by arXiv id, DOI, normalised URL and normalised title.
- Picks how each item is shown in the reader: pdf, frame, tweet, github, hf, reddit, youtube, or none.
- Applies data/overrides.json ({id: {"star": true, "tags": [...], "cats": [...], "hide": true}}).
- Keeps items already in data/items.json (the daily job only adds).
"""
import argparse, datetime, hashlib, json, os, re, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.path.join(HERE, "work")
DATA = os.path.join(ROOT, "data")
CJK = re.compile(r"[぀-ヿ一-鿿＀-￯]")
NO_FRAME = {"github.com", "huggingface.co", "x.com", "twitter.com", "www.reddit.com", "reddit.com", "opper.ai", "arxiv.org", "www.youtube.com", "youtube.com",
            "openreview.net", "dl.acm.org", "ieeexplore.ieee.org", "www.sciencedirect.com", "link.springer.com", "www.nature.com", "medium.com"}


def canon(u):
    """Canonical URL: one item per GitHub repo, no tracking query, fragment or trailing slash."""
    u = (u or "").strip()
    m = re.match(r"https?://github\.com/([^/#?]+/[^/#?]+)", u)
    if m:
        return "https://github.com/" + m.group(1).removesuffix(".git")
    u = re.sub(r"#.*$", "", u)
    u = re.sub(r"[?&](utm_[^=&]+|ref|s|a)=[^&]*", "", u).rstrip("?&")
    u = re.sub(r"/index\.html?$", "/", u)
    return u.rstrip("/")


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())[:120]


def item_id(r):
    k = r["key"]
    if k.startswith("sv:"):
        u = r["url"]
        m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9.]+)", u)
        if m:
            return "arxiv:" + re.sub(r"v\d+$", "", m.group(1))
        m = re.search(r"(?:x|twitter)\.com/[^/]+/status/(\d+)", u)
        if m:
            return "x:" + m.group(1)
        m = re.search(r"news\.ycombinator\.com/item\?id=(\d+)", u)
        if m:
            return "hn:" + m.group(1)
        m = re.match(r"https://github\.com/([^/]+/[^/#?]+)", u)
        if m:
            return "gh:" + m.group(1).lower()
        return "url:" + hashlib.sha1(u.encode()).hexdigest()[:12]
    return k


_frame_cache = {}


ALWAYS_FRAME = set()


def frameable(url, cache):
    host = urllib.parse.urlparse(url).netloc.lower()
    if host in ALWAYS_FRAME:
        return True
    if not host or host in NO_FRAME:
        return False
    if host in cache:
        return cache[host]
    ok = False
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            xfo = (r.headers.get("X-Frame-Options") or "").lower()
            csp = (r.headers.get("Content-Security-Policy") or "").lower()
            fa = re.search(r"frame-ancestors([^;]*)", csp)
            ok = not xfo and not (fa and "*" not in fa.group(1))
            if r.geturl().startswith("http://"):
                ok = False  # mixed content would be blocked on an https page
    except Exception:
        ok = False
    cache[host] = ok
    return ok


def view(r, cache):
    u = r["url"] or ""
    if r.get("arxiv"):
        return "pdf", f"https://arxiv.org/pdf/{r['arxiv']}"
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9.]+)", u)
    if m:
        return "pdf", f"https://arxiv.org/pdf/{m.group(1)}"
    if re.search(r"(?:x|twitter)\.com/[^/]+/status/\d+", u):
        return "tweet", None
    m = re.match(r"https://github\.com/([^/]+/[^/#?]+)", u)
    if m and r["type"] == "code":
        return "github", m.group(1)
    m = re.match(r"https://huggingface\.co/((?:datasets/|spaces/)?[^/]+/[^/#?]+)", u)
    if m:
        return "hf", m.group(1)
    m = re.search(r"news\.ycombinator\.com/item\?id=(\d+)", u)
    if m:
        return "hn", m.group(1)
    m = re.match(r"https://(?:www\.)?reddit\.com(/r/[^/]+/comments/[^/]+)", u)
    if m:
        return "reddit", f"https://www.redditmedia.com{m.group(1)}/?ref_source=embed&embed=true"
    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{11})", u)
    if m:
        return "youtube", f"https://www.youtube-nocookie.com/embed/{m.group(1)}"
    if r.get("pdf") and r["pdf"].startswith("https://") and frameable(r["pdf"], cache):
        return "pdf", r["pdf"]
    if u.startswith("https://") and frameable(u, cache):
        return "frame", None
    return "none", None


def clean_authors(a):
    out = []
    for x in a or []:
        x = (x or "").strip()
        if x and len(x) < 60 and ";" not in x and not CJK.search(x):
            out.append(x)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", default=os.path.join(WORK, "classified.jsonl"))
    ap.add_argument("--fresh", action="store_true", help="ignore the existing data/items.json")
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    tax = json.load(open(os.path.join(HERE, "taxonomy.json")))
    cache_p = os.path.join(DATA, "frame_cache.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    items_p = os.path.join(DATA, "items.json")
    old = {} if a.fresh or not os.path.exists(items_p) else {i["id"]: i for i in json.load(open(items_p))["items"]}
    seen_title = {norm_title(i["t"]): i["id"] for i in old.values() if i["y"] == "paper"}
    seen_url = {canon(i["u"]): i["id"] for i in old.values()}
    items = dict(old)
    recs = [json.loads(l) for l in open(a.inp)] if os.path.exists(a.inp) else []
    # Dates of HN/Reddit posts that link to a page, used when the page itself has no date.
    link_date = {}
    for r in recs:
        if r.get("link") and r.get("date"):
            link_date.setdefault(canon(r["link"]), r["date"])
    # surveys and rule matches first, so their categories win over duplicates
    recs.sort(key=lambda r: {"survey": 0, "rule": 1, "llm": 2}.get(r.get("how"), 3))
    for r in recs:
        if not r.get("url") or not r.get("title") or CJK.search(r["title"]):
            continue
        r = dict(r, url=canon(r["url"]))
        if r["url"].startswith("https://github.com/"):
            r["title"] = r["url"].split("github.com/", 1)[1]
            r["type"] = "code"
        # Dates: OpenAlex gives YYYY-01-01 when only the year is known; arXiv ids carry the month.
        dt = (r.get("date") or "")[:10]
        aid = r.get("arxiv") or ""
        if (not dt or dt.endswith("-01-01")) and re.match(r"\d{4}\.\d{4,5}$", aid):
            dt = f"20{aid[:2]}-{aid[2:4]}"
        elif dt.endswith("-01-01"):
            dt = link_date.get(r["url"]) or dt[:4]
        r["date"] = dt
        iid = item_id(r)
        nt = norm_title(r["title"]) if r["type"] == "paper" else None
        dup = items.get(iid) or (items.get(seen_title.get(nt)) if nt else None) or items.get(seen_url.get(r["url"]))
        if dup:
            dup["c"] = sorted(set(dup["c"]) | set(r["cats"]))
            dup["g"] = sorted(set(dup["g"]) | set(r["tags"]))
            continue
        k, e = view(r, cache)
        text = (r.get("abstract") or "").strip()
        rec = dict(id=iid, t=re.sub(r"\s+", " ", r["title"]).strip(), u=r["url"], k=k, y=r["type"], c=sorted(set(r["cats"])), g=sorted(set(r["tags"])),
                   d=(r.get("date") or "")[:10], a=", ".join(clean_authors(r.get("authors"))[:8]), v=r.get("venue") or r.get("subreddit") or "",
                   n=r.get("cites") or r.get("stars") or r.get("points") or 0, s=False, added=datetime.date.today().isoformat())
        if e:
            rec["e"] = e
        if text and (r.get("arxiv") or r["type"] == "code") and not CJK.search(text):
            rec["x"] = text[:420] + ("…" if len(text) > 420 else "")
        items[iid] = rec
        if nt:
            seen_title[nt] = iid
        seen_url[r["url"]] = iid
    by_t = {}
    for i in items.values():
        if i["y"] != "discussion":
            by_t.setdefault(norm_title(i["t"]), i)
    by_u = {i["u"]: i for i in items.values() if i["y"] != "discussion"}
    for iid in [k for k, i in items.items() if i["y"] == "discussion" and i["k"] == "hn"]:
        i = items[iid]
        host = by_t.get(norm_title(i["t"]))
        if host is not None:
            host["hn"] = i["e"]
            del items[iid]
    ov_p = os.path.join(DATA, "overrides.json")
    ov = json.load(open(ov_p)) if os.path.exists(ov_p) else {}
    for iid, o in ov.items():
        if iid in items:
            if o.get("hide"):
                del items[iid]
                continue
            it = items[iid]
            if "star" in o:
                it["s"] = bool(o["star"])
            if o.get("tags"):
                it["g"] = sorted(set(o["tags"]))
            if o.get("cats"):
                it["c"] = sorted(set(o["cats"]))
            if o.get("title"):
                it["t"] = o["title"]
            if o.get("date"):
                it["d"] = o["date"]
    # Classic works: mark them (adding any that the crawl missed) and write data/map.json.
    classics = json.load(open(os.path.join(HERE, "classics.json")))
    by_title = {norm_title(i["t"]): i for i in items.values() if i["y"] != "discussion"}
    by_url = {i["u"].rstrip("/"): i for i in items.values()}
    pool = {}
    for name in ("oa_candidates.jsonl", "arxiv_candidates.jsonl"):
        pth = os.path.join(WORK, name)
        if os.path.exists(pth):
            for line in open(pth):
                r = json.loads(line)
                pool.setdefault(norm_title(r["title"]), r)
    nodes = []
    for c in classics:
        it = (by_url.get(c.get("url", "").rstrip("/")) if c.get("url") else None) or by_title.get(norm_title(c["title"]))
        if it is not None and it["y"] == "discussion":
            it = None
        cand = pool.get(norm_title(c["title"]))
        if it is None and cand and not c.get("url"):
            r = dict(cand, type="paper", cats=[c["cat"]], tags=[], key=f"arxiv:{cand['arxiv']}" if cand.get("arxiv") else f"oa:{cand['oa']}")
            r["url"] = f"https://arxiv.org/abs/{cand['arxiv']}" if cand.get("arxiv") else (cand.get("url") or cand.get("doi"))
            if r["url"]:
                k, e = view(r, cache)
                it = dict(id=r["key"], t=cand["title"], u=r["url"], k=k, y="paper", c=[c["cat"]], g=[], d=(cand.get("date") or "")[:10],
                          a=", ".join(clean_authors(cand.get("authors"))[:8]), v=cand.get("venue") or "", n=cand.get("cites") or 0, s=False,
                          added=datetime.date.today().isoformat())
                if e:
                    it["e"] = e
                items[it["id"]] = it
        if it is None:
            u = c.get("url") or f"https://scholar.google.com/scholar?q={urllib.parse.quote(c['title'])}"
            iid = "classic:" + c["key"]
            k, e = view(dict(url=u, type="blog" if c.get("url") and "pdf" not in u else "paper"), cache)
            it = dict(id=iid, t=c["title"], u=u, k=k, y="paper" if c["year"] < 2026 else "blog", c=[c["cat"]], g=[], d=str(int(c["year"])), a=c["who"], v="", n=0, s=False,
                      added=datetime.date.today().isoformat())
            if e:
                it["e"] = e
            items[iid] = it
        it["cl"] = True
        if c["cat"] not in it["c"]:
            it["c"] = sorted(set(it["c"] + [c["cat"]]))
        nodes.append(dict(key=c["key"], year=c["year"], cat=c["cat"], short=c["short"], title=c["title"], who=c["who"], note=c["note"], id=it["id"], url=it["u"], date=it["d"]))
    json.dump(dict(categories=tax["categories"], nodes=nodes, edges=[[f, c["key"]] for c in classics for f in c.get("from", [])]),
              open(os.path.join(DATA, "map.json"), "w"), ensure_ascii=False, indent=0)
    # Group X posts under the post or work they react to (see reactions.py).
    rx_p = os.path.join(DATA, "reactions.json")
    rx = json.load(open(rx_p)) if os.path.exists(rx_p) else {}
    for i in items.values():
        i.pop("rof", None); i.pop("rx", None)
    def root(h, seen=()):
        r = rx.get(h, {}).get("host")
        return h if not r or r in seen or r not in items else root(r, seen + (h,))
    for iid, r in rx.items():
        if iid in items and r.get("host") in items:
            host = root(r["host"])
            if host == iid:
                continue
            items[iid]["rof"] = host
            items[iid]["dp"] = r.get("depth", "reaction")
            items[host].setdefault("rx", []).append(iid)
    for i in items.values():
        if "rx" in i:
            i["rx"].sort(key=lambda j: (items[j].get("dp") != "analysis", items[j]["d"]))
    sm_p = os.path.join(DATA, "summaries.json")
    sums = json.load(open(sm_p)) if os.path.exists(sm_p) else {}
    for i in items.values():
        if sums.get(i["id"]):
            i["sm"] = sums[i["id"]]
        elif i.get("x") and "sm" not in i:
            first = re.split(r"(?<=[.!?])\s", i["x"], maxsplit=1)[0]
            i["sm"] = first[:220]
    out = dict(updated=datetime.date.today().isoformat(), categories=tax["categories"], tags=tax["tags"], types=tax["types"],
               items=sorted(items.values(), key=lambda i: i["d"] or "", reverse=True))
    json.dump(out, open(items_p, "w"), ensure_ascii=False, separators=(",", ":"))
    json.dump(cache, open(cache_p, "w"), indent=0, sort_keys=True)
    from collections import Counter
    print("items", len(items), Counter(i["y"] for i in items.values()), Counter(i["k"] for i in items.values()))


if __name__ == "__main__":
    main()
