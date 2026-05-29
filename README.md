# AI GitHub Gem Finder

Finds **underrated AI repositories before they blow up** by scoring momentum
(stars *per day*, recency, engagement) instead of raw star counts, then
cross-checking each candidate against social buzz on Hacker News and Reddit.

The result is a self-contained dark-themed HTML dashboard, regenerated daily by
GitHub Actions and published to GitHub Pages.

## How it works

A three-step pipeline:

| Step | File | Input → Output | What it does |
|------|------|----------------|--------------|
| 1 | `scanner.py` | GitHub Search API → `output/gems.json` | Scans ~20 AI topics for young repos and scores them by momentum (`gem_score`, 0–100). |
| 2 | `social.py` | `output/gems.json` → `output/gems_enriched.json` | Adds a social bonus (0–30) from HN + Reddit mentions and re-ranks (`total_score`, capped at 100). |
| 3 | `dashboard.py` | `output/gems_enriched.json` → `output/dashboard.html` | Renders a filterable Jinja2 dashboard. |

`run_all.py` runs all three in sequence and opens the dashboard in your browser.

### Scoring

`gem_score` (0–100) is the GitHub momentum signal:

- **Star velocity** (stars/day since creation) — up to 40 pts (most important)
- **Recency** (newer repos score higher) — up to 30 pts
- **Fork engagement** (forks/stars) — up to 20 pts
- **Issue activity** — up to 10 pts

`total_score = min(gem_score + social_score, 100)`.

Social matching is deliberately conservative — a HN/Reddit post only counts if
it post-dates the repo *and* clearly references it (its `github.com/owner/repo`
URL, full `owner/repo` slug, or distinctive name as a whole word). This avoids
crediting a brand-new repo with unrelated, years-old posts that merely share a
common word.

## Setup

Requires Python 3.10+.

```bash
pip install -r requirements.txt

# Configure your GitHub token
cp .env.example .env        # on Windows: copy .env.example .env
# then edit .env and paste your token
```

Create a token at <https://github.com/settings/tokens>. No special scopes are
needed for the public Search API; the token mainly raises your rate limit.

Windows users can run `setup.bat` instead of the `pip install` step.

## Usage

```bash
python run_all.py        # full pipeline + opens the dashboard

# or run individual steps:
python scanner.py        # Step 1 — scan & score
python social.py         # Step 2 — social enrichment
python dashboard.py      # Step 3 — build dashboard
```

Outputs are written to `output/` (git-ignored). Open `output/dashboard.html`.

## Automation

`.github/workflows/daily.yml` runs the full pipeline every day at 08:00 UTC
(and via the "Run workflow" button), commits the refreshed `docs/`, and deploys
to GitHub Pages.

It expects a repository secret named **`GH_SCAN_TOKEN`** (a GitHub token used
for the Search API):

> repo **Settings → Secrets and variables → Actions → New repository secret**

## Project layout

```
scanner.py        Step 1 — GitHub scan & momentum scoring
social.py         Step 2 — Hacker News + Reddit enrichment
dashboard.py      Step 3 — HTML dashboard generator
run_all.py        Runs all three steps end to end
requirements.txt  Python dependencies
setup.bat         Windows convenience installer
.env.example      Template for your local .env
docs/             Published dashboard (GitHub Pages)
.github/workflows/daily.yml  Daily scheduled scan
```
