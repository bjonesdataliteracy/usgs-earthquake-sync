#!/usr/bin/env python3
"""Sync recent USGS earthquake data into a Supabase Postgres table.

Fetches the last 30 days of earthquakes (magnitude >= 2.5) from the USGS
FDSN event API as GeoJSON, flattens each feature into a row, and upserts the
rows into the `earthquakes` table on Supabase. Upserting on `event_id` means
new events are inserted while revised events (updated magnitude, alert, etc.)
overwrite the existing row.

The fetch/transform/upsert helpers here are also imported by `backfill.py`.

Environment variables (required):
    SUPABASE_URL                 e.g. https://<ref>.supabase.co
    SUPABASE_SECRET_KEY          Supabase secret / service_role key (bypasses RLS)
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import requests
from supabase import create_client

USGS_QUERY = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_COUNT = "https://earthquake.usgs.gov/fdsnws/event/1/count"
MIN_MAGNITUDE = 2.5
DAYS_BACK = 30
RESULT_LIMIT = 20000
BATCH_SIZE = 500
TABLE = "earthquakes"
HEADERS = {"User-Agent": "usgs-earthquake-sync/1.0 (github actions)"}


def epoch_ms_to_iso(value):
    """Convert USGS epoch-milliseconds timestamps to an ISO 8601 UTC string."""
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def get_client():
    """Build a Supabase client from environment variables (exits if missing)."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SECRET_KEY")
    if not url or not key:
        print(
            "ERROR: SUPABASE_URL and SUPABASE_SECRET_KEY must be set.",
            file=sys.stderr,
        )
        sys.exit(1)
    return create_client(url, key)


def _usgs_params(starttime, endtime, min_magnitude):
    return {
        "starttime": starttime.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": endtime.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": min_magnitude,
    }


def count_events(starttime, endtime, min_magnitude=MIN_MAGNITUDE):
    """Return how many events match a window, via the USGS count endpoint."""
    params = _usgs_params(starttime, endtime, min_magnitude)
    params["format"] = "text"
    resp = requests.get(USGS_COUNT, params=params, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return int(resp.text.strip())


def fetch_features(starttime, endtime, min_magnitude=MIN_MAGNITUDE, limit=RESULT_LIMIT):
    """Query the USGS API for a time window and return the GeoJSON features."""
    params = _usgs_params(starttime, endtime, min_magnitude)
    params["format"] = "geojson"
    params["limit"] = limit
    resp = requests.get(USGS_QUERY, params=params, headers=HEADERS, timeout=120)
    resp.raise_for_status()
    return resp.json().get("features", [])


def transform(feature):
    """Flatten one GeoJSON feature into a row dict for the earthquakes table."""
    props = feature.get("properties") or {}
    coords = (feature.get("geometry") or {}).get("coordinates") or []
    # GeoJSON coordinates are [longitude, latitude, depth_km].
    longitude = coords[0] if len(coords) > 0 else None
    latitude = coords[1] if len(coords) > 1 else None
    depth_km = coords[2] if len(coords) > 2 else None
    return {
        "event_id": feature.get("id"),
        "title": props.get("title"),
        "magnitude": props.get("mag"),
        "mag_type": props.get("magType"),
        "depth_km": depth_km,
        "latitude": latitude,
        "longitude": longitude,
        "place": props.get("place"),
        "event_time": epoch_ms_to_iso(props.get("time")),
        "updated_time": epoch_ms_to_iso(props.get("updated")),
        "felt": props.get("felt"),
        "cdi": props.get("cdi"),
        "mmi": props.get("mmi"),
        "alert": props.get("alert"),
        "tsunami": props.get("tsunami"),
        "significance": props.get("sig"),
        "event_type": props.get("type"),
        "status": props.get("status"),
        "net": props.get("net"),
        "url": props.get("url"),
    }


def upsert_rows(client, rows, batch_size=BATCH_SIZE, verbose=True):
    """Upsert rows into the earthquakes table in batches; returns count written.

    De-duplicates on event_id within the call so a single batch can't hit a
    duplicate-key conflict. Existing event_ids are overwritten (ON CONFLICT).
    """
    deduped = {row["event_id"]: row for row in rows if row.get("event_id")}
    rows = list(deduped.values())
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        client.table(TABLE).upsert(batch, on_conflict="event_id").execute()
        total += len(batch)
        if verbose:
            print(f"  Upserted {total}/{len(rows)} rows...", flush=True)
    return total


def main():
    client = get_client()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=DAYS_BACK)
    print(
        f"Fetching USGS earthquakes {start.date()} -> {end.date()} "
        f"(min magnitude {MIN_MAGNITUDE}, limit {RESULT_LIMIT})...",
        flush=True,
    )
    features = fetch_features(start, end)
    print(f"USGS returned {len(features)} features.", flush=True)
    rows = [transform(f) for f in features]
    print(f"Prepared {len(rows)} rows for upsert.", flush=True)
    total = upsert_rows(client, rows)
    print(f"Done. Upserted {total} earthquake records into '{TABLE}'.", flush=True)


if __name__ == "__main__":
    main()
