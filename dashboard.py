"""
GitHub Gem Finder - Step 3: HTML Dashboard Generator
Reads gems_enriched.json and produces a beautiful dark dashboard.
"""

import json
import os
from datetime import datetime
from jinja2 import Template

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI GitHub Gem Finder</title>
<style>
  :root {
    --bg: #070810;
    --surface: #0d0f1e;
    --card: #111427;
    --border: #1e2240;
    --accent: #ff6b35;
    --accent2: #7c3aed;
    --accent3: #06b6d4;
    --green: #10b981;
    --text: #e2e8f0;
    --muted: #64748b;
    --font: 'Inter', system-ui, sans-serif;
    --mono: 'JetBrains Mono', 'Fira Code', monospace;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    min-height: 100vh;
  }

  /* ── Header ── */
  header {
    background: linear-gradient(135deg, #0d0f1e 0%, #110d2e 50%, #0a1628 100%);
    border-bottom: 1px solid var(--border);
    padding: 2.5rem 2rem 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  header::before {
    content: '';
    position: absolute;
    top: -60px; left: 50%; transform: translateX(-50%);
    width: 600px; height: 200px;
    background: radial-gradient(ellipse, rgba(124,58,237,0.15) 0%, transparent 70%);
    pointer-events: none;
  }
  header h1 {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(90deg, #ff6b35, #7c3aed, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
  }
  header p {
    color: var(--muted);
    font-size: 0.95rem;
    letter-spacing: 0.05em;
  }
  .meta-chips {
    display: flex;
    justify-content: center;
    gap: 0.75rem;
    margin-top: 1.2rem;
    flex-wrap: wrap;
  }
  .chip {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 0.3rem 0.85rem;
    font-size: 0.78rem;
    color: var(--muted);
    font-family: var(--mono);
  }
  .chip span { color: var(--accent); font-weight: 600; }

  /* ── Filters ── */
  .controls {
    display: flex;
    gap: 0.75rem;
    padding: 1.5rem 2rem;
    max-width: 1400px;
    margin: 0 auto;
    flex-wrap: wrap;
    align-items: center;
  }
  .controls input {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    padding: 0.5rem 1rem;
    font-size: 0.88rem;
    width: 260px;
    outline: none;
    font-family: var(--font);
  }
  .controls input:focus { border-color: var(--accent); }
  .filter-btn {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--muted);
    padding: 0.5rem 1rem;
    font-size: 0.82rem;
    cursor: pointer;
    transition: all 0.15s;
    font-family: var(--font);
  }
  .filter-btn:hover, .filter-btn.active {
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
  }
  .total-label {
    margin-left: auto;
    color: var(--muted);
    font-size: 0.82rem;
    font-family: var(--mono);
  }

  /* ── Grid ── */
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 1.25rem;
    padding: 0 2rem 3rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  /* ── Card ── */
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.4rem;
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    transition: transform 0.15s, border-color 0.15s;
    animation: fadeInUp 0.4s ease both;
    position: relative;
    overflow: hidden;
  }
  .card:hover {
    transform: translateY(-2px);
    border-color: #2a2f5a;
  }
  .card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }
  .card.tier-hot::before  { background: linear-gradient(90deg, #ff6b35, #f59e0b); }
  .card.tier-warm::before { background: linear-gradient(90deg, #7c3aed, #06b6d4); }
  .card.tier-cold::before { background: var(--border); }

  /* ── Card header ── */
  .card-header {
    display: flex;
    align-items: flex-start;
    gap: 0.85rem;
  }
  .avatar {
    width: 40px; height: 40px;
    border-radius: 8px;
    object-fit: cover;
    flex-shrink: 0;
    border: 1px solid var(--border);
  }
  .card-title {
    flex: 1;
    min-width: 0;
  }
  .repo-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text);
    text-decoration: none;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .repo-name:hover { color: var(--accent); }
  .repo-owner {
    font-size: 0.75rem;
    color: var(--muted);
    font-family: var(--mono);
  }

  /* ── Gem score badge ── */
  .score-badge {
    flex-shrink: 0;
    width: 52px; height: 52px;
    border-radius: 10px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: var(--mono);
  }
  .score-badge.hot  { background: rgba(255,107,53,0.12); border: 1px solid rgba(255,107,53,0.3); }
  .score-badge.warm { background: rgba(124,58,237,0.12); border: 1px solid rgba(124,58,237,0.3); }
  .score-badge.cold { background: var(--surface);        border: 1px solid var(--border); }
  .score-num {
    font-size: 1.1rem;
    font-weight: 800;
    line-height: 1;
  }
  .score-badge.hot  .score-num { color: #ff6b35; }
  .score-badge.warm .score-num { color: #a78bfa; }
  .score-badge.cold .score-num { color: var(--muted); }
  .score-label { font-size: 0.58rem; color: var(--muted); text-transform: uppercase; }

  /* ── Description ── */
  .description {
    font-size: 0.83rem;
    color: #94a3b8;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* ── Stats row ── */
  .stats {
    display: flex;
    gap: 1.2rem;
    flex-wrap: wrap;
  }
  .stat {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.78rem;
    color: var(--muted);
    font-family: var(--mono);
  }
  .stat strong { color: var(--text); }
  .stat .icon { font-size: 0.9rem; }

  /* ── Velocity pill ── */
  .velocity-bar {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }
  .velocity-track {
    flex: 1;
    height: 4px;
    background: var(--border);
    border-radius: 2px;
    overflow: hidden;
  }
  .velocity-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #ff6b35, #f59e0b);
  }
  .velocity-label {
    font-size: 0.72rem;
    color: var(--accent);
    font-family: var(--mono);
    white-space: nowrap;
  }

  /* ── Social mentions ── */
  .social-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  .social-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.72rem;
    border-radius: 999px;
    padding: 0.2rem 0.6rem;
    text-decoration: none;
    font-family: var(--mono);
    transition: opacity 0.15s;
    border: 1px solid;
  }
  .social-pill:hover { opacity: 0.75; }
  .social-pill.hn    { background: rgba(255,102,0,0.1); border-color: rgba(255,102,0,0.3); color: #ff6600; }
  .social-pill.reddit { background: rgba(255,69,0,0.1); border-color: rgba(255,69,0,0.3); color: #ff4500; }

  /* ── Topics ── */
  .topics { display: flex; flex-wrap: wrap; gap: 0.4rem; }
  .topic {
    font-size: 0.68rem;
    font-family: var(--mono);
    background: rgba(6,182,212,0.07);
    border: 1px solid rgba(6,182,212,0.2);
    color: #67e8f9;
    border-radius: 999px;
    padding: 0.15rem 0.55rem;
  }

  /* ── Footer ── */
  footer {
    text-align: center;
    padding: 2rem;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: 0.8rem;
  }

  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }
</style>
</head>
<body>

<header>
  <h1>AI GitHub Gem Finder</h1>
  <p>Hidden gems before they become mainstream &mdash; scored by velocity + social buzz</p>
  <div class="meta-chips">
    <div class="chip">Generated <span>{{ generated_at }}</span></div>
    <div class="chip">Repos scanned <span>{{ total_gems }}</span></div>
    <div class="chip">Sources <span>GitHub + Reddit + HN</span></div>
  </div>
</header>

<div class="controls">
  <input type="text" id="search" placeholder="Search repos, topics, languages..." oninput="filterCards()">
  <button class="filter-btn active" onclick="setFilter('all', this)">All</button>
  <button class="filter-btn" onclick="setFilter('hot', this)">Hot (&gt;70)</button>
  <button class="filter-btn" onclick="setFilter('buzzing', this)">Buzzing</button>
  <button class="filter-btn" onclick="setFilter('young', this)">Under 14 days</button>
  <span class="total-label" id="count">{{ gems|length }} gems</span>
</div>

<div class="grid" id="grid">
{% for gem in gems %}
{% set tier = 'hot' if gem.total_score >= 70 else ('warm' if gem.total_score >= 40 else 'cold') %}
{% set velocity_pct = [gem.star_velocity / 50 * 100, 100] | min %}
<div class="card tier-{{ tier }}"
     data-name="{{ gem.name | lower }}"
     data-topics="{{ gem.topics | join(' ') | lower }}"
     data-lang="{{ (gem.language or '') | lower }}"
     data-score="{{ gem.total_score }}"
     data-social="{{ gem.social_score }}"
     data-days="{{ gem.days_alive }}">

  <div class="card-header">
    <img class="avatar" src="{{ gem.avatar }}" alt="{{ gem.owner }}" loading="lazy">
    <div class="card-title">
      <a class="repo-name" href="{{ gem.url }}" target="_blank" rel="noopener">{{ gem.name }}</a>
      <div class="repo-owner">{{ gem.language or 'Unknown' }} &bull; {{ gem.days_alive }}d old</div>
    </div>
    <div class="score-badge {{ tier }}">
      <div class="score-num">{{ gem.total_score }}</div>
      <div class="score-label">score</div>
    </div>
  </div>

  <div class="description">{{ gem.description }}</div>

  <div class="stats">
    <div class="stat"><span class="icon">⭐</span><strong>{{ gem.stars }}</strong> stars</div>
    <div class="stat"><span class="icon">🍴</span><strong>{{ gem.forks }}</strong> forks</div>
    <div class="stat"><span class="icon">💬</span><strong>{{ gem.issues }}</strong> issues</div>
  </div>

  <div class="velocity-bar">
    <div class="velocity-track">
      <div class="velocity-fill" style="width: {{ velocity_pct | int }}%"></div>
    </div>
    <div class="velocity-label">{{ gem.star_velocity }}/day</div>
  </div>

  {% if gem.hn_mentions or gem.reddit_mentions %}
  <div class="social-row">
    {% for m in gem.hn_mentions[:2] %}
    <a class="social-pill hn" href="{{ m.url }}" target="_blank" rel="noopener">
      &#9650; HN &middot; {{ m.points }}pts
    </a>
    {% endfor %}
    {% for m in gem.reddit_mentions[:3] %}
    <a class="social-pill reddit" href="{{ m.url }}" target="_blank" rel="noopener">
      &#8679; {{ m.source }} &middot; {{ m.upvotes }}&#8679;
    </a>
    {% endfor %}
  </div>
  {% endif %}

  {% if gem.topics %}
  <div class="topics">
    {% for t in gem.topics[:6] %}
    <span class="topic">{{ t }}</span>
    {% endfor %}
  </div>
  {% endif %}

</div>
{% endfor %}
</div>

<footer>
  Built with GitHub API + Reddit + Hacker News &bull; Gem score = velocity &times; recency &times; engagement &bull; Not financial advice
</footer>

<script>
  let activeFilter = 'all';

  function setFilter(f, btn) {
    activeFilter = f;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterCards();
  }

  function filterCards() {
    const q = document.getElementById('search').value.toLowerCase();
    const cards = document.querySelectorAll('.card');
    let visible = 0;

    cards.forEach(card => {
      const matchSearch = !q ||
        card.dataset.name.includes(q) ||
        card.dataset.topics.includes(q) ||
        card.dataset.lang.includes(q);

      const score = parseFloat(card.dataset.score);
      const social = parseFloat(card.dataset.social);
      const days = parseInt(card.dataset.days);

      const matchFilter =
        activeFilter === 'all'     ||
        (activeFilter === 'hot'     && score >= 70) ||
        (activeFilter === 'buzzing' && social > 5)  ||
        (activeFilter === 'young'   && days <= 14);

      const show = matchSearch && matchFilter;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    document.getElementById('count').textContent = visible + ' gems';
  }
</script>
</body>
</html>
"""


def build_dashboard():
    """Generate the HTML dashboard from gems_enriched.json."""
    src = "output/gems_enriched.json"
    if not os.path.exists(src):
        print("Run social.py first to generate gems_enriched.json")
        return

    with open(src, encoding="utf-8") as f:
        data = json.load(f)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    template = Template(TEMPLATE)
    html = template.render(
        gems=data["gems"],
        total_gems=data["total_gems"],
        generated_at=generated_at,
    )

    out_path = "output/dashboard.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard built: {out_path}")
    print(f"Open it in your browser to see the results.")


if __name__ == "__main__":
    build_dashboard()
