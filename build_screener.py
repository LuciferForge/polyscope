#!/usr/bin/env python3
"""
PolyScope Screener — Static Site Generator
Reads from market_universe.db → generates GitHub Pages-deployable site in docs/
"""

import sqlite3
import os
import json
import re
import math
from datetime import datetime, timezone
from pathlib import Path
from html import escape

# ─── Config ──────────────────────────────────────────────────────────────────
DB_PATH     = "/Users/apple/Documents/LuciferForge/polymarket-ai/market_universe.db"
OUT_DIR     = Path("/Users/apple/Documents/LuciferForge/products/polyscope-screener/docs")
SITE_URL    = "https://polyscope.luciferforge.io"
SITE_NAME   = "PolyScope"
SITE_TAGLINE = "Prediction Market Intelligence"
CHECKOUT_URL = "https://manja8.gumroad.com/l/agyjd"
API_DOCS_URL = "https://api.polyscope.luciferforge.io/docs"
PROTODEX_URL = "https://protodex.io"
LUCIFERFORGE_URL = "https://luciferforge.io"
BUILD_TS     = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
BUILD_DATE   = datetime.now(timezone.utc).strftime("%B %d, %Y")

CATEGORY_LABELS = {
    "politics":      "Politics",
    "sports":        "Sports",
    "crypto":        "Crypto",
    "geopolitics":   "Geopolitics",
    "economics":     "Economics",
    "science_tech":  "Science & Tech",
    "entertainment": "Entertainment",
    "weather":       "Weather",
    "pop_culture":   "Pop Culture",
    "other":         "Other",
}

CATEGORY_ICONS = {
    "politics":      "🏛️",
    "sports":        "⚽",
    "crypto":        "₿",
    "geopolitics":   "🌍",
    "economics":     "📈",
    "science_tech":  "🔬",
    "entertainment": "🎬",
    "weather":       "🌤️",
    "pop_culture":   "⭐",
    "other":         "🔮",
}

# ─── Helpers ─────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text[:80]

def fmt_price(p) -> str:
    if p is None:
        return "—"
    return f"{float(p)*100:.1f}¢"

def fmt_pct(p) -> str:
    if p is None:
        return "—"
    return f"{float(p)*100:.0f}%"

def fmt_volume(v) -> str:
    if v is None:
        return "—"
    v = float(v)
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"

def fmt_change(c) -> tuple[str, str]:
    """Returns (formatted_string, css_class)"""
    if c is None:
        return "—", "neutral"
    c = float(c)
    pct = c * 100
    cls = "positive" if c > 0 else ("negative" if c < 0 else "neutral")
    sign = "+" if c > 0 else ""
    return f"{sign}{pct:.1f}pp", cls

def fmt_date(d) -> str:
    if not d:
        return "—"
    try:
        dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except Exception:
        return d[:10]

def days_until(d) -> int | None:
    if not d:
        return None
    try:
        dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return max(0, (dt - now).days)
    except Exception:
        return None

def market_url(market_id: str, slug: str | None) -> str:
    key = slug if slug else slugify(str(market_id))
    return f"/markets/{key}.html"

def safe_str(v) -> str:
    return escape(str(v)) if v else ""

# ─── Load Data ───────────────────────────────────────────────────────────────

def load_markets() -> list[dict]:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("""
        SELECT id, question, category, tags, slug, volume, volume_24h, liquidity,
               end_date, best_bid, best_ask, spread, last_trade_price, one_day_change,
               active, resolved, snapshot_ts
        FROM markets
        WHERE active = 1 AND resolved = 0
        ORDER BY volume_24h DESC NULLS LAST
    """)
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

# ─── CSS / Shared Assets ────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg-primary:    #0A0A0A;
  --bg-secondary:  #111111;
  --bg-tertiary:   #1A1A1A;
  --border:        #262626;
  --border-hover:  #404040;
  --text-primary:  #EDEDED;
  --text-secondary:#A1A1A1;
  --text-tertiary: #666666;
  --accent:        #3B82F6;
  --accent-hover:  #2563EB;
  --success:       #22C55E;
  --danger:        #EF4444;
  --warning:       #F59E0B;
  --info:          #8B5CF6;
  --teal:          #00d4aa;
  --radius-sm:     6px;
  --radius-md:     8px;
  --radius-lg:     12px;
  --radius-xl:     16px;
}

