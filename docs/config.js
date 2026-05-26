// Smartii landing page config.
// Fill these in to wire up Pro signups + donations. Leave blank for a "marketing only" build.
//
// Where to find each value:
//   SUPABASE_URL                  Project Settings → API → Project URL
//   SUPABASE_ANON_KEY             Project Settings → API → anon public key
//   STRIPE_PUBLISHABLE_KEY        Stripe Dashboard → Developers → API keys → publishable
//   STRIPE_PRICING_TABLE_ID       Stripe Dashboard → Pricing Tables → ID (looks like prctbl_xxx)
//   STRIPE_DONATION_LINK          Stripe → Payment Links → a one-time link with "let customer
//                                 choose amount" enabled. Append `?prefilled_amount=AMOUNT` per click.
//   STRIPE_PORTAL_LINK            Stripe → Customer Portal → published link (cus-mgmt page)

window.SMARTII_CONFIG = {
  SUPABASE_URL: "",
  SUPABASE_ANON_KEY: "",
  STRIPE_PUBLISHABLE_KEY: "",
  STRIPE_PRICING_TABLE_ID: "",
  STRIPE_DONATION_LINK: "",
  STRIPE_PORTAL_LINK: ""
};
