#!/usr/bin/env python3
"""Sync recent USGS earthquake data into a Supabase Postgres table.

Fetches the last 30 days of earthquakes (magnitude >= 2.5) from the USGS
FDSN event API as GeoJSON, flattens each feature into a row, and upserts the
rows into the `earthquakes` table on Supabase. Upserting on `event_id` means
new events are inserted while revised events (updated magnitude, alert, etc.)
overwrite the existing row.

Environment variables (required):
    SUPABASE_URL                 e.g. https://<ref>.supabase.co
    SUPABASE_SERVICE_ROLE_KEY    service role key (bypasses RLS)
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import requests
from supabase import create_client

USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
MIN_MAGNITUDE = 2.5
DAYS_BACK = 30
RESULT_LIMIT = 20000
BATCH_SIZE = 500
TABLE = "earthquakes"


def epoch_ms_to_iso(value):
    """Convert USGS epoch-milliseconds timestamps to an ISO 8601 UTC string."""
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def fetch_earthquakes():
    """Query the USGS API and return the list of GeoJSON features."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=DAYS_BACK)
    params = {
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": MIN_MAGNITUDE,
        "limit": RESULT_LIMIT,
    }
    print(
        f"Fetching USGS earthquakes {start.date()} -> {end.date()} "
        f"(min magnitude {MIN_MAGNITUDE}, limit {RESULT_LIMIT})...",
        flush=True,
    )
    resp = requests.get(
        USGS_API,
        params=params,
        headers={"User-Agent": "usgs-earthquake-sync/1.0 (github actions)"},
        timeout=120,
    )
    resp.raise_for_status()
    features = resp.json().get("features", [])
    print(f"USGS returned {len(features)} features.", flush=True)
    return features


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


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print(
            "ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = create_client(url, key)

    features = fetch_earthquakes()
    rows = [transform(f) for f in features if f.get("id")]

    # USGS can occasionally return the same id twice; keep the last occurrence
    # so the batch upsert doesn't hit a duplicate-key conflict within one call.
    deduped = {row["event_id"]: row for row in rows}
    rows = list(deduped.values())
    print(f"Prepared {len(rows)} unique rows for upsert.", flush=True)

    total = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        client.table(TABLE).upsert(batch, on_conflict="event_id").execute()
        total += len(batch)
        print(f"  Upserted {total}/{len(rows)} rows...", flush=True)

    print(f"Done. Upserted {total} earthquake records into '{TABLE}'.", flush=True)


if __name__ == "__main__":
    main()
