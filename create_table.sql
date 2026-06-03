-- Supabase / Postgres table for USGS earthquake data.
-- Run once against your project (e.g. via the Supabase SQL editor or CLI).
-- The pipeline upserts on event_id, so this script is safe to re-run.

create table if not exists public.earthquakes (
    event_id      text primary key,           -- USGS event id, e.g. "us7000n7p6"
    title         text,
    magnitude     real,
    mag_type      text,
    depth_km      real,
    latitude      double precision,
    longitude     double precision,
    place         text,
    event_time    timestamptz,                -- USGS properties.time
    updated_time  timestamptz,                -- USGS properties.updated
    felt          integer,
    cdi           real,
    mmi           real,
    alert         text,
    tsunami       integer,
    significance  integer,                     -- USGS properties.sig
    event_type    text,                        -- USGS properties.type
    status        text,
    net           text,
    url           text,
    fetched_at    timestamptz default now()
);

create index if not exists idx_earthquakes_event_time on public.earthquakes (event_time desc);
create index if not exists idx_earthquakes_magnitude  on public.earthquakes (magnitude desc);
create index if not exists idx_earthquakes_lat_lon    on public.earthquakes (latitude, longitude);
create index if not exists idx_earthquakes_alert      on public.earthquakes (alert);
