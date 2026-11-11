#!/usr/bin/env python3
"""Turn X post IDs (collected from a logged-in search in the owner's browser) into candidate records,
reading each post through the public api.fxtwitter.com.

Usage: x_hydrate.py IDS.txt [IDS2.txt ...]   -> crawler/work/browser_x.jsonl (appends, skips known ids)
"""
import json, os, re, sys, time, urllib.request
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "work", "browser_x.jsonl")


def get(i):
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"https://api.fxtwitter.com/status/{i}", headers={"User-Agent": "weight-space-reader/0.1"}), timeout=30) as r:
                return json.load(r).get("tweet")
        except Exception as ex:
            if getattr(ex, "code", None) == 404:
                return None
            time.sleep(2 * (k + 1))
    return None


def main():
    ids = []
    for f in sys.argv[1:]:
        ids += open(f).read().split()
    have = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            have.add(json.loads(line)["key"])
    n = 0
    with open(OUT, "a") as f:
        for i in dict.fromkeys(ids):
            if f"x:{i}" in have:
                continue
            t = get(i)
            if not t:
                continue
            who = t["author"]["screen_name"]
            text = t.get("text") or ""
            art = (t.get("article") or {})
            if art.get("title"):
                text = (art.get("title") + ". " + text).strip()
            clean = re.sub(r"https?://\S+", "", text).strip()
            try:
                day = parsedate_to_datetime(t["created_at"]).date().isoformat()
            except Exception:
                day = ""
            q = (t.get("quote") or {}).get("id")
            links = [u.get("replacement") or u.get("expanded_url") or u.get("url") for u in ((t.get("raw_text") or {}).get("facets") or []) if isinstance(u, dict) and u.get("type") == "url"]
            rec = dict(key=f"x:{i}", type="post", title=f"@{who}: " + clean[:110] + ("…" if len(clean) > 110 else ""), url=f"https://x.com/{who}/status/{i}",
                       date=day, authors=["@" + who], abstract=clean[:1200], quote=f"x:{q}" if q else None, links=links, likes=t.get("likes"),
                       replying_to=t.get("replying_to_status"), via=["browser-search"])
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
            if n % 50 == 0:
                print("hydrated", n, flush=True)
            time.sleep(0.3)
    print("DONE", n)


if __name__ == "__main__":
    main()
