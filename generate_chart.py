"""Generate a self-contained HTML chart of cumulative tanker port calls by country."""

import pandas as pd
import json

df = pd.read_csv("portwatch_tanker_cumulative_by_country.csv")
countries = sorted(df["country"].unique())
years = ["2024", "2025", "2026"]
colors = {"2024": "#636EFA", "2025": "#EF553B", "2026": "#00CC96"}
START_LABEL = "Mar 1"

# Convert normalized day_of_year values to readable labels using 2024 as the leap-year reference.
date_index = pd.date_range("2024-01-01", periods=366, freq="D")

# Build traces: 3 per country (one per year), only first country visible
traces = []
buttons = []

for i, country in enumerate(countries):
    cdf = df[df["country"] == country]
    for year in years:
        if year not in cdf.columns:
            continue
        sub = cdf[["day_of_year", year]].dropna()
        if sub.empty:
            continue
        days = sub["day_of_year"].astype(int).tolist()
        vals = sub[year].astype(int).tolist()
        # Use month-day labels
        labels = [date_index[d - 1].strftime("%b %d") for d in days]
        traces.append({
            "x": labels,
            "y": vals,
            "mode": "lines",
            "name": year,
            "line": {"color": colors[year], "width": 2},
            "visible": i == 0,
            "meta": country,
        })

# Build dropdown buttons
traces_per_country = len(years)
for i, country in enumerate(countries):
    visibility = [False] * len(traces)
    start = i * traces_per_country
    for j in range(traces_per_country):
        if start + j < len(traces):
            visibility[start + j] = True
    buttons.append({
        "label": country,
        "method": "update",
        "args": [
            {"visible": visibility},
            {"title": f"Cumulative Tanker Port Calls Since {START_LABEL} — {country}"},
        ],
    })

layout = {
    "title": f"Cumulative Tanker Port Calls Since {START_LABEL} — {countries[0]}",
    "xaxis": {
        "title": f"Date ({START_LABEL} onward)",
        "tickmode": "auto",
        "nticks": 20,
    },
    "yaxis": {"title": f"Cumulative Tanker Calls Since {START_LABEL}"},
    "updatemenus": [
        {
            "buttons": buttons,
            "direction": "down",
            "showactive": True,
            "x": 0.0,
            "xanchor": "left",
            "y": 1.18,
            "yanchor": "top",
            "active": 0,
        }
    ],
    "legend": {"x": 0.01, "y": 0.99, "bgcolor": "rgba(255,255,255,0.7)"},
    "template": "plotly_white",
    "height": 600,
}

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PortWatch Tanker Port Calls</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
</head>
<body>
<div id="chart" style="width:100%;max-width:1200px;margin:0 auto;"></div>
<script>
var traces = {json.dumps(traces)};
var layout = {json.dumps(layout)};
Plotly.newPlot("chart", traces, layout, {{responsive: true}});
</script>
</body>
</html>"""

with open("portwatch_tanker_chart.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Generated portwatch_tanker_chart.html ({len(traces)} traces, {len(countries)} countries)")
