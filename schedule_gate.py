"""Decide whether the scheduled PortWatch workflow should proceed."""

import os
from pathlib import Path


def main():
    event_name = os.environ["GITHUB_EVENT_NAME"]
    out_path = Path(os.environ["GITHUB_OUTPUT"])

    should_run = True
    reason = f"event {event_name} always runs"

    if event_name == "schedule":
        reason = "scheduled run at 8:00 AM UTC always proceeds"

    print(reason)
    with out_path.open("a") as f:
        f.write(f"should_run={'true' if should_run else 'false'}\n")
        f.write(f"reason={reason}\n")


if __name__ == "__main__":
    main()
