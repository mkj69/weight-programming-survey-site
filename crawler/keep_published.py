#!/usr/bin/env python3
"""After a local --fresh rebuild, put back items that exist only in the published data
(for example items the daily job added on GitHub), so a full rebuild never drops them.

Usage: keep_published.py [git-ref]   (default origin/main)
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
pub = json.loads(subprocess.run(["git", "show", f"{ref}:data/items.json"], cwd=ROOT, capture_output=True, text=True, check=True).stdout)
p = os.path.join(ROOT, "data", "items.json")
cur = json.load(open(p))
have = {i["id"] for i in cur["items"]}
urls = {i["u"] for i in cur["items"]}
added = [i for i in pub["items"] if i["id"] not in have and i["u"] not in urls]
cur["items"] = sorted(cur["items"] + added, key=lambda i: i["d"] or "", reverse=True)
json.dump(cur, open(p, "w"), ensure_ascii=False, separators=(",", ":"))
print("restored", len(added), "items from", ref)
