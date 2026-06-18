# Tanker Port Calls Tracker

## Overview

This project tracks **tanker port calls** by country, using daily data from [IMF PortWatch](https://portwatch.imf.org/). A "port call" is a single visit by a ship to a port, so counting tanker port calls is a simple way to measure how much tanker traffic — and, by extension, oil and gas shipping — is moving through a country's ports.

The objective is to see **how the Strait of Hormuz disruption has affected tanker traffic.**

**Background:** The Strait of Hormuz — a narrow waterway between Iran and Oman/the UAE — is one of the world's most important oil-shipping chokepoints, carrying a large share of globally traded oil. Traffic through it was largely blocked from **28 February 2026**, when the United States and Israel launched an air war against Iran, cutting tanker movements through the Gulf to a trickle. 

To make any shift visible, the tracker counts tanker calls **cumulatively starting on March 1 of each year** and overlays **2026 against 2024 and 2025** as comparison baselines. Because every year's running total restarts from zero on the same date, the three lines can be read side by side: where the 2026 line pulls noticeably above or below the 2024 and 2025 lines, that gap is the signal of how traffic has changed.

An automated pipeline keeps the data current and publishes an interactive chart (one country at a time, selected from a dropdown) to GitHub Pages.

**Live chart**: [Tanker Port Calls Tracker](https://cherrylchico.github.io/tanker_port_calls/portwatch_tanker_chart.html)

## How It Works

A GitHub Actions workflow runs every day at 15:00 UTC (10–11 AM ET). PortWatch refreshes its data weekly on Tuesdays ~9 AM ET, so the daily run is timed to land after that update; the other days act as a retry net for late updates and revisions.

1. Fetches the last 14 days of tanker port call data from the PortWatch ArcGIS API (re-fetches to capture any revisions)
2. Updates `portwatch_tanker_daily_by_country.csv` with new and revised data
3. Rebuilds `portwatch_tanker_cumulative_by_country.csv` with cumulative totals per country starting on March 1 of each year
4. Commits updated CSVs and scheduler state, then deploys to GitHub Pages

The interactive chart loads the cumulative CSV at runtime, so routine data refreshes happen through the CSV rather than manual HTML edits.

## Manual Tools

These are run by hand and are **not** part of the daily workflow. Both use [uv](https://docs.astral.sh/uv/) for dependencies.

### Rebuild / verify the cumulative data — `portwatch_tanker_update.ipynb`

A notebook that rebuilds `portwatch_tanker_cumulative_by_country.csv` from the maintained daily CSV plus a 14-day PortWatch API top-up (the same logic as `update_portwatch.py`). Use it to manually refresh or verify the cumulative output, or to explore the data interactively. Full details (data source, requirements, outputs) are documented in the notebook's own header.

```bash
uv run jupyter lab            # interactive: open the notebook, then Run All
# or headless:
uv run jupyter nbconvert --to notebook --execute --inplace portwatch_tanker_update.ipynb
```

By default it writes only the cumulative CSV; set `WRITE_DAILY_CSV = True` in the config cell to also overwrite the daily CSV.

### Build the self-contained chart — `build_embedded_chart.py`

`portwatch_tanker_chart_embedded.html` is a standalone version of the chart with the data **baked in** (no runtime CSV fetch). The workflow does **not** rebuild it, so refresh it by hand whenever the cumulative CSV changes:

```bash
uv run build_embedded_chart.py
```

It reads the current `portwatch_tanker_cumulative_by_country.csv` and overwrites the embedded HTML in place — so make sure the CSV is up to date first (e.g. run the notebook or `update_portwatch.py` beforehand).

## Files

| File | Description |
|------|-------------|
| `update_portwatch.py` | Update script — fetches from API, updates CSVs, tracks weekly refresh state |
| `schedule_gate.py` | Workflow helper that lets scheduled runs proceed |
| `portwatch_tanker_chart.html` | Interactive Plotly chart that loads the cumulative CSV at runtime (auto-updates on deploy) |
| `build_embedded_chart.py` | Manual script that bakes the cumulative CSV into a standalone HTML chart |
| `portwatch_tanker_chart_embedded.html` | Self-contained chart with data embedded — rebuilt by `build_embedded_chart.py` |
| `portwatch_tanker_daily_by_country.csv` | Daily tanker port calls by country (2024+) |
| `portwatch_tanker_cumulative_by_country.csv` | Cumulative tanker calls since March 1, pivoted by year |
| `portwatch_update_state.json` | Scheduler state used by the update script |
| `bootstrap_daily.py` | One-time script to initialize daily CSV from raw PortWatch data |
| `portwatch_tanker_update.ipynb` | Manual notebook to rebuild/verify the cumulative CSV (see Manual Tools) |
| `.github/workflows/update-portwatch.yml` | GitHub Actions workflow |

## Deploy Your Own Copy

Starting from a local clone of this repository, here is how to run and publish it under your own GitHub account.

**Prerequisites:** [git](https://git-scm.com/), a GitHub account, and [uv](https://docs.astral.sh/uv/) (for the Python scripts).

### Option A — run locally (no GitHub needed)

This refreshes the data and produces a standalone chart you can open in a browser:

```bash
uv run update_portwatch.py        # fetch latest data from PortWatch into the CSVs
uv run build_embedded_chart.py    # bake the CSV into portwatch_tanker_chart_embedded.html
```

Then open `portwatch_tanker_chart_embedded.html` directly in your browser. Nothing is published.

### Option B — publish the live, auto-updating site

1. **Create your own GitHub repo** and push this local copy to it:
   ```bash
   git remote set-url origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin master
   ```
   (Use `git remote add origin ...` instead if no remote is set.)

2. **Enable GitHub Pages:** repo **Settings → Pages → Build and deployment → Source: GitHub Actions**.

3. **Allow the workflow to commit data:** **Settings → Actions → General → Workflow permissions → Read and write permissions**. The daily job commits the refreshed CSVs back to the repo, so it needs write access.

4. **Update the live-chart link** near the top of this README to your own Pages URL. Once deployed, the chart lives at:
   ```
   https://<your-username>.github.io/<your-repo>/portwatch_tanker_chart.html
   ```
   (The chart loads its CSV by a relative path, so no other URLs need changing.)

5. **Trigger the first build:** go to the **Actions** tab → **Update PortWatch Data** → **Run workflow** (manual `workflow_dispatch`), or just push any commit. After that the workflow runs automatically every day at 15:00 UTC.

## Data Source

[IMF PortWatch](https://portwatch.imf.org/) — Daily Ports Data via ArcGIS REST API. Data is aggregated to country-day level using server-side statistics. PortWatch typically has a 5-6 day lag from the current date.