html { scroll-behavior: smooth; }

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', sans-serif;
  font-size: 15px;
  line-height: 1.6;
  min-height: 100vh;
}

a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-hover); }

/* ── Nav ── */
.nav {
  height: 48px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 24px;
}
.nav-brand {
  font-weight: 700;
  font-size: 1rem;
  color: var(--text-primary);
  white-space: nowrap;
}
.nav-brand span { color: var(--teal); }
.nav-links { display: flex; gap: 16px; flex: 1; }
.nav-links a {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: color 0.15s, background 0.15s;
}
.nav-links a:hover { color: var(--text-primary); background: var(--bg-tertiary); }
.nav-right { margin-left: auto; display: flex; gap: 8px; align-items: center; }

/* ── Layout ── */
.container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
.page-header { padding: 40px 0 32px; }
.page-title { font-size: 2rem; font-weight: 700; line-height: 1.2; }
.page-subtitle { color: var(--text-secondary); margin-top: 8px; font-size: 14px; }

/* ── Cards ── */
.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  transition: border-color 0.15s ease;
}
.card:hover { border-color: var(--border-hover); }

/* ── Section headers ── */
.section { margin: 32px 0; }
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-title .dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--teal);
  animation: pulse 2s infinite;
}
.section-link { font-size: 13px; color: var(--text-secondary); }
.section-link:hover { color: var(--accent); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Market Table ── */
.market-table { width: 100%; border-collapse: collapse; }
.market-table th {
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}
.market-table th.right { text-align: right; }
.market-table td {
  padding: 11px 12px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  vertical-align: middle;
}
.market-table tr:hover td { background: var(--bg-tertiary); }
.market-table tr:last-child td { border-bottom: none; }
.market-table td.right {
  text-align: right;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}
.market-table td.mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}
.market-question {
  max-width: 380px;
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.market-question:hover { color: var(--accent); }

/* ── Price / Change badges ── */
.price-pill {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}
.positive { color: var(--success); }
.negative { color: var(--danger); }
.neutral  { color: var(--text-tertiary); }

/* ── Category badge ── */
.cat-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 500;
  padding: 2px 7px;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  white-space: nowrap;
}

/* ── Crash signal cards ── */
.crash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.crash-card {
  background: linear-gradient(135deg, rgba(239,68,68,0.06) 0%, var(--bg-secondary) 100%);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: var(--radius-lg);
  padding: 16px;
  transition: border-color 0.15s;
}
.crash-card:hover { border-color: rgba(239,68,68,0.45); }
.crash-drop {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--danger);
}
.crash-question {
  font-size: 13px;
  color: var(--text-primary);
  margin: 8px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.crash-meta {
  font-size: 12px;
  color: var(--text-tertiary);
  font-family: 'JetBrains Mono', monospace;
}

/* ── Category grid ── */
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}
.cat-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 16px;
  text-align: center;
  transition: border-color 0.15s, background 0.15s;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.cat-card:hover {
  border-color: var(--teal);
  background: var(--bg-tertiary);
}
.cat-icon { font-size: 1.75rem; }
.cat-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.cat-count { font-size: 12px; color: var(--text-tertiary); font-family: 'JetBrains Mono', monospace; }

/* ── Monetization banner ── */
.cta-banner {
  background: linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(139,92,246,0.1) 100%);
  border: 1px solid rgba(59,130,246,0.25);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin: 24px 0;
}
.cta-text { font-size: 14px; color: var(--text-secondary); }
.cta-text strong { color: var(--text-primary); }
.cta-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}
.btn-primary:hover { background: var(--accent-hover); color: white; }
.btn-secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}
.btn-secondary:hover { border-color: var(--border-hover); color: var(--text-primary); }

