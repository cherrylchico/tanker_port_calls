"""One-time script: create portwatch_tanker_daily_by_country.csv from Daily_Ports_Data.csv."""

import pandas as pd

df = pd.read_csv("Daily_Ports_Data.csv", usecols=["date", "year", "country", "portcalls_tanker"])
df["date"] = pd.to_datetime(df["date"])
df = df[df["year"] >= 2024].copy()

agg = df.groupby(["country", "date"], as_index=False)["portcalls_tanker"].sum()
agg = agg.rename(columns={"portcalls_tanker": "tanker_calls"})
agg = agg.sort_values(["country", "date"]).reset_index(drop=True)

agg[["country", "date", "tanker_calls"]].to_csv("portwatch_tanker_daily_by_country.csv", index=False)
print(f"Created: {len(agg):,} rows, {agg['date'].min().date()} to {agg['date'].max().date()}")
