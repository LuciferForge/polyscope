# PolyScope

**Free Polymarket prediction-market screener.** 15,841 markets indexed, top movers, highest volume, crash signals, and category filters — all in one page.

🔗 **Live:** https://luciferforge.github.io/polyscope/

## What it shows

- **24h movers** — biggest price swings across active markets
- **Volume leaders** — what's actually trading, not what's just listed
- **Crash signals** — markets down ≥15% over 24h (`one_day_change <= -0.15` in [`build_screener.py`](build_screener.py#L644-L646)), a proxy for "dropped from a recent high" mean-reversion setups. See the [methodology discussion](https://github.com/LuciferForge/polyscope/discussions/2) for honest caveats and how the historical 73% / 5,629-event number from [cross-signal-data](https://github.com/LuciferForge/cross-signal-data) relates to (but isn't identical to) this proxy.
- **Category filters** — politics, crypto, sports, economics, AI, etc.
- **Active markets only** — `closed=false` Gamma API filter, daily refresh

## How it's built

- Static site generator: `build_screener.py` calls the Polymarket Gamma API, ranks markets, and writes `docs/index.html` + per-market pages.
- Hosted on GitHub Pages. Zero backend, zero subscription, zero login.
- Source of truth for the screener data: same pipeline that powers [api.protodex.io](https://api.protodex.io) and the [Polymarket Historical Dataset](https://gumroad.com/l/agyjd?utm_source=github&utm_medium=readme&utm_campaign=polyscope-week22) on Gumroad.

## Why this exists

Polymarket's own UI optimises for individual market depth. If you want to **scan** the universe for opportunities — "what dropped ≥15% in the last 24h", "where is volume actually concentrated", "what political markets exist under 20¢" — you need a screener. There wasn't a free one, so this is it.

## Run it yourself

```bash
git clone https://github.com/LuciferForge/polyscope.git
cd polyscope
pip install requests
python build_screener.py
open docs/index.html
```

No API key required. Hits the public Gamma endpoint.

## Want the underlying data?

The screener shows the latest snapshot. If you want the **full historical price series** — 15.69M+ price snapshots and 1.54M+ orderbook snapshots across 15,841 markets, 61+ days of depth, for backtesting and feature engineering — that's the [Polymarket Historical Dataset](https://gumroad.com/l/agyjd?utm_source=github&utm_medium=readme&utm_campaign=polyscope-week22) ($9, SQLite + CSV). Stats live at [api.protodex.io/stats](https://api.protodex.io/stats).

## Community / open questions

The roadmap is being shaped in the open. Live threads (jump in if any of these are useful — comments directly influence what ships next):

- [#5 — Show & tell: how I screen 13,963 markets in 30 seconds](https://github.com/LuciferForge/polyscope/discussions/5) — the actual workflow, start here if you're new
- [#1 — What screener views would you actually use?](https://github.com/LuciferForge/polyscope/discussions/1) — liquidity-weighted movers, new-market alerts, resolution-soon view, cross-market correlations
- [#2 — How the "Crash Signal" actually works (methodology + the 73% number)](https://github.com/LuciferForge/polyscope/discussions/2) — full implementation + caveats, no marketing
- [#3 — Movers vs Volume: which list do you open first?](https://github.com/LuciferForge/polyscope/discussions/3) — defaults, min-volume sliders, opinionated vs configurable
- [#4 — For backtesters: what's missing from the historical dataset?](https://github.com/LuciferForge/polyscope/discussions/4) — order-book depth, trade tape, resolution joins, news tagging

PRs equally welcome — [`build_screener.py`](build_screener.py) is ~750 lines of plain Python.

## License

MIT.