/* ── Market detail page ── */
.market-hero { padding: 32px 0 24px; }
.market-hero-meta { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.market-hero-q {
  font-size: 1.6rem;
  font-weight: 700;
  line-height: 1.3;
  max-width: 800px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  margin: 24px 0;
}
.stat-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
}
.stat-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  font-family: 'JetBrains Mono', monospace;
  margin-bottom: 6px;
}
.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}
.breadcrumb {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.breadcrumb a { color: var(--text-secondary); }
.breadcrumb a:hover { color: var(--accent); }

/* ── Footer ── */
footer {
  margin-top: 64px;
  border-top: 1px solid var(--border);
  padding: 24px 0;
  font-size: 13px;
  color: var(--text-tertiary);
}
.footer-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.footer-links { display: flex; gap: 16px; }
.footer-links a { color: var(--text-tertiary); }
.footer-links a:hover { color: var(--text-secondary); }

/* ── Pagination ── */
.pagination {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin: 32px 0;
  flex-wrap: wrap;
}
.page-btn {
  padding: 6px 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.page-btn:hover, .page-btn.active {
  border-color: var(--accent);
  color: var(--accent);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .nav-links { display: none; }
  .page-title { font-size: 1.5rem; }
  .market-hero-q { font-size: 1.2rem; }
  .cta-banner { flex-direction: column; }
  .market-table th:nth-child(n+4),
  .market-table td:nth-child(n+4) { display: none; }
  .crash-grid { grid-template-columns: 1fr; }
  .cat-grid { grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); }
}
@media (max-width: 480px) {
  .container { padding: 0 12px; }
  .stats-grid { grid-template-columns: 1fr 1fr; }
}
"""

# ─── HTML Shell ──────────────────────────────────────────────────────────────

def html_page(
    title: str,
    description: str,
    body: str,
    canonical: str = "",
    extra_head: str = "",
) -> str:
    canonical_tag = f'<link rel="canonical" href="{SITE_URL}{canonical}">' if canonical else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#0A0A0A">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:type" content="website">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{escape(title)}">
  <meta name="twitter:description" content="{escape(description)}">
  {canonical_tag}
  {extra_head}
  <style>{CSS}</style>
</head>
<body>
{_nav()}
{body}
{_footer()}
</body>
</html>"""

def _nav() -> str:
    return f"""<nav class="nav">
  <a class="nav-brand" href="/">Poly<span>Scope</span></a>
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/category/politics.html">Politics</a>
    <a href="/category/sports.html">Sports</a>
    <a href="/category/crypto.html">Crypto</a>
    <a href="/category/geopolitics.html">Geopolitics</a>
    <a href="/category/economics.html">Economics</a>
  </div>
  <div class="nav-right">
    <a href="{CHECKOUT_URL}" class="btn-primary" target="_blank" rel="noopener">Get Data $9</a>
  </div>
</nav>"""

def _footer() -> str:
    return f"""<footer>
  <div class="container">
    <div class="footer-inner">
      <span>Data by <a href="{LUCIFERFORGE_URL}" target="_blank" rel="noopener">LuciferForge</a> &bull; <a href="{PROTODEX_URL}" target="_blank" rel="noopener">protodex.io</a> &bull; Updated {BUILD_DATE}</span>
      <div class="footer-links">
        <a href="/">Screener</a>
        <a href="/category/politics.html">Politics</a>
        <a href="/category/sports.html">Sports</a>
        <a href="/category/crypto.html">Crypto</a>
        <a href="{CHECKOUT_URL}" target="_blank" rel="noopener">Full Data $9</a>
        <a href="{API_DOCS_URL}" target="_blank" rel="noopener">API</a>
      </div>
    </div>
  </div>
</footer>"""

def _cta_banner() -> str:
    return f"""<div class="cta-banner">
  <div class="cta-text">
    <strong>Want full price history + orderbook data?</strong><br>
    Access historical prices, depth charts, and real-time streams for all 2,000+ active markets.
  </div>
  <div class="cta-actions">
    <a href="{CHECKOUT_URL}" class="btn-primary" target="_blank" rel="noopener">
      ↗ Get Full Data — $9
    </a>
    <a href="{API_DOCS_URL}" class="btn-secondary" target="_blank" rel="noopener">
      ⚡ Real-time API
    </a>
  </div>
</div>"""

# ─── Homepage ────────────────────────────────────────────────────────────────

def build_homepage(markets: list[dict]) -> str:
    # Top movers (biggest absolute 24h change, need one_day_change != None)
    movers = sorted(
        [m for m in markets if m["one_day_change"] is not None],
        key=lambda m: abs(float(m["one_day_change"])),
        reverse=True
    )[:20]

    # Highest volume 24h
    top_volume = sorted(
        [m for m in markets if m["volume_24h"] and float(m["volume_24h"]) > 0],
        key=lambda m: float(m["volume_24h"]),
        reverse=True
    )[:20]

    # Crash signals: dropped >15% from recent high (proxy: one_day_change < -0.15)
    crash_signals = sorted(
        [m for m in markets if m["one_day_change"] is not None and float(m["one_day_change"]) <= -0.15],
        key=lambda m: float(m["one_day_change"])
    )[:12]

    # Category counts
    cat_counts: dict[str, int] = {}
    for m in markets:
        c = m["category"] or "other"
        cat_counts[c] = cat_counts.get(c, 0) + 1

    # Stats strip
    total = len(markets)
    total_vol = sum(float(m["volume_24h"] or 0) for m in markets)
    total_liq = sum(float(m["liquidity"] or 0) for m in markets)

    body = f"""<div class="container">
  <div class="page-header">
    <h1 class="page-title">Prediction Market <span style="color:var(--teal)">Screener</span></h1>
    <p class="page-subtitle">{total:,} active markets &bull; {fmt_volume(total_vol)} 24h volume &bull; {fmt_volume(total_liq)} liquidity &bull; Updated {BUILD_DATE}</p>
  </div>

  {_cta_banner()}

  <!-- CRASH SIGNALS -->
  <div class="section">
    <div class="section-header">
      <div class="section-title">
        <span class="dot" style="background:var(--danger)"></span>
        Crash Signals
      </div>
      <span style="font-size:12px;color:var(--text-tertiary)">Mean reversion probability: <strong style="color:var(--warning)">73%</strong> based on 5,629 historical events</span>
    </div>
    {_crash_grid(crash_signals)}
  </div>

  <!-- TOP MOVERS -->
  <div class="section">
    <div class="section-header">
      <div class="section-title">
        <span class="dot"></span>
        Top Movers (24h)
      </div>
    </div>
    {_market_table(movers, show_change=True)}
  </div>

  <!-- HIGHEST VOLUME -->
  <div class="section">
    <div class="section-header">
      <div class="section-title">
        <span class="dot" style="background:var(--accent)"></span>
        Highest Volume
      </div>
    </div>
    {_market_table(top_volume, show_change=False)}
  </div>

  <!-- CATEGORIES -->
  <div class="section">
    <div class="section-header">
      <div class="section-title">Browse by Category</div>
    </div>
    {_cat_grid(cat_counts)}
  </div>
</div>"""

    return html_page(
        title=f"{SITE_NAME} — Polymarket Prediction Market Screener",
        description=f"Real-time screener for {total:,} active Polymarket prediction markets. Top movers, highest volume, crash signals, and category filters.",
        body=body,
        canonical="/",
    )

def _crash_grid(markets: list[dict]) -> str:
    if not markets:
        return '<p style="color:var(--text-tertiary);font-size:13px;">No crash signals detected right now.</p>'
    cards = []
    for m in markets:
        change, _ = fmt_change(m["one_day_change"])
        price = fmt_pct(m["last_trade_price"])
        pre_crash = float(m["last_trade_price"] or 0) - float(m["one_day_change"] or 0)
        url = market_url(m["id"], m.get("slug"))
        q = escape(m["question"][:100])
        cards.append(f"""<a href="{url}" style="text-decoration:none;">
  <div class="crash-card">
    <div class="crash-drop">{change}</div>
    <div class="crash-question">{q}</div>
    <div class="crash-meta">
      Now: {price} &nbsp;|&nbsp; Pre-drop: {fmt_pct(pre_crash)} &nbsp;|&nbsp; {CATEGORY_LABELS.get(m['category'], 'Other')}
    </div>
  </div>
</a>""")
    return f'<div class="crash-grid">{"".join(cards)}</div>'

def _market_table(markets: list[dict], show_change: bool = True) -> str:
    change_col = '<th class="right">24h Change</th>' if show_change else ""
    rows = []
    for m in markets:
        url = market_url(m["id"], m.get("slug"))
        q = escape(m["question"])
        cat = CATEGORY_LABELS.get(m["category"], "Other")
        price = fmt_pct(m["last_trade_price"])
        vol24 = fmt_volume(m["volume_24h"])
        spread = f'{float(m["spread"]*100):.1f}¢' if m.get("spread") is not None else "—"
        end = fmt_date(m.get("end_date"))

        change_td = ""
        if show_change:
            chg, cls = fmt_change(m.get("one_day_change"))
            change_td = f'<td class="right mono {cls}">{chg}</td>'

        rows.append(f"""<tr>
  <td><a href="{url}" class="market-question">{q}</a></td>
  <td><span class="cat-badge">{cat}</span></td>
  <td class="right mono">{price}</td>
  <td class="right mono">{vol24}</td>
  {change_td}
  <td class="right mono">{spread}</td>
  <td class="right" style="color:var(--text-tertiary);font-size:12px;">{end}</td>
</tr>""")

    change_th = '<th class="right">24h</th>' if show_change else ""
    return f"""<div style="overflow-x:auto;">
<table class="market-table">
<thead><tr>
  <th>Market</th>
  <th>Category</th>
  <th class="right">Price</th>
  <th class="right">24h Vol</th>
  {change_th}
  <th class="right">Spread</th>
  <th class="right">Ends</th>
</tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
</div>"""

def _cat_grid(cat_counts: dict[str, int]) -> str:
    items = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    cards = []
    for cat, cnt in items:
        label = CATEGORY_LABELS.get(cat, cat.title())
        icon = CATEGORY_ICONS.get(cat, "🔮")
        url = f"/category/{cat}.html"
        cards.append(f"""<a href="{url}" style="text-decoration:none;">
  <div class="cat-card">
    <div class="cat-icon">{icon}</div>
    <div class="cat-name">{label}</div>
    <div class="cat-count">{cnt:,} markets</div>
  </div>
</a>""")
    return f'<div class="cat-grid">{"".join(cards)}</div>'

# ─── Category Pages ──────────────────────────────────────────────────────────

def build_category_page(cat: str, markets: list[dict]) -> str:
    label = CATEGORY_LABELS.get(cat, cat.title())
    icon = CATEGORY_ICONS.get(cat, "🔮")
    count = len(markets)
    total_vol = sum(float(m["volume_24h"] or 0) for m in markets)

    body = f"""<div class="container">
  <div class="page-header">
    <div class="breadcrumb">
      <a href="/">Home</a> <span>/</span> <span>Categories</span>
    </div>
    <h1 class="page-title">{icon} {label} Markets</h1>
    <p class="page-subtitle">{count:,} active markets &bull; {fmt_volume(total_vol)} 24h volume</p>
  </div>

  {_cta_banner()}

  <div class="section">
    <div class="section-header">
      <div class="section-title">
        <span class="dot"></span>
        All {label} Markets
      </div>
    </div>
    {_market_table(markets, show_change=True)}
  </div>
</div>"""

    return html_page(
        title=f"{label} Prediction Markets | {SITE_NAME}",
        description=f"Browse {count:,} active {label.lower()} prediction markets on Polymarket. Current prices, 24h volume, and market data.",
        body=body,
        canonical=f"/category/{cat}.html",
    )

# ─── Market Detail Pages ─────────────────────────────────────────────────────

def build_market_page(m: dict) -> tuple[str, str]:
    """Returns (filename, html)"""
    key = m.get("slug") or slugify(str(m["id"]))
    filename = f"{key}.html"

    q = m["question"]
    cat = m.get("category", "other")
    cat_label = CATEGORY_LABELS.get(cat, cat.title())
    price = fmt_pct(m["last_trade_price"])
    bid = fmt_pct(m["best_bid"])
    ask = fmt_pct(m["best_ask"])
    spread_raw = m.get("spread")
    spread = f'{float(spread_raw)*100:.1f}¢' if spread_raw is not None else "—"
    vol = fmt_volume(m["volume"])
    vol24 = fmt_volume(m["volume_24h"])
    liq = fmt_volume(m["liquidity"])
    chg, chg_cls = fmt_change(m.get("one_day_change"))
    end = fmt_date(m.get("end_date"))
    d_left = days_until(m.get("end_date"))
    days_str = f"{d_left} days left" if d_left is not None else ""

    # Price color
    ltp = float(m.get("last_trade_price") or 0)
    price_color = "var(--success)" if ltp >= 0.5 else "var(--warning)" if ltp >= 0.2 else "var(--danger)"

    # SEO title — strip leading "Will " if already present to avoid "Will Will..."
    q_clean = q.rstrip("?")
    q_lower = q_clean.lower()
    if q_lower.startswith("will "):
        page_title = f"{q_clean}? | {SITE_NAME}"
    else:
        page_title = f"Will {q_clean}? | {SITE_NAME}"
    page_desc = f"Current price: {price} ({chg} 24h). Volume: {vol24} in 24h. Ends {end}. Track this Polymarket prediction on {SITE_NAME}."

    body = f"""<div class="container">
  <div class="market-hero">
    <div class="breadcrumb">
      <a href="/">Home</a>
      <span>/</span>
      <a href="/category/{cat}.html">{cat_label}</a>
      <span>/</span>
      <span style="color:var(--text-tertiary)">Market</span>
    </div>
    <div class="market-hero-meta">
      <span class="cat-badge">{CATEGORY_ICONS.get(cat, '')} {cat_label}</span>
      {f'<span class="cat-badge" style="border-color:var(--warning);color:var(--warning)">{days_str}</span>' if days_str else ''}
    </div>
    <h1 class="market-hero-q">{escape(q)}</h1>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">Current Price</div>
      <div class="stat-value" style="color:{price_color}">{price}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">24h Change</div>
      <div class="stat-value {chg_cls}">{chg}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">24h Volume</div>
      <div class="stat-value">{vol24}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Total Volume</div>
      <div class="stat-value">{vol}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Liquidity</div>
      <div class="stat-value">{liq}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Bid / Ask</div>
      <div class="stat-value" style="font-size:1rem">{bid} / {ask}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Spread</div>
      <div class="stat-value">{spread}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Resolves</div>
      <div class="stat-value" style="font-size:1rem">{end}</div>
    </div>
  </div>

  {_cta_banner()}

  <div class="card" style="margin:24px 0;">
    <h2 style="font-size:1rem;font-weight:600;margin-bottom:12px;">About this Market</h2>
    <p style="color:var(--text-secondary);font-size:14px;line-height:1.7;">
      This is an active Polymarket prediction market. Traders buy YES/NO shares
      priced from 0¢ to 100¢ — the price reflects the crowd's estimated probability that
      the event resolves YES. A price of <strong style="color:var(--text-primary)">{price}</strong>
      means the market implies a <strong style="color:var(--text-primary)">{price}</strong> probability.
    </p>
    <p style="color:var(--text-secondary);font-size:14px;line-height:1.7;margin-top:12px;">
      Want full price history, orderbook depth, and real-time data?
      <a href="{CHECKOUT_URL}" target="_blank" rel="noopener" style="color:var(--accent)">Get the full dataset for $9 →</a>
    </p>
  </div>

  <div style="margin:32px 0;">
    <h2 style="font-size:1rem;font-weight:600;margin-bottom:16px;">More {cat_label} Markets</h2>
    <p style="color:var(--text-secondary);font-size:13px;">
      <a href="/category/{cat}.html">Browse all {cat_label} markets →</a>
    </p>
  </div>
</div>"""

    return filename, html_page(
        title=page_title,
        description=page_desc,
        body=body,
        canonical=f"/markets/{filename}",
    )

# ─── Sitemap ─────────────────────────────────────────────────────────────────

def build_sitemap(markets: list[dict], cats: list[str]) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    urls = [f"""  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>"""]
    for cat in cats:
        urls.append(f"""  <url>
    <loc>{SITE_URL}/category/{cat}.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>""")
    for m in markets:
        key = m.get("slug") or slugify(str(m["id"]))
        urls.append(f"""  <url>
    <loc>{SITE_URL}/markets/{key}.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>0.6</priority>
  </url>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{"".join(urls)}
</urlset>"""

# ─── robots.txt ──────────────────────────────────────────────────────────────

def build_robots() -> str:
    return f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""

# ─── 404 page ────────────────────────────────────────────────────────────────

def build_404() -> str:
    body = """<div class="container" style="text-align:center;padding:80px 20px;">
  <div style="font-size:4rem;margin-bottom:16px;">🔮</div>
  <h1 class="page-title" style="margin-bottom:12px;">404 — Market Not Found</h1>
  <p style="color:var(--text-secondary);margin-bottom:32px;">This market may have resolved or the URL changed.</p>
  <a href="/" class="btn-primary">← Back to Screener</a>
</div>"""
    return html_page(
        title=f"404 Not Found | {SITE_NAME}",
        description="Page not found.",
        body=body,
    )

# ─── Main Build ──────────────────────────────────────────────────────────────

def main():
    print(f"[PolyScope] Loading markets from {DB_PATH}...")
    markets = load_markets()
    print(f"[PolyScope] {len(markets):,} active markets loaded")

    # Ensure output dirs exist
    (OUT_DIR / "markets").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "category").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "assets").mkdir(parents=True, exist_ok=True)

    # Write CSS asset
    (OUT_DIR / "assets" / "style.css").write_text(CSS)

    # ── Homepage ──
    print("[PolyScope] Building homepage...")
    (OUT_DIR / "index.html").write_text(build_homepage(markets))

    # ── Category pages ──
    cats = sorted(set(m["category"] or "other" for m in markets))
    print(f"[PolyScope] Building {len(cats)} category pages...")
    for cat in cats:
        cat_markets = sorted(
            [m for m in markets if (m["category"] or "other") == cat],
            key=lambda m: float(m["volume_24h"] or 0),
            reverse=True,
        )
        html = build_category_page(cat, cat_markets)
        (OUT_DIR / "category" / f"{cat}.html").write_text(html)

    # ── Market detail pages ──
    print(f"[PolyScope] Building {len(markets):,} market pages...")
    for i, m in enumerate(markets):
        filename, html = build_market_page(m)
        (OUT_DIR / "markets" / filename).write_text(html)
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(markets)} market pages written...")

    # ── Sitemap ──
    print("[PolyScope] Building sitemap.xml...")
    (OUT_DIR / "sitemap.xml").write_text(build_sitemap(markets, cats))

    # ── robots.txt ──
    (OUT_DIR / "robots.txt").write_text(build_robots())

    # ── 404 ──
    (OUT_DIR / "404.html").write_text(build_404())

    # ── CNAME ──
    (OUT_DIR / "CNAME").write_text("")  # blank — set custom domain later

    # ── _config.yml for GitHub Pages ──
    (OUT_DIR / ".nojekyll").write_text("")  # Disable Jekyll processing

    # ── Build stats ──
    market_files = list((OUT_DIR / "markets").glob("*.html"))
    cat_files = list((OUT_DIR / "category").glob("*.html"))
    total_bytes = sum(f.stat().st_size for f in market_files) + \
                  sum(f.stat().st_size for f in cat_files) + \
                  (OUT_DIR / "index.html").stat().st_size

    print(f"""
[PolyScope] Build complete!
  Homepage:       {OUT_DIR}/index.html
  Category pages: {len(cat_files)} ({', '.join(cats)})
  Market pages:   {len(market_files):,}
  Sitemap URLs:   {1 + len(cats) + len(markets):,}
  Total size:     {total_bytes / 1_048_576:.1f} MB
  Output dir:     {OUT_DIR}
""")

if __name__ == "__main__":
    main()
