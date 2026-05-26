-- Smartii Pro — entitlement schema.
-- Two tables:
--   public.entitlements        — one row per user × plan, updated by the Stripe webhook
--   public.stripe_customers    — links Stripe customer_id → auth.users.id, so the webhook
--                                can look up the right user when a subscription event arrives.
--
-- Row Level Security is on for both: a user can read only their own rows. The webhook
-- runs with the service-role key so RLS is bypassed there.

create extension if not exists "pgcrypto";

create table if not exists public.stripe_customers (
  user_id uuid primary key references auth.users(id) on delete cascade,
  stripe_customer_id text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists public.entitlements (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  plan text not null,                       -- "pro_monthly", "pro_yearly", "lifetime", ...
  status text not null,                     -- "active", "canceled", "past_due", ...
  stripe_subscription_id text unique,
  stripe_customer_id text,
  current_period_end timestamptz,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists entitlements_user_idx on public.entitlements(user_id);
create index if not exists entitlements_status_idx on public.entitlements(status);

alter table public.stripe_customers enable row level security;
alter table public.entitlements      enable row level security;

create policy "users read own customer row"
  on public.stripe_customers for select
  using (auth.uid() = user_id);

create policy "users read own entitlements"
  on public.entitlements for select
  using (auth.uid() = user_id);

-- One-time donations are logged but don't gate anything.
create table if not exists public.donations (
  id uuid primary key default gen_random_uuid(),
  email text,
  amount_cents integer not null,
  currency text not null default 'usd',
  stripe_payment_intent text unique,
  created_at timestamptz not null default now()
);
