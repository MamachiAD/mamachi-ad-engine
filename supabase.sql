-- Run once in Supabase > SQL Editor. Safe to run again.
create extension if not exists pgcrypto;

create table if not exists mamachi_orders (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  status text default 'pending_payment',   -- pending_payment | paid_review | approved | rejected | completed | payment_mismatch
  vendor_name text, vendor_email text, manage_token text,
  product_title text, destination_url text, summary text, language text default 'English', hashtags text,
  unit text, qty int, geo_level text, geo_region text, placement text,
  hours numeric, posts_per_day int, posts_total int, posts_remaining int, ad_hours text,
  variation text default 'unique',          -- unique = different text per platform, same = identical everywhere
  renew_reminder boolean default false, renewal_sent boolean default false,
  own_social boolean default false, social_activated boolean default false,
  amount numeric, currency text, paypal_order_id text, paypal_capture_id text, paid_at timestamptz,
  starts_at timestamptz, ends_at timestamptz, last_posted_at timestamptz, day_key text, day_count int default 0,
  refunded_at timestamptz
);
create table if not exists mamachi_ad_posts (
  id bigint generated always as identity primary key,
  order_id uuid references mamachi_orders(id) on delete cascade,
  posted_at timestamptz default now(), platforms text, short_url text, shortio_id text
);
create table if not exists mamachi_messages (id bigint generated always as identity primary key, created_at timestamptz default now(), name text, email text, message text);
create table if not exists mamachi_leads (
  id bigint generated always as identity primary key, created_at timestamptz default now(),
  source text, post_url text unique, author text, text text, score int, need text, draft_reply text, status text default 'new'   -- new | approved | sent | skipped | won
);

-- These tables hold private data. Row-level security ON with no public policies = only your service_role key can read or write them.
alter table mamachi_orders enable row level security;
alter table mamachi_ad_posts enable row level security;
alter table mamachi_messages enable row level security;
alter table mamachi_leads enable row level security;

-- Your own products AND services (free, unlimited). Add as many rows as you like in Table Editor.
alter table mamachi_products add column if not exists hashtags text;                      -- the engine reads these when present
alter table mamachi_products add column if not exists image_style text;
alter table mamachi_products add column if not exists kind text default 'book';       -- book | service | product
alter table mamachi_products add column if not exists language text default 'English';

-- Added for go-live: small key-value store used by the worker (so no Cloudflare KV is needed), and the location / learning columns.
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
