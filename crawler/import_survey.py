#!/usr/bin/env python3
"""Import the hand-collected survey items (private repo) as link records with English titles.

Reads ../weight-programming-survey/{tools/rows.json, raw/*.meta.json, raw/*.md}.
Writes crawler/work/survey_items.jsonl. No text from the sources is copied, only titles and links.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SURVEY = os.path.join(HERE, "..", "..", "weight-programming-survey")
CJK = re.compile(r"[぀-ヿ一-鿿＀-￯]")
TOPIC2CAT = {"wsp": "wsp", "qwenputer": "compile", "family": "compile", "derive": "compile", "compile": "compile", "percepta": "compile", "found": None}


def tweet_title(raw):
    m = re.search(r"^@@META @(\w+)", raw, re.M)
    handle = m.group(1) if m else "x"
    body = [l.strip() for l in raw.splitlines() if l.strip() and not l.startswith("@@META")]
    text = re.sub(r"https?://\S+", "", body[0] if body else "").strip()
    return f"@{handle}: " + (text[:110] + ("…" if len(text) > 110 else ""))


def main():
    rows = json.load(open(os.path.join(SURVEY, "tools", "rows.json")))
    out = []
    for r in rows:
        meta = json.load(open(os.path.join(SURVEY, "raw", r["id"] + ".meta.json")))
        raw = open(os.path.join(SURVEY, "raw", r["id"] + ".md"), errors="replace").read()
        kind, url = r["kind"], r["url"]
        title = None
        if kind == "tw":
            title, typ = tweet_title(raw), "post"
        elif kind == "arxiv":
            title, typ = meta.get("mtitle"), "paper"
        elif kind == "hn":
            title, typ = re.sub(r"^HN[：:]\s*", "", meta.get("title", "")), "discussion"
        elif kind == "reddit":
            title, typ = re.sub(r"^Reddit[：:]\s*", "", meta.get("title", "")), "discussion"
        elif kind == "hf":
            ref = meta["ref"]
            title = ref.replace("datasets/", "") + (" (dataset card)" if ref.startswith("datasets/") else " (model card)")
            typ = "dataset" if ref.startswith("datasets/") else "model"
        elif kind == "gh":
            repo, path = meta["ref"].split(":", 1)
            title = repo + ("" if path.lower() == "readme.md" else f" — {path}")
            typ = "code"
            url = f"https://github.com/{repo}" if path.lower() == "readme.md" else url
        else:
            title, typ = meta.get("mtitle"), "blog"
        if not title or CJK.search(title):
            heading = re.search(r"^#\s+(.+)$", raw, re.M)
            if heading and not CJK.search(heading.group(1)):
                title = heading.group(1).strip()
        if not title or CJK.search(title):
            title = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
        author = meta.get("mauthor") or (r.get("author") if not CJK.search(str(r.get("author"))) else "")
        author = "" if str(author) in ("见页面", "None") else re.sub(r"\s*[（(].*?[)）]", "", str(author))
        cat = TOPIC2CAT.get(r["topic"])
        out.append(dict(key="sv:" + r["id"], type=typ, title=title.strip(), url=url, date=(r.get("date") or "")[:10],
                        authors=[author] if author else [], abstract="", survey_topic=r["topic"], cat_hint=cat, cred=r["cred"], via=["survey"]))
    with open(os.path.join(HERE, "work", "survey_items.jsonl"), "w") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    bad = [o for o in out if CJK.search(o["title"] + " ".join(o["authors"]))]
    print(len(out), "items;", len(bad), "still contain CJK")
    for o in bad[:20]:
        print("  ", o["key"], o["title"][:80], o["authors"])


if __name__ == "__main__":
    main()
