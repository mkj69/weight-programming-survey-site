# Weight Space Reader

A reading list and reader for work on the **weight space of neural networks**: language models
that read and write weights, programs compiled into weights, weight editing and model diffs, fast
weights and self-modifying networks, and weight-space learning.

**Site:** https://mkj69.github.io/weight-programming-survey-site/
**Field map:** https://mkj69.github.io/weight-programming-survey-site/map.html

The collection stores **links and metadata only**. The reader shows each work from its original
source (the PDF, the post, the page, or the README), so no third-party text is copied into this
repository.

---

## What is on the site

### Library (`index.html`)

A two-pane reader. The list is on the left; the selected item opens on the right.

- **Views.** *Key works* (the default) shows classics, starred items, and posts that drew several
  reactions. *All* shows the whole collection. *Starred* shows only starred items.
- **Filters.** Search over titles, authors, and summaries; filter by category, type, and tag; sort
  by newest, oldest, or most cited.
- **One-sentence summaries.** Every item has a short summary under its title, written for this
  collection (not copied from the source).
- **Reader.** The right pane shows the original:

  | Source | How it is shown |
  |---|---|
  | arXiv papers | the PDF, in the browser's PDF viewer |
  | Other open-access PDFs | the PDF, when the host allows embedding |
  | X posts | X's official embedded post |
  | Blogs and other pages | the page itself, when the site allows embedding |
  | GitHub repositories | the README, fetched live from GitHub and rendered |
  | Hugging Face models, datasets, Spaces | the model or dataset card, fetched live |
  | Hacker News | the story and comment thread, from the HN API |
  | Reddit, YouTube | their official embeds |

  Some sites (for example GitHub pages themselves, Hugging Face pages, and some company blogs) do
  not allow other sites to embed them. Those open in a new tab when clicked. With a browser
  extension that lifts embedding limits, tick **Embed all sites** to show them in the pane anyway.
- **Reactions.** Quote-posts and posts that comment on a work are grouped under the original post
  or work, not listed separately. The original shows how many reactions it has. Its reader page
  lists them in two groups: *with analysis* (measurements, replications, technical arguments) and
  *short reactions* (praise, news-style restatements), which is folded. Tick
  **Show reactions as items** to list them on their own.
- **Linked discussions.** When a Hacker News thread discusses an item, the item shows an
  *HN discussion* link that opens the thread in the same pane.
