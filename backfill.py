#!/usr/bin/env python3
"""One-off historical backfill for the USGS earthquakes table.

Walks a date range (default 2025-01-01 -> now) one month at a time, fetching
each window from the USGS API and upserting into the same `earthquakes` table
used by the hourly sync. Because writes are upserts on `event_id`, this is safe
to re-run and overlaps harmlessly with the hourly job.

The USGS query endpoint caps each request at 20,000 results, so before fetching
a window we check its count; any window that approaches the cap is split in half
recursively until each piece is safely under the limit (handles unusually dense
periods automatically).

Environment variables:
    SUPABASE_URL          (required)
    SUPABASE_SECRET_KEY   (required)
    START_DATE            optional, YYYY-MM-DD (default 2025-01-01)
    END_DATE              optional, YYYY-MM-DD (default: now)
    MIN_MAGNITUDE         optional float (default 2.5)
"""

import os
import time
from datetime import datetime, timezone

from sync_earthquakes import (
    MIN_MAGNITUDE,
    TABLE,
    count_events,
    fetch_features,
    get_client,
    transform,
    upsert_rows,
)

# Stay comfortably below the USGS 20,000-per-query hard cap.
SAFETY_LIMIT = 18000


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


def process_window(client, start, end, min_magnitude, stats):
    """Count, (optionally split,) fetch and upsert a single time window."""
    n = count_events(start, end, min_magnitude)
    if n == 0:
        print(f"  {start.date()} -> {end.date()}: 0 events, skipping.", flush=True)
        return
    if n > SAFETY_LIMIT:
        mid = start + (end - start) / 2
        print(
            f"  {start.date()} -> {end.date()}: {n} events > {SAFETY_LIMIT}, "
            f"splitting at {mid.date()}...",
            flush=True,
        )
        process_window(client, start, mid, min_magnitude, stats)
        process_window(client, mid, end, min_magnitude, stats)
        return

    features = fetch_features(start, end, min_magnitude)
    rows = [transform(f) for f in features]
    upserted = upsert_rows(client, rows, verbose=False)
    stats["total"] += upserted
    print(
        f"  {start.date()} -> {end.date()}: {n} events, upserted {upserted}. "
        f"Running total: {stats['total']}",
        flush=True,
    )
    # Be polite to the USGS API between windows.
    time.sleep(0.5)


def main():
    start_str = os.environ.get("START_DATE", "2025-01-01")
    end_str = os.environ.get("END_DATE")
    min_magnitude = float(os.environ.get("MIN_MAGNITUDE", MIN_MAGNITUDE))

    start = datetime.fromisoformat(start_str).replace(tzinfo=timezone.utc)
    end = (
        datetime.fromisoformat(end_str).replace(tzinfo=timezone.utc)
        if end_str
        else datetime.now(timezone.utc)
    )

    client = get_client()
    print(
        f"Backfilling USGS earthquakes {start.date()} -> {end.date()} "
        f"(min magnitude {min_magnitude})...",
        flush=True,
    )

    stats = {"total": 0}
    for w_start, w_end in month_windows(start, end):
        process_window(client, w_start, w_end, min_magnitude, stats)

    print(
        f"Done. Backfill upserted {stats['total']} earthquake records "
        f"into '{TABLE}'.",
        flush=True,
    )


if __name__ == "__main__":
    main()
