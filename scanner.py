"""
GitHub Gem Finder - Step 1: Scanner
Finds underrated AI repos before they blow up.
Scores by VELOCITY (stars/day), not total stars.
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN or GITHUB_TOKEN == "paste_your_token_here":
    print("ERROR: Add your GitHub token to the .env file first!")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# AI topics to mine — these are the niches before they go mainstream
AI_TOPICS = [
    "llm",
    "large-language-model",
    "ai-agent",
    "rag",
    "fine-tuning",
    "mcp",                       # model context protocol — very hot right now
    "multimodal",
    "local-llm",
    "embeddings",
    "function-calling",
    "prompt-engineering",
    "ai-tools",
    "llama",
    "mistral",
    "ollama",
    "vllm",
    "inference",
    "ai-workflow",
    "agentic",
    "vector-database",
]


def search_repos(topic, days_back=90, min_stars=5, max_stars=800):
    """Query GitHub Search API for young repos under a given topic."""
    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    query = f"topic:{topic} created:>{since_date} stars:{min_stars}..{max_stars}"

    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 30,
    }

    resp = requests.get(url, headers=HEADERS, params=params)

    if resp.status_code == 200:
        return resp.json().get("items", [])
    elif resp.status_code == 403:
        reset_time = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
        wait = max(reset_time - int(time.time()), 10)
        print(f"    Rate limited. Waiting {wait}s...")
        time.sleep(wait)
        return []
    else:
        print(f"    Error {resp.status_code} for topic '{topic}'")
        return []


def score_repo(repo):
    """
    Calculate a Gem Score (0-100) based on momentum signals.

    Scoring breakdown:
    - Star velocity (stars/day)   → 0-40 pts  ← most important
    - Recency (how new it is)     → 0-30 pts
    - Fork engagement ratio       → 0-20 pts
    - Issue community activity    → 0-10 pts
    """
    created_at = datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    days_alive = max((datetime.now() - created_at).days, 1)

    stars = repo["stargazers_count"]
    forks = repo["forks_count"]
    issues = repo["open_issues_count"]

    # Velocity: stars gained per day since creation
    star_velocity = stars / days_alive

    # Fork ratio: high means people actually clone and use it (not just star)
    fork_ratio = forks / max(stars, 1)

    # Recency: repos < 30 days old get a big boost
    recency_score = max(0, (90 - days_alive) / 90) * 30

    # Velocity score (capped at 40)
    velocity_score = min(star_velocity * 8, 40)

    # Fork engagement (capped at 20)
    fork_score = min(fork_ratio * 50, 20)

    # Issue activity (capped at 10)
    issue_score = min(issues * 0.5, 10)

    total = velocity_score + fork_score + recency_score + issue_score

    return {
        "name": repo["full_name"],
        "description": repo["description"] or "No description",
        "url": repo["html_url"],
        "stars": stars,
        "forks": forks,
        "issues": issues,
        "days_alive": days_alive,
        "star_velocity": round(star_velocity, 2),
        "fork_ratio": round(fork_ratio, 3),
        "gem_score": round(min(total, 100), 1),
        "language": repo.get("language") or "Unknown",
        "topics": repo.get("topics", []),
        "created_at": repo["created_at"],
        "updated_at": repo["updated_at"],
        "avatar": repo["owner"]["avatar_url"],
        "owner": repo["owner"]["login"],
    }


def find_gems():
    """Main function: scan all AI topics, deduplicate, score, return top 50."""
    print("=" * 60)
    print("  GitHub Gem Finder — Scanning for AI gems")
    print("=" * 60)

    all_repos = {}  # keyed by repo ID to deduplicate across topics

    for i, topic in enumerate(AI_TOPICS):
        print(f"  [{i+1:02d}/{len(AI_TOPICS)}] topic: {topic}")
        repos = search_repos(topic)

        for repo in repos:
            repo_id = repo["id"]
            if repo_id not in all_repos:
                all_repos[repo_id] = score_repo(repo)

        time.sleep(2.5)  # GitHub Search API: 30 req/min for authenticated users

    # Sort by gem score descending
    gems = sorted(all_repos.values(), key=lambda x: x["gem_score"], reverse=True)

    print(f"\n{'='*60}")
    print(f"  Scanned {len(gems)} unique repos. Top 10 gems:")
    print(f"{'='*60}")
    for gem in gems[:10]:
        print(
            f"  {gem['gem_score']:5.1f} | "
            f"{gem['name']:<40} | "
            f"{gem['stars']:>5} stars | "
            f"{gem['star_velocity']:.1f}/day"
        )

    # Save full results to JSON for the HTML dashboard (Step 3)
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_scanned": len(gems),
        "gems": gems[:50],
    }

    os.makedirs("output", exist_ok=True)
    with open("output/gems.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved top 50 gems to output/gems.json")
    return gems[:50]


if __name__ == "__main__":
    find_gems()