- **Comments.** Every item has a comment thread, with timestamps, through
  [giscus](https://giscus.app) and GitHub Discussions. Commenting needs a GitHub account.
- **Stars and tags (owner).** Click the star next to a title to star or unstar it. Remove a tag
  with its ×, or add one from **+ Add tag**. Changes show at once in your browser. **Save N changes**
  opens a pre-filled GitHub issue; submitting it writes the changes to the repository, and
  everyone sees them a minute or two later.
- **Add a link (owner).** Paste a URL in **Paste a link to add it**. This opens a pre-filled issue.
  On submit, a GitHub Action reads the page's title, authors, and date, guesses the category and
  tags (or uses the ones you write in the issue), and adds the item.

### Field map (`map.html`)

A timeline of about 50 classic works in five branches, with lines showing which work built on
which. Click a node to read a short note on it, see what it built on and what it led to, and open it
in the reader. Classic works also carry a *Classic* badge in the library.

---

## Categories and tags

| Category | What belongs | Tags |
|---|---|---|
| LLMs reading and writing weights | An LLM or agent reads, interprets, edits, or writes another network's weights; agents inside the training loop | reading weights, editing weights, hand-written weights, replication, critique, application, agent in the loop, benchmark |
| Programs compiled into weights | Programs or algorithms built into transformer weights by construction | RASP / Tracr, compiler, circuit injection, computer in weights, provably correct |
| Weight editing and model diffs | Editing weights to change behaviour or knowledge; task vectors; model merging; weight differences between checkpoints | knowledge editing, locate and edit, task vectors, model merging, model diffing, unlearning, sequential editing |
| Fast weights and self-modifying networks | Networks that write their own or another network's weights at run time | fast weights, linear attention, self-referential, hypernetworks, test-time training, meta-learning |
| Weight-space learning | Weights treated as data: representations, equivariant networks over weights, generating weights, model zoos | weight representations, equivariant networks, weight generation, model zoos, predicting from weights |

An item can be in more than one category. The lists live in `crawler/taxonomy.json`.

---

## How the collection is built

```
 sources                     candidates                 decisions                 site data
 ───────                     ──────────                 ─────────                 ─────────
 OpenAlex (citations, ──┐
   keyword searches)    │
 arXiv (recent)         ├──► crawler/work/*.jsonl ──► classify.py ──► build.py ──► data/items.json
 GitHub, Hugging Face   │                              (rules, then     (dedupe,      data/map.json
 Hacker News, Reddit    │                               an LLM for       embeds,
 X (tracked accounts,   │                               unclear items)   overrides,
   one-off search)    ──┘                                                summaries,
 hand-picked items (crawler/forced.json)                                 reactions)
```

1. **Papers** (`crawler/papers.py`). Starts from about 60 seed works per branch
   (`crawler/seeds.json`), collects every work that cites them and every work they cite, then runs
   about 40 keyword searches. Source: [OpenAlex](https://openalex.org).
2. **Recent papers** (`crawler/arxiv_recent.py`). Searches arXiv directly, because OpenAlex lags by
   days to weeks.
3. **Code, models, discussions** (`crawler/other.py`). GitHub repository search, Hugging Face
   models, datasets, and Spaces, Hacker News stories (all time), and Reddit posts (through the
   arctic-shift archive).
4. **X posts.** `crawler/x_accounts.py` reads recent posts from about 50 tracked accounts through the
   public api.fxtwitter.com. X search needs a login, so a one-off search was run in the owner's
   own browser; `crawler/x_hydrate.py` turns the collected post IDs into records.
5. **Relevance** (`crawler/classify.py`, rules in `crawler/rules.py`). A title that clearly names
   the topic (for example *knowledge editing*, *Tracr*, *fast weight programmer*) is accepted with
   its category. Words that also appear outside machine learning (such as *hypernetwork* in graph
   theory or *weight space* in function spaces) only mark an item as unclear. Unclear items, and
   posts found by topical X searches, are judged by an LLM in batches. Retractions and spam are
   dropped. Items in `crawler/forced.json` are always included.
6. **Merging** (`crawler/build.py`). De-duplicates by arXiv ID, DOI, canonical URL (one item per
   GitHub repository), and normalised title; folds HN threads into the item they discuss; picks how
   each item is shown; fixes dates (OpenAlex gives `YYYY-01-01` when only the year is known, so
   those show the year, or the month from the arXiv ID); applies `data/overrides.json`; marks the
   classics from `crawler/classics.json`; and writes `data/items.json` and `data/map.json`.
7. **Summaries** (`crawler/summarize.py`). Writes the one-sentence summaries into
   `data/summaries.json`. New items added by the daily job get the first sentence of their
   abstract or description until summaries are regenerated.
8. **Reactions** (`crawler/reactions.py`). Groups X posts under the post or work they react to and
   labels each one *analysis* or *reaction* (`data/reactions.json`).

### Daily update

`.github/workflows/daily.yml` runs `crawler/daily.py` every day at **8:00 Chicago time** (the
workflow is scheduled at both 13:00 and 14:00 UTC and only proceeds at 8:00 local time, so it keeps
working across daylight saving changes). It looks for items from the last few days (GitHub, Hugging
Face, Hacker News, Reddit, arXiv, OpenAlex, and the tracked X accounts), keeps those whose titles
match the category rules, and commits the new `data/`. It does not use an LLM, so it is stricter
than the initial build. You can also run it by hand from the Actions tab.

### Issues that change the collection

`.github/workflows/issue.yml` handles issues labelled `add` or `edit`, **only when opened by the
repository owner**, and closes each issue with a short reply saying what changed.

- `add`: `url: <link>`, and optionally `category:`, `tags:`, `star: yes`.
- `edit`: either a JSON block written by the site's **Save** button, or
  `id: <item id>` with `star: yes|no`, `tags: a, b`, `category: ...`, `hide: yes`.

Edits are stored in `data/overrides.json`, so they survive every rebuild.

---

## Data format

`data/items.json`:

```json
{
  "updated": "2026-11-11",
  "categories": {"wsp": "LLMs reading and writing weights", "...": "..."},
  "tags": {"wsp": ["reading weights", "..."], "...": []},
  "types": ["paper", "blog", "post", "code", "model", "dataset", "discussion", "video"],
  "items": [
    {
      "id": "arxiv:2611.09382",
      "t": "Exploring Weight-Space Programming: Capabilities, Generalization, and Limitations",
      "u": "https://arxiv.org/abs/2611.09382",
      "k": "pdf",
      "e": "https://arxiv.org/pdf/2611.09382",
      "y": "paper",
      "c": ["wsp"],
      "g": ["benchmark", "critique"],
      "d": "2026-11-06",
      "a": "Junru Hu, Cheng Tang, ...",
      "v": "arXiv",
      "n": 0,
      "s": true,
      "cl": true,
      "sm": "Evaluates direct weight editing across seven benchmarks and two model sizes ...",
      "rx": ["x:...", "x:..."],
      "added": "2026-11-10"
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `id` | Stable ID: `arxiv:`, `doi:`, `oa:` (OpenAlex), `gh:` (repository), `x:` (post), `hn:`, `rd:`, `url:` |
| `t`, `u` | Title and original URL |
| `k`, `e` | How the reader shows it (`pdf`, `frame`, `tweet`, `github`, `hf`, `hn`, `reddit`, `youtube`, `none`) and the URL or ID it embeds |
| `y` | Type |
| `c`, `g` | Categories and tags |
| `d`, `a`, `v` | Date (`YYYY-MM-DD`, `YYYY-MM`, or `YYYY`), authors, venue |
| `n` | Citations, stars, or points, whichever applies |
| `s`, `cl` | Starred; classic |
| `sm` | One-sentence summary |
| `rx`, `rof`, `dp` | Reactions grouped under this item; the item this one reacts to; `analysis` or `reaction` |
| `hn` | ID of an HN thread that discusses this item |

`data/map.json` holds the classic works (`nodes`) and the links between them (`edges`).

---

## Running it yourself

The site is plain HTML, CSS, and JavaScript; it needs no build step.

```bash
python3 -m http.server 8000      # then open http://localhost:8000
```

Rebuilding the data needs Python 3.10+, the GitHub CLI (`gh`, logged in, for repository search),
and an OpenAlex API key (free, at https://openalex.org) in `OPENALEX_API_KEY` or
`crawler/work/.env`. The LLM steps call the Codex CLI (`codex exec`).

```bash
python3 crawler/papers.py                         # papers from OpenAlex (resumable)
python3 crawler/arxiv_recent.py --since 2026-05-01
python3 crawler/other.py                          # GitHub, Hugging Face, HN, Reddit
python3 crawler/x_accounts.py --since 2026-03-01
python3 crawler/classify.py --llm                 # rules, then the LLM for unclear items
python3 crawler/build.py --fresh                  # write data/items.json and data/map.json
python3 crawler/reactions.py                      # group X posts under their originals
python3 crawler/summarize.py                      # one-sentence summaries
python3 crawler/build.py                          # merge summaries and reactions
```

Comments need the [giscus app](https://github.com/apps/giscus) installed on this repository and
Discussions turned on; the IDs are in `assets/config.js`. The daily job needs the
`OPENALEX_API_KEY` repository secret.

---

## Repository layout

```
index.html, map.html        the two pages
assets/                     app.js (library), map.js (field map), styles, icon, config.js (repo and giscus IDs)
data/items.json             the collection (links and metadata)
data/map.json               classic works and their links
data/overrides.json         stars, tags, titles, dates, and hidden items set by hand
data/summaries.json         one-sentence summaries
data/reactions.json         which post reacts to which, and its depth
data/frame_cache.json       which sites allow embedding
crawler/                    everything that builds the data (see above)
.github/workflows/          the daily update and the issue handler
```

---

## Known limits

- **Coverage is broad but not complete.** Papers come from the citation graph of the seed works
  plus keyword searches; work that neither cites the seeds nor uses the keywords can be missed.
  The scope is deliberately wide ("anything about weight space"), so applied uses of
  hypernetworks and model merging are included.
- **Relevance was decided partly by an LLM.** A sample check found most accepted items on topic,
  with some borderline ones. Use **edit → hide** to remove items.
- **X is the weakest source.** Without a login there is no search, so the daily job only sees the
  tracked accounts; the one-off logged-in search covered the main keywords up to 2026-11-11. New
  posts from other accounts can be added with **Paste a link**.
- **Some pages cannot be embedded**, because their sites forbid it; they open in a new tab.
- **Dates for some papers show the year only**, because the source only gives the year.
- **The daily job uses rules only**, so it misses items whose titles do not name the topic, and its
  summaries are the first sentence of the abstract until the summary step is rerun.

The bilingual (Chinese and English) survey this collection grew out of is kept in a separate
private repository.
