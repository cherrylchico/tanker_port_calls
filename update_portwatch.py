"""Fetch last 14 days of PortWatch tanker data and rebuild cumulative output.

Designed to run daily via GitHub Actions. Re-fetches the last 14 days
because PortWatch may revise recent data, then appends any new days
beyond the existing dataset.
"""

import requests
import pandas as pd
import time
from datetime import date, timedelta

BASE_URL = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Ports_Data/FeatureServer/0/query"
DAILY_CSV = "portwatch_tanker_daily_by_country.csv"
CUMULATIVE_CSV = "portwatch_tanker_cumulative_by_country.csv"
YEARS = [2024, 2025, 2026]


def fetch_aggregated_page(where_clause, offset=0, page_size=1000):
    params = {
        "where": where_clause,
        "outStatistics": '[{"statisticType":"sum","onStatisticField":"portcalls_tanker","outStatisticFieldName":"portcalls_tanker"}]',
        "groupByFieldsForStatistics": "country,year,month,day",
        "resultRecordCount": page_size,
        "resultOffset": offset,
        "f": "json",
    }
    resp = requests.get(BASE_URL, params=params, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    features = data.get("features", [])
    records = [f["attributes"] for f in features]
    exceeded = data.get("exceededTransferLimit", False)
    return records, exceeded


def fetch_date_range(start_date, end_date):
    """Fetch aggregated tanker data for a date range."""
    clauses = []
    # Group by year-month ranges to build a WHERE clause
    current = start_date
    while current <= end_date:
        y, m, d_start = current.year, current.month, current.day
        # End of this month or end_date, whichever is earlier
        if current.month == 12:
            month_end = date(current.year, 12, 31)
        else:
            month_end = date(current.year, current.month + 1, 1) - timedelta(days=1)
        chunk_end = min(month_end, end_date)
        d_end = chunk_end.day

        clauses.append(
            f"(year = {y} AND month = {m} AND day >= {d_start} AND day <= {d_end})"
        )
        current = chunk_end + timedelta(days=1)

    where = " OR ".join(clauses)
    print(f"Fetching: {start_date} to {end_date}")

    all_records = []
    offset = 0
    while True:
        records, exceeded = fetch_aggregated_page(where, offset)
        all_records.extend(records)
        if not exceeded or len(records) == 0:
            break
        offset += len(records)
        time.sleep(0.3)

    print(f"  Fetched {len(all_records)} records")
    return all_records


def main():
    today = date.today()
    lookback_start = today - timedelta(days=14)

    # Load existing daily data
    try:
        daily = pd.read_csv(DAILY_CSV)
        daily["date"] = pd.to_datetime(daily["date"])
        print(f"Loaded {DAILY_CSV}: {len(daily):,} rows, {daily['date'].min().date()} to {daily['date'].max().date()}")
    except FileNotFoundError:
        print(f"{DAILY_CSV} not found — will create from scratch")
        daily = pd.DataFrame(columns=["country", "date", "tanker_calls"])
        daily["date"] = pd.to_datetime(daily["date"])

    # Fetch last 14 days (re-fetch for revisions) plus any days after existing max
    fetch_start = lookback_start
    if len(daily) > 0:
        existing_max = daily["date"].max().date()
        # Also fetch anything beyond existing max if that's earlier than lookback
        fetch_start = min(fetch_start, existing_max - timedelta(days=1))

    records = fetch_date_range(fetch_start, today)

    if records:
        new_df = pd.DataFrame(records)
        new_df["date"] = pd.to_datetime(
            new_df[["year", "month", "day"]].rename(columns={"year": "year", "month": "month", "day": "day"})
        )
        new_df = new_df.rename(columns={"portcalls_tanker": "tanker_calls"})
        new_df = new_df[["country", "date", "tanker_calls"]]

        # Remove overlapping dates from existing, then append new
        if len(daily) > 0:
            overlap_mask = daily["date"] >= pd.Timestamp(fetch_start)
            removed = overlap_mask.sum()
            daily = daily[~overlap_mask]
            print(f"Removed {removed} existing rows from {fetch_start} onward (will be replaced)")

        daily = pd.concat([daily, new_df], ignore_index=True)
        daily = daily.groupby(["country", "date"], as_index=False)["tanker_calls"].sum()
    else:
        print("No new records from API")

    # Filter to target years
    daily["year"] = daily["date"].dt.year
    daily = daily[daily["year"].isin(YEARS)].copy()
    daily = daily.sort_values(["country", "date"]).reset_index(drop=True)

    # Save daily data
    daily[["country", "date", "tanker_calls"]].to_csv(DAILY_CSV, index=False)
    print(f"Saved {DAILY_CSV}: {len(daily):,} rows, {daily['date'].min().date()} to {daily['date'].max().date()}")

    # Build cumulative output
    countries = sorted(daily["country"].unique())
    max_date = daily["date"].max().date()

    frames = []
    for yr in YEARS:
        start = date(yr, 1, 1)
        end = min(date(yr, 12, 31), max_date)
        if start > end:
            continue
        dates = pd.date_range(start, end, freq="D")
        for c in countries:
            tmp = pd.DataFrame({"country": c, "date": dates, "year": yr})
            frames.append(tmp)

    grid = pd.concat(frames, ignore_index=True)
    merged = grid.merge(daily[["country", "date", "tanker_calls"]], on=["country", "date"], how="left")
    merged["tanker_calls"] = merged["tanker_calls"].fillna(0).astype(int)
    merged = merged.sort_values(["country", "year", "date"]).reset_index(drop=True)
    merged["cumulative_tanker"] = merged.groupby(["country", "year"])["tanker_calls"].cumsum()
    # Normalize day_of_year so leap and non-leap years align:
    # In non-leap years, shift days after Feb 28 by +1 to match leap year numbering
    doy = merged["date"].dt.dayofyear
    is_leap = merged["date"].dt.is_leap_year
    after_feb = merged["date"].dt.month >= 3
    merged["day_of_year"] = doy + (~is_leap & after_feb).astype(int)

    pivot = merged.pivot_table(
        index=["country", "day_of_year"],
        columns="year",
        values="cumulative_tanker",
        aggfunc="first",
    )
    pivot.columns = [str(int(c)) for c in pivot.columns]
    pivot = pivot.reset_index()

    pivot.to_csv(CUMULATIVE_CSV, index=False)
    print(f"Saved {CUMULATIVE_CSV}: {pivot.shape}")


if __name__ == "__main__":
    main()
