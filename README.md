# Weight Space Reader

A reading list of work on the weight space of neural networks: LLMs that read and write weights,
programs compiled into weights, weight editing and model diffs, fast weights and self-modifying
networks, and weight-space learning.

Site: https://mkj69.github.io/weight-programming-survey-site/

- The collection stores links and metadata only. The reader embeds each original: PDFs for papers,
  the post for X, the page itself for blogs, and the README for GitHub and Hugging Face.
- Comments use GitHub Discussions through giscus.
- `crawler/` builds `data/items.json`. A GitHub Action runs `crawler/daily.py` every day at 8:00
  Chicago time. Pasting a link on the site opens an issue that adds it (owner only).
