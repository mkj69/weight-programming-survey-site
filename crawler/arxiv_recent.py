#!/usr/bin/env python3
"""Search arXiv directly for recent papers (OpenAlex lags by days to weeks).

Usage: arxiv_recent.py --since YYYY-MM-DD [--out FILE]
Output lines use the same fields as papers.py so build.py can merge them.
"""
import argparse, json, os, re, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
NS = {"a": "http://www.w3.org/2005/Atom"}
QUERIES = [
    'all:"weight space"', 'all:"weight-space"', 'all:"model editing"', 'all:"knowledge editing"', 'all:"task arithmetic"',
    'all:"task vector"', 'all:"model merging"', 'all:"fast weight"', 'all:"fast weights"', 'all:hypernetwork', 'all:"self-referential"',
    'all:"compiled transformer"', 'all:RASP', 'all:tracr', 'all:"transformer program"', 'all:"model diffing"', 'all:"weight difference"',
    'all:"neural functional"', 'all:"parameter generation"', 'all:"weight generation"', 'all:"edit the weights"', 'all:"neural network weights"',
]


def fetch(q, start):
    u = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": q, "start": start, "max_results": 200, "sortBy": "submittedDate", "sortOrder": "descending"})
    for k in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "weight-space-reader-crawler/0.1"}), timeout=90) as r:
                return ET.fromstring(r.read())
        except Exception:
            time.sleep(10 * (k + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True)
    ap.add_argument("--out", default=os.path.join(HERE, "work", "arxiv_candidates.jsonl"))
    a = ap.parse_args()
    out = {}
    for q in QUERIES:
        start = 0
        while start < 2000:
            root = fetch(q, start)
            if root is None:
                break
            entries = root.findall("a:entry", NS)
            old = False
            for e in entries:
                pub = e.findtext("a:published", "", NS)[:10]
                if pub < a.since:
                    old = True
                    break
                aid = re.sub(r"v\d+$", "", e.findtext("a:id", "", NS).rsplit("/abs/", 1)[-1])
                rec = out.setdefault(aid, dict(oa=None, title=re.sub(r"\s+", " ", e.findtext("a:title", "", NS)).strip(), date=pub,
                    authors=[x.findtext("a:name", "", NS) for x in e.findall("a:author", NS)][:12], venue="arXiv", doi=None, arxiv=aid,
                    url=f"https://arxiv.org/abs/{aid}", pdf=f"https://arxiv.org/pdf/{aid}", abstract=re.sub(r"\s+", " ", e.findtext("a:summary", "", NS)).strip()[:3000],
                    cites=None, kind="preprint", via=[]))
                rec["via"].append(f"arxiv:{q}")
            if old or len(entries) < 200:
                break
            start += 200
            time.sleep(3.5)
        print(q, len(out), flush=True)
        time.sleep(3.5)
    with open(a.out, "w") as f:
        for r in out.values():
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("DONE", len(out))


if __name__ == "__main__":
    main()
