# Weight Space Reader

A reading list and reader for work on the weight space of neural networks: LLMs that read and
write weights, programs compiled into weights, weight editing and model diffs, fast weights and
self-modifying networks, and weight-space learning. It covers over 4,000 papers, posts,
repositories, and discussions, each with a one-sentence summary, plus a timeline map of the
classic works.

**Site:** https://mkj69.github.io/weight-programming-survey-site/ · **Map:** https://mkj69.github.io/weight-programming-survey-site/map.html

The repository stores links and metadata only (`data/items.json`). The site shows each work from
its original source: the PDF for papers, the post for X, the page for blogs, and the README for
GitHub and Hugging Face. Each item has a comment thread through GitHub Discussions.

The collection updates itself every day at 8:00 Chicago time: a GitHub Action (`crawler/daily.py`)
looks for new papers, repositories, posts, and discussions on these topics and adds them. The
update can be paused from the link at the bottom of the site's list. The code that builds the
collection is in `crawler/`.
