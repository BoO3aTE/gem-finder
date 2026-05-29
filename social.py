"""
GitHub Gem Finder - Step 2: Social Signal Enrichment
Checks Reddit + Hacker News for each gem.
A repo gaining GitHub velocity AND social buzz = the real deal.

Matching is deliberately conservative: a post only counts as a mention when it
both (a) post-dates the repo's creation and (b) clearly references THIS repo
(its github.com/owner/repo URL, its full owner/repo slug, or its name as a
whole word for distinctive names). This avoids crediting a young repo with
unrelated, years-old posts that merely share a common word in the title.
"""

import re
import json
import time
import requests
from datetime import datetime, timezone

REDDIT_HEADERS = {
    "User-Agent": "GemFinder/1.0 (AI trend research tool)"
}

# Subreddits where early AI adopters hang out
SUBREDDITS = [
    "LocalLLaMA",
    "MachineLearning",
    "artificial",
    "singularity",
    "ChatGPT",
    "programming",
    "Python",
]

# Posts created within this many seconds before the repo's creation are still
# allowed (small grace for clock/timezone skew).
DATE_GRACE_SECONDS = 86400


def _repo_created_ts(gem):
    """Unix timestamp of the repo's creation, or 0 if unparseable."""
    try:
        dt = datetime.strptime(gem["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        return dt.replace(tzinfo=timezone.utc).timestamp()
    except (KeyError, ValueError, TypeError):
        return 0.0


def _make_repo_matcher(full_name):
    """
    Return a predicate(title, url, *extra) that decides whether a post
    genuinely references `full_name` (an "owner/repo" string).
    """
    full = full_name.lower()
    owner, _, short = full.partition("/")
    word_re = re.compile(rf"\b{re.escape(short)}\b") if len(short) >= 5 else None

    def references_repo(title, *texts):
        title = (title or "").lower()
        blobs = [(t or "").lower() for t in texts]

        # Strongest: a link straight to this repo.
        for b in blobs:
            if f"github.com/{full}" in b:
                return True

        # Full "owner/repo" slug appears anywhere.
        for b in [title, *blobs]:
            if full in b:
                return True

        # Distinctive bare repo name as a whole word in the title.
        if word_re and word_re.search(title):
            return True

        return False

    return references_repo


def search_hackernews(gem):
    """Search HN via Algolia API. Free, no auth, very generous limits."""
    full_name = gem["name"]
    query = full_name.split("/")[-1]  # just repo name, not owner prefix
    created_ts = _repo_created_ts(gem)
    references_repo = _make_repo_matcher(full_name)

    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": query, "tags": "story", "hitsPerPage": 10}

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return []

        mentions = []
        for hit in resp.json().get("hits", []):
            # Skip posts that predate the repo — they can't be about it.
            created_at_i = hit.get("created_at_i") or 0
            if created_ts and created_at_i < created_ts - DATE_GRACE_SECONDS:
                continue

            title = hit.get("title", "")
            hit_url = hit.get("url") or ""
            if references_repo(title, hit_url):
                mentions.append({
                    "source": "HackerNews",
                    "title": title,
                    "url": f"https://news.ycombinator.com/item?id={hit['objectID']}",
                    "points": hit.get("points") or 0,
                    "comments": hit.get("num_comments") or 0,
                })
        return mentions

    except Exception as e:
        print(f"    HN error: {e}")
        return []


def search_reddit(gem):
    """Search AI subreddits for repo mentions using Reddit's public JSON API."""
    full_name = gem["name"]
    query = full_name.split("/")[-1]
    created_ts = _repo_created_ts(gem)
    references_repo = _make_repo_matcher(full_name)
    mentions = []

    for subreddit in SUBREDDITS:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {"q": query, "sort": "new", "limit": 5, "restrict_sr": "true"}

        try:
            resp = requests.get(url, headers=REDDIT_HEADERS, params=params, timeout=10)
            if resp.status_code != 200:
                # Reddit's anonymous endpoint rate-limits aggressively (429).
                if resp.status_code == 429:
                    print(f"    Reddit/{subreddit} rate limited (429)")
                continue

            posts = resp.json().get("data", {}).get("children", [])
            for post in posts:
                d = post["data"]
                # Skip posts that predate the repo.
                if created_ts and (d.get("created_utc") or 0) < created_ts - DATE_GRACE_SECONDS:
                    continue

                title = d.get("title", "")
                body = d.get("selftext", "")
                link = d.get("url", "")
                if references_repo(title, body, link):
                    mentions.append({
                        "source": f"r/{subreddit}",
                        "title": title,
                        "url": f"https://reddit.com{d['permalink']}",
                        "upvotes": d.get("ups", 0),
                        "comments": d.get("num_comments", 0),
                    })
        except Exception as e:
            print(f"    Reddit/{subreddit} error: {e}")

        time.sleep(0.5)  # polite rate limit: ~2 req/s to Reddit

    return mentions


def social_score(hn_mentions, reddit_mentions):
    """
    Calculate social bonus points (max +30).
    Flat bonus for any mention + weighted by engagement.
    """
    score = 0.0

    if hn_mentions:
        score += 6  # flat bonus for any HN appearance
        for m in hn_mentions:
            score += min(m["points"] * 0.08, 8)
            score += min(m["comments"] * 0.15, 4)

    if reddit_mentions:
        score += 4  # flat bonus for any Reddit appearance
        for m in reddit_mentions:
            score += min(m["upvotes"] * 0.04, 6)
            score += min(m["comments"] * 0.1, 3)

    return round(min(score, 30), 1)


def enrich_gems():
    """Load gems.json, add social signals, save gems_enriched.json."""
    print("=" * 60)
    print("  Step 2: Social Signal Enrichment")
    print("  Checking Reddit + Hacker News for all 50 gems")
    print("  (takes ~5 min — Reddit rate limits require pacing)")
    print("=" * 60)

    with open("output/gems.json", encoding="utf-8") as f:
        data = json.load(f)

    gems = data["gems"]
    enriched = []

    for i, gem in enumerate(gems):
        name = gem["name"]
        print(f"  [{i+1:02d}/{len(gems)}] {name}", end="", flush=True)

        hn = search_hackernews(gem)
        reddit = search_reddit(gem)
        s_score = social_score(hn, reddit)

        tag = f"  HN:{len(hn)} Reddit:{len(reddit)} +{s_score}" if (hn or reddit) else ""
        print(tag or "  (no mentions yet)")

        gem["hn_mentions"] = hn
        gem["reddit_mentions"] = reddit
        gem["social_score"] = s_score
        # total_score is a 0-100 composite: GitHub momentum (gem_score, 0-100)
        # plus social buzz (0-30), capped so the dashboard "score" stays 0-100.
        gem["total_score"] = round(min(gem["gem_score"] + s_score, 100), 1)
        enriched.append(gem)

        time.sleep(0.8)

    # Re-sort by combined score
    enriched.sort(key=lambda x: x["total_score"], reverse=True)

    print(f"\n{'=' * 60}")
    print("  Final Top 10 (GitHub velocity + social buzz):")
    print(f"{'=' * 60}")
    for gem in enriched[:10]:
        buzz = " BUZZING" if gem["social_score"] > 5 else ""
        print(
            f"  {gem['total_score']:5.1f} | "
            f"{gem['name']:<42} | "
            f"{gem['stars']:>5} stars{buzz}"
        )

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_gems": len(enriched),
        "gems": enriched,
    }

    with open("output/gems_enriched.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved to output/gems_enriched.json")
    return enriched


if __name__ == "__main__":
    enrich_gems()
