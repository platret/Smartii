# Smartii backend (Supabase)

This folder holds everything needed to run the **Smartii Pro** entitlement backend.
It is optional — the extension keeps working in BYO-API-key mode without it. Pro
features (Godmode + cloud sync) require a Supabase project and a Stripe account.

## What's here

- `migrations/20260526000000_init.sql` — `entitlements`, `stripe_customers`, `donations`
  tables + Row Level Security policies.
- `functions/stripe-webhook/` — Deno edge function that turns Stripe events into
  rows in `entitlements`.

## One-time setup

```bash
# 1. Create the project
npx supabase login
npx supabase link --project-ref <your-project-ref>

# 2. Apply schema
npx supabase db push

# 3. Configure Stripe + Supabase secrets
npx supabase secrets set \
  STRIPE_SECRET_KEY=sk_live_xxx \
  STRIPE_WEBHOOK_SECRET=whsec_xxx

# 4. Deploy the webhook (no JWT — Stripe doesn't send one)
npx supabase functions deploy stripe-webhook --no-verify-jwt
```

Stripe → **Developers → Webhooks → Add endpoint**

- URL: `https://<your-project-ref>.supabase.co/functions/v1/stripe-webhook`
- Events: `checkout.session.completed`, `customer.subscription.created`,
  `customer.subscription.updated`, `customer.subscription.deleted`

Then fill in `lib/config.js` (extension) and `docs/config.js` (landing page) with
your `SUPABASE_URL` + `SUPABASE_ANON_KEY` and the Stripe Pricing Table /
Payment Link IDs.
