"""Decide whether the scheduled PortWatch workflow should proceed."""

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

STATE_FILE = Path("portwatch_update_state.json")
ET_TZ = ZoneInfo("America/New_York")


def most_recent_monday(day_in_et):
    return day_in_et - timedelta(days=day_in_et.weekday())


def main():
    event_name = os.environ["GITHUB_EVENT_NAME"]
    out_path = Path(os.environ["GITHUB_OUTPUT"])
    now_et = datetime.now(timezone.utc).astimezone(ET_TZ)
    today_et = now_et.date()

    should_run = True
    reason = f"event {event_name} always runs"

    if event_name == "schedule":
        if now_et.hour != 10:
            should_run = False
            reason = f"skip {now_et.isoformat()} because it is not 10:00 AM ET"
        elif today_et.weekday() == 0:
            should_run = True
            reason = f"weekly Monday check for {today_et.isoformat()}"
        else:
            cycle_monday = most_recent_monday(today_et)
            last_completed = None
            if STATE_FILE.exists():
                with STATE_FILE.open() as f:
                    state = json.load(f)
                # Backward-compatible read: old state used Tuesday cycle key.
                raw = state.get("last_completed_cycle_monday") or state.get(
                    "last_completed_cycle_tuesday"
                )
                if raw:
                    last_completed = date.fromisoformat(raw)

            should_run = last_completed is None or last_completed < cycle_monday
            if should_run:
                reason = (
                    f"cycle {cycle_monday.isoformat()} is still pending; "
                    "keep checking daily until source data advances"
                )
            else:
                reason = (
                    f"cycle {cycle_monday.isoformat()} already completed on "
                    f"{last_completed.isoformat()}; skip extra daily check"
                )

    print(reason)
    with out_path.open("a") as f:
        f.write(f"should_run={'true' if should_run else 'false'}\n")
        f.write(f"reason={reason}\n")


if __name__ == "__main__":
    main()
