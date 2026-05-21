# PolyScope

**Free Polymarket prediction-market screener.** 13,963 markets indexed, top movers, highest volume, crash signals, and category filters — all in one page.

🔗 **Live:** https://luciferforge.github.io/polyscope/

## What it shows

- **24h movers** — biggest price swings across active markets
- **Volume leaders** — what's actually trading, not what's just listed
- **Crash signals** — markets that lost >20% in 1h, where mean-reversion historically wins ~80% (see [cross-signal-data](https://github.com/LuciferForge/cross-signal-data))
- **Category filters** — politics, crypto, sports, economics, AI, etc.
- **Active markets only** — `closed=false` Gamma API filter, daily refresh

## How it's built

- Static site generator: `build_screener.py` calls the Polymarket Gamma API, ranks markets, and writes `docs/index.html` + per-market pages.
- Hosted on GitHub Pages. Zero backend, zero subscription, zero login.
- Source of truth for the screener data: same pipeline that powers [api.protodex.io](https://api.protodex.io) and the [Polymarket Historical Dataset](https://gumroad.com/l/agyjd?utm_source=github&utm_medium=readme&utm_campaign=polyscope-week22) on Gumroad.

## Why this exists

Polymarket's own UI optimises for individual market depth. If you want to **scan** the universe for opportunities — "what crashed in the last hour", "where is volume actually concentrated", "what political markets exist under 20¢" — you need a screener. There wasn't a free one, so this is it.

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

The screener shows the latest snapshot. If you want the **full historical price series** — 9.5M+ snapshots across 9,550 markets for backtesting and feature engineering — that's the [Polymarket Historical Dataset](https://gumroad.com/l/agyjd?utm_source=github&utm_medium=readme&utm_campaign=polyscope-week22).

## License

MIT.
