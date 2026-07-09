#!/usr/bin/env python3
"""Snapshot 2026 USGS earthquake data to a CSV for offline analysis.

Fetches every magnitude >= 2.5 earthquake from 2026-01-01 up to (but not
including) today from the USGS FDSN event API, one calendar month at a time,
and writes the rows to data/earthquakes_2026.csv using the same column layout
as the `earthquakes` Supabase table (see create_table.sql / README).

The snapshot powers `earthquake_analysis_2026.ipynb`, so the notebook can be
re-run without network access or Supabase credentials. Re-running this script
refreshes the snapshot in place.

No environment variables required — the USGS API is public.
"""

import csv
import os
import time
from datetime import datetime, timezone

from sync_earthquakes import MIN_MAGNITUDE, fetch_features, transform

SNAPSHOT_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "data", "earthquakes_2026.csv")

# Same column order as the Supabase table (minus fetched_at, which is
# database-generated).
COLUMNS = [
    "event_id", "title", "magnitude", "mag_type", "depth_km",
    "latitude", "longitude", "place", "event_time", "updated_time",
    "felt", "cdi", "mmi", "alert", "tsunami", "significance",
    "event_type", "status", "net", "url",
]


def month_windows(start, end):
    """Yield (window_start, window_end) tuples, one calendar month at a time."""
    cur = start
    while cur < end:
        if cur.month == 12:
            nxt = cur.replace(year=cur.year + 1, month=1, day=1)
        else:
            nxt = cur.replace(month=cur.month + 1, day=1)
        yield cur, min(nxt, end)
        cur = nxt


def main():
    # Snapshot through the most recent complete UTC day so the last data
    # point isn't a misleading partial day.
    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0,
                                             microsecond=0)
    rows = []
    print(
        f"Snapshotting USGS earthquakes {SNAPSHOT_START.date()} -> {end.date()} "
        f"(min magnitude {MIN_MAGNITUDE})...",
        flush=True,
    )
    for w_start, w_end in month_windows(SNAPSHOT_START, end):
        features = fetch_features(w_start, w_end)
        rows.extend(transform(f) for f in features)
        print(f"  {w_start.date()} -> {w_end.date()}: {len(features)} events "
              f"(running total {len(rows)})", flush=True)
        time.sleep(0.5)  # be polite to the USGS API between windows

    # De-duplicate on event_id (windows share boundary instants) and keep a
    # stable chronological order so re-runs produce clean diffs.
    deduped = {row["event_id"]: row for row in rows if row.get("event_id")}
    rows = sorted(deduped.values(), key=lambda r: (r["event_time"], r["event_id"]))

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} events to {OUTPUT_PATH}.", flush=True)


if __name__ == "__main__":
    main()
