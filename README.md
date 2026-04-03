# Tanker Port Calls Tracker

Daily tracker of tanker port calls by country, sourced from [IMF PortWatch](https://portwatch.imf.org/). An automated pipeline fetches updated data and publishes an interactive chart to GitHub Pages.

**Live chart**: [cherrylchico.github.io/tanker_port_calls/portwatch_tanker_chart.html](https://cherrylchico.github.io/tanker_port_calls/portwatch_tanker_chart.html)

## How It Works

A GitHub Actions workflow runs daily at 06:00 UTC:

1. Fetches the last 14 days of tanker port call data from the PortWatch ArcGIS API (re-fetches to capture any revisions)
2. Updates `portwatch_tanker_daily_by_country.csv` with new and revised data
3. Rebuilds `portwatch_tanker_cumulative_by_country.csv` with cumulative totals per country starting on March 1 of each year
4. Commits updated CSVs and deploys to GitHub Pages

The interactive chart loads the cumulative CSV at runtime, so routine data refreshes happen through the CSV rather than manual HTML edits.

## Files

| File | Description |
|------|-------------|
| `update_portwatch.py` | Daily update script — fetches from API, updates CSVs |
| `portwatch_tanker_chart.html` | Interactive Plotly chart with country dropdown |
| `portwatch_tanker_daily_by_country.csv` | Daily tanker port calls by country (2024+) |
| `portwatch_tanker_cumulative_by_country.csv` | Cumulative tanker calls since March 1, pivoted by year |
| `bootstrap_daily.py` | One-time script to initialize daily CSV from raw PortWatch data |
| `portwatch_tanker_update.ipynb` | Original exploratory notebook |
| `.github/workflows/update-portwatch.yml` | GitHub Actions workflow |

## Data Source

[IMF PortWatch](https://portwatch.imf.org/) — Daily Ports Data via ArcGIS REST API. Data is aggregated to country-day level using server-side statistics. PortWatch typically has a 5-6 day lag from the current date.
