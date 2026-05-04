from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


BASE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PortWatch Tanker Port Calls</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  body { font-family: sans-serif; margin: 0; padding: 20px; }
  #container { width: 100%; max-width: 1200px; margin: 0 auto; }
  #controls { margin-bottom: 10px; }
  #controls label { font-size: 14px; margin-right: 8px; }
  #country-select { font-size: 14px; padding: 4px 8px; }
  #loading { text-align: center; padding: 40px; color: #666; }
  #source-note { margin-bottom: 12px; color: #666; font-size: 13px; }
</style>
</head>
<body>
<div id="container">
  <div id="loading">Loading data...</div>
  <div id="controls" style="display:none;">
    <label for="country-select">Country:</label>
    <select id="country-select"></select>
  </div>
  <div id="source-note" style="display:none;"></div>
  <div id="chart"></div>
</div>
<script>
const EMBEDDED_CSV_TEXT = __EMBEDDED_CSV_TEXT__;
const GENERATED_AT = __GENERATED_AT__;
const YEARS = ["2024", "2025", "2026"];
const COLORS = {"2024": "#636EFA", "2025": "#EF553B", "2026": "#00CC96"};
const START_LABEL = "Mar 1";

function dayOfYearToLabel(day) {
  const d = new Date(2024, 0, day);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function parseCSV(text) {
  const lines = text.replace(/\\r/g, "").trim().split("\\n");
  const headers = lines[0].split(",");
  const numCols = headers.length;
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const row = {};
    let fields;
    if (lines[i].includes('"')) {
      fields = [];
      let inQuote = false, field = "";
      for (const ch of lines[i]) {
        if (ch === '"') { inQuote = !inQuote; }
        else if (ch === "," && !inQuote) { fields.push(field); field = ""; }
        else { field += ch; }
      }
      fields.push(field);
    } else {
      fields = lines[i].split(",");
    }
    while (fields.length < numCols) fields.push("");
    for (let j = 0; j < numCols; j++) {
      row[headers[j]] = fields[j];
    }
    rows.push(row);
  }
  return rows;
}

function normalizedDayToIsoDate(day, year) {
  const isLeapYear = new Date(Date.UTC(year, 1, 29)).getUTCDate() === 29;
  let actualDay = day;
  if (!isLeapYear && day >= 61) actualDay -= 1;

  const date = new Date(Date.UTC(year, 0, actualDay));
  return date.toISOString().slice(0, 10);
}

function latestAvailableDate(rows) {
  let latestIsoDate = null;
  for (const row of rows) {
    const day = parseInt(row.day_of_year, 10);
    if (Number.isNaN(day)) continue;

    for (const year of YEARS) {
      if (!row[year]) continue;
      const isoDate = normalizedDayToIsoDate(day, parseInt(year, 10));
      if (!latestIsoDate || isoDate > latestIsoDate) {
        latestIsoDate = isoDate;
      }
    }
  }
  return latestIsoDate;
}

function formatDateLabel(isoDate) {
  const parsed = new Date(isoDate + "T00:00:00Z");
  if (Number.isNaN(parsed.getTime())) return isoDate;
  return parsed.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric"
  });
}

function renderChart(rows) {
  document.getElementById("loading").style.display = "none";
  document.getElementById("controls").style.display = "block";

  const sourceNote = document.getElementById("source-note");
  const latestDate = latestAvailableDate(rows);
  if (latestDate) {
    sourceNote.textContent = "Latest available PortWatch data: " + formatDateLabel(latestDate);
    sourceNote.style.display = "block";
  }

  const byCountry = {};
  for (const row of rows) {
    const c = row.country;
    if (!byCountry[c]) byCountry[c] = [];
    byCountry[c].push(row);
  }
  const countries = Object.keys(byCountry).sort();

  const select = document.getElementById("country-select");
  for (const c of countries) {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    select.appendChild(opt);
  }

  function buildTraces(country) {
    const cRows = byCountry[country];
    const traces = [];
    for (const year of YEARS) {
      const labels = [], vals = [];
      for (const row of cRows) {
        const v = row[year];
        if (v !== undefined && v !== "") {
          labels.push(dayOfYearToLabel(parseInt(row.day_of_year, 10)));
          vals.push(parseFloat(v));
        }
      }
      traces.push({
        x: labels, y: vals,
        mode: "lines",
        name: year,
        line: { color: COLORS[year], width: 2 }
      });
    }
    return traces;
  }

  function plotCountry(country) {
    const traces = buildTraces(country);
    const layout = {
      title: "Cumulative Tanker Port Calls Since " + START_LABEL + " - " + country,
      xaxis: { title: "Date (" + START_LABEL + " onward)", tickmode: "auto", nticks: 20 },
      yaxis: { title: "Cumulative Tanker Calls Since " + START_LABEL },
      legend: { x: 0.01, y: 0.99, bgcolor: "rgba(255,255,255,0.7)" },
      template: "plotly_white",
      height: 600
    };
    Plotly.react("chart", traces, layout, { responsive: true });
  }

  select.addEventListener("change", () => plotCountry(select.value));
  plotCountry(countries[0]);
}

try {
  const rows = parseCSV(EMBEDDED_CSV_TEXT);
  renderChart(rows);
} catch (err) {
  document.getElementById("loading").textContent = "Error loading embedded data: " + err.message;
}
</script>
</body>
</html>
"""


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    csv_path = repo_root / "portwatch_tanker_cumulative_by_country.csv"
    output_path = repo_root / "portwatch_tanker_chart_embedded.html"

    csv_text = csv_path.read_text(encoding="utf-8")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = (
        BASE_HTML.replace("__EMBEDDED_CSV_TEXT__", json.dumps(csv_text))
        .replace("__GENERATED_AT__", json.dumps(generated_at))
    )
    output_path.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
