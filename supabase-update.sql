-- Run this ONE block now (safe to run again). It adds everything new since the first SQL file.
create table if not exists mamachi_kv (key text primary key, value text, expires_at timestamptz);
alter table mamachi_kv enable row level security;

-- precise location + the advertiser's own prompt
alter table mamachi_orders add column if not exists ad_prompt text;
alter table mamachi_orders add column if not exists geo_country text;
alter table mamachi_orders add column if not exists geo_country_name text;
alter table mamachi_orders add column if not exists geo_areas text;
alter table mamachi_orders add column if not exists tz_offset numeric;
alter table mamachi_ad_posts add column if not exists areas text;
alter table mamachi_ad_posts add column if not exists angle text;

-- self-improvement and audience numbers
create table if not exists mamachi_learning (
  id bigint generated always as identity primary key, created_at timestamptz default now(),
  kind text, ref text, angle text, platforms text, shortio_id text, short_url text, clicks int default 0, checked_at timestamptz);
create table if not exists mamachi_settings (key text primary key, value jsonb);
alter table mamachi_learning enable row level security;
alter table mamachi_settings enable row level security;
