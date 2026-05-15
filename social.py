"""
GitHub Gem Finder - Step 2: Social Signal Enrichment
Checks Reddit + Hacker News for each gem.
A repo gaining GitHub velocity AND social buzz = the real deal.
"""

import json
import time
import requests
from datetime import datetime

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


def search_hackernews(repo_name):
    """Search HN via Algolia API. Free, no auth, very generous limits."""
    query = repo_name.split("/")[-1]  # just repo name, not owner prefix
    url = "https://hn.algolia.com/api/v1/search"
    params = {"query": query, "tags": "story", "hitsPerPage": 5}

    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return []

        mentions = []
        for hit in resp.json().get("hits", []):
            title = hit.get("title", "")
            hit_url = hit.get("url") or ""
            # only count if repo name actually appears in title or URL
            if query.lower() in title.lower() or query.lower() in hit_url.lower():
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


def search_reddit(repo_name):
    """Search AI subreddits for repo mentions using Reddit's public JSON API."""
    query = repo_name.split("/")[-1]
    mentions = []

    for subreddit in SUBREDDITS:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {"q": query, "sort": "new", "limit": 3, "restrict_sr": "true"}

        try:
            resp = requests.get(url, headers=REDDIT_HEADERS, params=params, timeout=10)
            if resp.status_code == 200:
                posts = resp.json().get("data", {}).get("children", [])
                for post in posts:
                    d = post["data"]
                    title = d.get("title", "")
                    body = d.get("selftext", "")
                    if query.lower() in title.lower() or query.lower() in body.lower():
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

        hn = search_hackernews(name)
        reddit = search_reddit(name)
        s_score = social_score(hn, reddit)

        tag = f"  HN:{len(hn)} Reddit:{len(reddit)} +{s_score}" if (hn or reddit) else ""
        print(tag or "  (no mentions yet)")

        gem["hn_mentions"] = hn
        gem["reddit_mentions"] = reddit
        gem["social_score"] = s_score
        gem["total_score"] = round(gem["gem_score"] + s_score, 1)
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
        "generated_at": datetime.now().isoformat(),
        "total_gems": len(enriched),
        "gems": enriched,
    }

    with open("output/gems_enriched.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved to output/gems_enriched.json")
    return enriched


if __name__ == "__main__":
    enrich_gems()
