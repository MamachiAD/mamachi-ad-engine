-- Run ONCE, after supabase.sql. Adds Mamachi Ads itself to your free rotation.
-- Your table requires client_name, so every row below sets it. If Supabase ever says
-- 'null value in column "X"', copy the message and send it to me; the fix is one more column here.
alter table mamachi_products add column if not exists hashtags text;
alter table mamachi_products add column if not exists image_style text;
alter table mamachi_products add column if not exists kind text default 'book';
alter table mamachi_products add column if not exists language text default 'English';

insert into mamachi_products (client_name, product_title, destination_url, manuscript_text, hashtags, is_active, kind) values
('Mamachi Internal', 'Mamachi Ads: think outside the box, use SI for your business', 'https://mamachiad.github.io/mamachi-ad-engine/', 'Mamachi Ads makes a fresh animated ad for your book, product or service and posts it automatically on YouTube, TikTok, Instagram and more. Pay by the hour, day, week, month or year, and see your posting schedule before you pay.', '#MamachiAds #SmallBusiness #Marketing', true, 'service'),
('Mamachi Internal', 'Advertise from $2 an hour with Mamachi Ads', 'https://mamachiad.github.io/mamachi-ad-engine/#pricing', 'Try a one-hour local feed ad for $2, then scale up to more reach and more posts a day when you see your link clicks. Every post is tracked and you get an email each time.', '#Advertising #Startups #Creators', true, 'service'),
('Mamachi Internal', 'Authors: get your book seen with Mamachi Ads', 'https://mamachiad.github.io/mamachi-ad-engine/advertise.html', 'New animated ads for your book on a steady schedule, in 12 languages, with a private page showing every post and click. Your own accounts can carry the ad too.', '#SelfPublishing #Authors #BookMarketing', true, 'service'),
('Mamachi Internal', 'Local business? Put your offer on every screen', 'https://mamachiad.github.io/mamachi-ad-engine/advertise.html', 'Cafes, shops and studios: choose your reach, pick a placement and let Mamachi Ads post a fresh animated ad every day you have paid for.', '#LocalBusiness #SmallBusiness #Shoplocal', true, 'service'),
('Mamachi Internal', 'SI engine: how Mamachi automates promotion', 'https://mamachiad.github.io/mamachi-ad-engine/', 'The SI engine writes, animates and posts ads on a schedule, switches between free AI models when one runs out, and shows advertisers exactly what was posted.', '#SuperIntelligence #Automation #AI', true, 'service');
