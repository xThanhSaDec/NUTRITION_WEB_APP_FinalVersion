-- Supabase schema for NutriDish
-- Run in Supabase SQL editor or via CLI.
-- Profiles
create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  age int not null,
  weight_kg numeric not null,
  height_cm numeric not null,
  gender text not null check (gender in ('male', 'female')),
  activity text not null default 'moderate',
  goal_weight numeric null,
  targets jsonb not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);
-- Logs for meals
create table if not exists public.food_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  meal_type text not null default 'unspecified',
  image_url text,
  food_name text,
  class_name text,
  confidence numeric,
  servings numeric default 1,
  calories numeric default 0,
  protein numeric default 0,
  fat numeric default 0,
  carbs numeric default 0,
  fiber numeric default 0,
  created_at timestamp with time zone default now()
);
-- Daily summaries and streak tracking
create table if not exists public.daily_summaries (
  user_id uuid not null references auth.users(id) on delete cascade,
  day date not null,
  totals jsonb not null,
  complete boolean not null default false,
  updated_at timestamp with time zone default now(),
  primary key (user_id, day)
);
-- Enable Row Level Security
alter table public.profiles enable row level security;
alter table public.food_logs enable row level security;
alter table public.daily_summaries enable row level security;
-- RLS: users can read/write their own rows
create policy if not exists "Profiles own" on public.profiles for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy if not exists "Food logs own" on public.food_logs for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy if not exists "Daily summaries own" on public.daily_summaries for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
-- Storage bucket (create from UI or CLI). Name: food-uploads (public)
-- Optional: App-level Users table (public) referencing auth.users
create table if not exists public.users (
  user_id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  display_name text,
  url_image text,
  created_at timestamp with time zone default now()
);
-- Ensure url_image exists on legacy deployments where users table predates this column
alter table public.users
add column if not exists url_image text;
alter table public.users enable row level security;
create policy if not exists "Users own" on public.users for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
-- Nutrition master table (for server-side nutrition lookup)
create table if not exists public.nutrition (
  dish_name text primary key,
  calories numeric,
  protein numeric,
  fat numeric,
  carbs numeric,
  fiber numeric,
  serving text,
  dataset_source text
);
alter table public.nutrition enable row level security;
-- Allow read to all authenticated users (or make it anon if desired)
create policy if not exists "Nutrition read" on public.nutrition for
select using (true);
-- Storage policies for avatar/meal uploads in bucket 'food-uploads'
-- Note: Create the bucket in Supabase Storage UI named exactly 'food-uploads'.
-- Public read (optional): allow anyone to view files in this bucket
create policy if not exists "storage public read food-uploads" on storage.objects for
select using (bucket_id = 'food-uploads');
-- Authenticated users can upload to this bucket
create policy if not exists "storage authenticated upload food-uploads" on storage.objects for
insert to authenticated with check (bucket_id = 'food-uploads');
-- Authenticated users can update/delete their own objects in this bucket
create policy if not exists "storage update own food-uploads" on storage.objects for
update to authenticated using (
    bucket_id = 'food-uploads'
    and auth.uid() = owner
  ) with check (
    bucket_id = 'food-uploads'
    and auth.uid() = owner
  );
create policy if not exists "storage delete own food-uploads" on storage.objects for delete to authenticated using (
  bucket_id = 'food-uploads'
  and auth.uid() = owner
);
-- Force PostgREST to reload schema cache so new columns become visible immediately
notify pgrst,
'reload schema';
-- Migration safety: add goal_weight to existing deployments if missing
alter table public.profiles
add column if not exists goal_weight numeric null;