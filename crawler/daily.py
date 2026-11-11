#!/usr/bin/env python3
"""Daily update (run by GitHub Actions at 8:00 America/Chicago).

Looks for items published or posted in the last few days, keeps the ones whose titles match the
category rules, and adds them to data/items.json. No LLM is used here.
"""
import datetime, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
ROOT = os.path.dirname(HERE)


def run(*args):
    print("+", " ".join(args), flush=True)
    r = subprocess.run([sys.executable, *args], cwd=ROOT)
    if r.returncode != 0:
        print("step failed, continuing", flush=True)


def main():
    sp = os.path.join(ROOT, "data", "settings.json")
    if os.path.exists(sp) and json.load(open(sp)).get("daily_updates") == "off":
        print("Daily updates are paused (data/settings.json). Nothing to do.")
        return
    os.makedirs(WORK, exist_ok=True)
    for f in os.listdir(WORK):
        if f.endswith(".jsonl"):
            os.remove(os.path.join(WORK, f))
    items_p = os.path.join(ROOT, "data", "items.json")
    last = json.load(open(items_p))["updated"] if os.path.exists(items_p) else "2026-11-01"
    since = (datetime.date.fromisoformat(last) - datetime.timedelta(days=3)).isoformat()
    run("crawler/other.py", "--since", since)
    run("crawler/arxiv_recent.py", "--since", since)
    run("crawler/x_accounts.py", "--since", since)
    if os.environ.get("OPENALEX_API_KEY"):
        run("crawler/papers.py", "--since", since)
    run("crawler/classify.py")
    run("crawler/build.py")


if __name__ == "__main__":
    main()
