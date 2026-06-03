# usgs-earthquake-sync

Hourly data pipeline that pulls live [USGS earthquake data](https://earthquake.usgs.gov/fdsnws/event/1/)
into a [Supabase](https://supabase.com) Postgres database via GitHub Actions.

Built to power live-data demos (e.g. analytics walkthroughs in
[Hex](https://hex.tech)) where the underlying table needs to stay current
without manual intervention.

## How it works

1. A GitHub Actions workflow (`.github/workflows/sync.yml`) runs every hour on a
   cron schedule (and can be triggered manually via **workflow_dispatch**).
2. `sync_earthquakes.py` queries the USGS FDSN event API for the **last 30 days**
   of earthquakes with **magnitude ≥ 2.5** (GeoJSON, up to 20,000 events).
3. Each GeoJSON feature is flattened into a row. Epoch-millisecond timestamps
   (`time`, `updated`) are converted to ISO 8601 / `timestamptz`, and
   `geometry.coordinates` (`[longitude, latitude, depth_km]`) is split into
   columns.
4. Rows are **upserted** into the `earthquakes` table in batches of 500 using
   `ON CONFLICT (event_id)`. New events are inserted; revised events (updated
   magnitude, alert level, etc.) overwrite the existing row.

## Files

| File | Purpose |
| --- | --- |
| `create_table.sql` | Table definition + indexes for the `earthquakes` table |
| `sync_earthquakes.py` | Fetch → transform → upsert script |
| `requirements.txt` | Python dependencies (`requests`, `supabase`) |
| `.github/workflows/sync.yml` | Hourly GitHub Actions workflow |

## Setup

### 1. Create the table

Run `create_table.sql` against your Supabase project (Supabase SQL editor, or
`psql`/Supabase CLI). It is idempotent and safe to re-run.

### 2. Configure repository secrets

In **Settings → Secrets and variables → Actions**, add:

| Secret | Value |
| --- | --- |
| `SUPABASE_URL` | `https://<project-ref>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Project **service role** key (Settings → API) |

The service role key bypasses Row Level Security so the workflow can write. It is
only ever stored as a GitHub Actions secret — never commit it to the repo.

### 3. Run it

Trigger the workflow manually from the **Actions** tab (**Run workflow**), or wait
for the next hourly run. To run locally instead:

```bash
pip install -r requirements.txt
export SUPABASE_URL="https://<project-ref>.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<service-role-key>"
python sync_earthquakes.py
```

## Schema

`earthquakes`, keyed on `event_id` (the USGS event id, e.g. `us7000n7p6`):

`title`, `magnitude`, `mag_type`, `depth_km`, `latitude`, `longitude`, `place`,
`event_time`, `updated_time`, `felt`, `cdi`, `mmi`, `alert`, `tsunami`,
`significance`, `event_type`, `status`, `net`, `url`, `fetched_at`.

Indexed on `event_time DESC`, `magnitude DESC`, `(latitude, longitude)`, and `alert`.

## Data source & license

Data from the U.S. Geological Survey Earthquake Hazards Program. USGS data are in
the **public domain** (U.S. government work) — no licensing restrictions.
