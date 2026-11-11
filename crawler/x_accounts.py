#!/usr/bin/env python3
"""Recent posts from tracked X accounts, read through the public api.fxtwitter.com (no login).

Usage: x_accounts.py --since YYYY-MM-DD
Keeps posts whose text matches the topic keywords. Output: crawler/work/x_candidates.jsonl
"""
import argparse, json, os, re, sys, time, urllib.request
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS = """divagr1925 TheVixhal dbreunig rikiyatakehi lateinteraction a1zhang jayden_teoh_ simonw AlexKrentsel SchmidhuberAI honnibal physicsrob
QwenDevs Alibaba_Qwen karpathy JustinAngel giffmana Yuchenj_UW ivanfioravanti Marktechpost ChristosTzamos percepta_ai NeelNanda5 ch402 davidbau
jxmnop natolambert neilkale deepaksinghml _doubleAI_ miriamgonp willdepue alon_rag gabepereyra bradenjhancock o__jerry__o xingyudang jacsebl csinva
emollick kzkirie FrancoisChauba1 xingjianbai neural_avb yoonholeee HaozeHe_Hector NielsRogge akhaliq""".split()
TOPIC = re.compile(r"weight[- ]space|qwenputer|qwen(?:fs|gpu|pu|x86)\b|nesformer|torchwright|tracr|\bRASP\b|compiled? (?:in)?to (?:the )?weights|"
                   r"(?:read|write|edit)(?:s|ing)? .{0,25}weights|hand-?(?:written|crafted) weights|fast weights?|hypernetwork|model editing|knowledge editing|"
                   r"task (?:vector|arithmetic)|model merging|model diffing|weightprogrambench|self-referential", re.I)


def get(url):
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "weight-space-reader/0.1"}), timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 * (k + 1))
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True)
    ap.add_argument("--out", default=os.path.join(HERE, "work", "x_candidates.jsonl"))
    a = ap.parse_args()
    out = {}
    for h in ACCOUNTS:
        cursor = None
        for page in range(4):
            d = get(f"https://api.fxtwitter.com/2/profile/{h}/statuses" + (f"?cursor={cursor}" if cursor else ""))
            rs = d.get("results") or []
            stop = False
            for t in rs:
                try:
                    day = parsedate_to_datetime(t["created_at"]).date().isoformat()
                except Exception:
                    continue
                if day < a.since:
                    stop = True
                    continue
                text = t.get("text") or ""
                if not TOPIC.search(text):
                    continue
                who = t["author"]["screen_name"]
                clean = re.sub(r"https?://\S+", "", text).strip()
                out[t["id"]] = dict(key="x:" + t["id"], type="post", title=f"@{who}: " + clean[:110] + ("…" if len(clean) > 110 else ""),
                                    url=f"https://x.com/{who}/status/{t['id']}", date=day, authors=["@" + who], abstract=clean[:600], via=[f"x:{h}"])
            cursor = (d.get("cursor") or {}).get("bottom")
            if stop or not cursor or not rs:
                break
        print(h, len(out), flush=True)
    with open(a.out, "w") as f:
        for r in out.values():
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("DONE", len(out))


if __name__ == "__main__":
    main()
