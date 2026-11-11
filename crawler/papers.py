#!/usr/bin/env python3
"""Collect candidate papers from OpenAlex: seed works, works citing them, works they cite,
and keyword searches. Output: crawler/work/oa_candidates.jsonl (one work per line).

Relevance is decided later (classify.py); this step only gathers candidates.
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
API = "https://api.openalex.org/works"
UA = {"User-Agent": "weight-space-reader-crawler/0.1"}
KEY = os.environ.get("OPENALEX_API_KEY")
if not KEY and os.path.exists(os.path.join(WORK, ".env")):
    for _l in open(os.path.join(WORK, ".env")):
        if _l.startswith("OPENALEX_API_KEY="):
            KEY = _l.strip().split("=", 1)[1]
if KEY:
    UA["Authorization"] = "Bearer " + KEY
FIELDS = "id,display_name,publication_date,authorships,primary_location,locations,ids,abstract_inverted_index,cited_by_count,type,referenced_works"

QUERIES = [
    "weight space", "weight-space learning", "neural network weights as input", "learning on neural network weights",
    "model zoo neural network weights", "weight generation diffusion", "parameter generation neural network",
    "hypernetwork", "fast weights", "fast weight programmer", "self-referential weight matrix", "self-modifying neural network",
    "linear attention fast weight", "test-time training hidden state", "meta-learning weight update rule",
    "model editing", "knowledge editing language model", "editing factual knowledge", "locate and edit",
    "task arithmetic", "task vector", "model merging", "weight averaging fine-tuned models", "weight interpolation",
    "model diffing", "weight difference fine-tuning", "parameter difference fine-tuned base model",
    "machine unlearning weight editing", "rank-one model editing",
    "compiled transformer", "RASP transformer program", "transformer programs interpretable", "compile program into transformer weights",
    "hand-crafted transformer weights", "looped transformer programmable computer", "neural network weights interpretability",
    "weight-space programming", "LLM edit neural network weights", "reading neural network weights",
    "weight symmetry permutation neural network", "neural functional network", "implicit neural representation weights classification",
]


def get(url, tries=6):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as ex:
            code = getattr(ex, "code", None)
            if code == 404:
                return None
            time.sleep(min(60, 3 * (k + 1) * (3 if code == 429 else 1)))
    raise RuntimeError("failed " + url)


def abstract(inv):
    if not inv:
        return ""
    pos = []
    for w, ps in inv.items():
        for p in ps:
            pos.append((p, w))
    return " ".join(w for _, w in sorted(pos))


def arxiv_id(w):
    for loc in [w.get("primary_location") or {}] + (w.get("locations") or []):
        u = (loc or {}).get("landing_page_url") or ""
        m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}|[a-z\-]+/[0-9]{7})", u)
        if m:
            return m.group(1)
    doi = (w.get("ids") or {}).get("doi") or ""
    m = re.search(r"10\.48550/arxiv\.(.+)$", doi, re.I)
    return m.group(1) if m else None


def slim(w, via):
    loc = w.get("primary_location") or {}
    src = (loc.get("source") or {}).get("display_name")
    return dict(
        oa=w["id"].rsplit("/", 1)[-1], title=w.get("display_name") or "", date=w.get("publication_date"),
        authors=[(a.get("author") or {}).get("display_name") for a in (w.get("authorships") or [])[:12]],
        venue=src, doi=(w.get("ids") or {}).get("doi"), arxiv=arxiv_id(w), url=loc.get("landing_page_url"),
        pdf=loc.get("pdf_url"), abstract=abstract(w.get("abstract_inverted_index"))[:3000],
        cites=w.get("cited_by_count"), kind=w.get("type"), via=[via],
    )


def pages(params, limit):
    cursor, n = "*", 0
    while cursor and n < limit:
        q = dict(params, cursor=cursor, **{"per-page": 200, "select": FIELDS})
        try:
            d = get(API + "?" + urllib.parse.urlencode(q))
        except RuntimeError as ex:
            print("page failed, moving on:", str(ex)[:120], flush=True)
            return
        if not d:
            return
        for w in d["results"]:
            yield w
            n += 1
        cursor = d["meta"].get("next_cursor")
        if not d["results"]:
            return


def recent(since, out_path):
    """Daily mode: keyword searches restricted to works published since a date."""
    found = {}
    for q in QUERIES:
        for w in pages({"search": q, "filter": f"from_publication_date:{since}"}, 400):
            s = slim(w, f"q:{q}")
            found.setdefault(s["oa"], s)
    with open(out_path, "w") as f:
        for s in found.values():
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print("recent", len(found), flush=True)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--since":
        return recent(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else os.path.join(WORK, "oa_candidates.jsonl"))
    os.makedirs(WORK, exist_ok=True)
    seeds = json.load(open(os.path.join(HERE, "seeds.json")))
    found, done = {}, set()
    ck, dk = os.path.join(WORK, "oa_candidates.jsonl"), os.path.join(WORK, "oa_done.json")
    if os.path.exists(ck):
        for line in open(ck):
            r = json.loads(line); found[r["oa"]] = r
    if os.path.exists(dk):
        done = set(json.load(open(dk)))

    def save(step):
        done.add(step)
        with open(ck + ".tmp", "w") as f:
            for s_ in found.values():
                f.write(json.dumps(s_, ensure_ascii=False) + "\n")
        os.replace(ck + ".tmp", ck)
        json.dump(sorted(done), open(dk, "w"))

    def add(w, via):
        s = slim(w, via)
        if s["oa"] in found:
            if via not in found[s["oa"]]["via"]:
                found[s["oa"]]["via"].append(via)
        else:
            found[s["oa"]] = s

    resolved = []
    for cat, titles in seeds.items():
        for t in titles:
            d = get(API + "?" + urllib.parse.urlencode({"search": t, "per-page": 5, "select": FIELDS}))
            best = max((d or {}).get("results", []), key=lambda w: SequenceMatcher(None, t.lower(), (w.get("display_name") or "").lower()).ratio(), default=None)
            ok = best and SequenceMatcher(None, t.lower(), (best.get("display_name") or "").lower()).ratio() > 0.8
            print(("SEED " if ok else "MISS ") + cat + " | " + t + (" -> " + best["id"] if ok else ""), flush=True)
            if ok:
                add(best, f"seed:{cat}")
                resolved.append((cat, best))
    json.dump([(c, w["id"]) for c, w in resolved], open(os.path.join(WORK, "seeds_resolved.json"), "w"))

    for cat, w in resolved:
        wid = w["id"].rsplit("/", 1)[-1]
        if f"x:{wid}" in done:
            continue
        n = 0
        for c in pages({"filter": f"cites:{wid}"}, 4000):
            add(c, f"cites:{cat}:{wid}")
            n += 1
        refs = [r.rsplit("/", 1)[-1] for r in (w.get("referenced_works") or [])]
        for i in range(0, len(refs), 50):
            d = get(API + "?" + urllib.parse.urlencode({"filter": "openalex:" + "|".join(refs[i:i + 50]), "per-page": 50, "select": FIELDS}))
            for r in (d or {}).get("results", []):
                add(r, f"ref:{cat}:{wid}")
        print(f"expand {cat} {wid} cites={n} refs={len(refs)} total={len(found)}", flush=True)
        save(f"x:{wid}")

    for q in QUERIES:
        if f"q:{q}" in done:
            continue
        n = 0
        for w in pages({"search": q}, 1000):
            add(w, f"q:{q}")
            n += 1
        print(f"query {q!r} {n} total={len(found)}", flush=True)
        save(f"q:{q}")
    print("DONE", len(found), flush=True)


if __name__ == "__main__":
    main()
