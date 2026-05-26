// Smartii Stripe webhook (Supabase Edge Function, Deno runtime).
//
// Listens to Stripe and writes entitlement state into public.entitlements.
// Handles:
//   - checkout.session.completed         → resolve customer ↔ user, mark Pro active
//   - customer.subscription.updated      → refresh status + current_period_end
//   - customer.subscription.deleted      → mark canceled
//   - payment_intent.succeeded (one-time)→ insert into public.donations
//
// Deploy:
//   supabase functions deploy stripe-webhook --no-verify-jwt
// Set secrets:
//   supabase secrets set STRIPE_SECRET_KEY=sk_live_...
//   supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_...
// Then in Stripe Dashboard → Webhooks, add:
//   <project>.supabase.co/functions/v1/stripe-webhook
//
// Stripe verifies the signature with STRIPE_WEBHOOK_SECRET. We use the service-role
// key to bypass RLS for writes.

import Stripe from "https://esm.sh/stripe@14.21.0?target=deno";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY")!, {
  apiVersion: "2024-06-20",
  httpClient: Stripe.createFetchHttpClient()
});

const webhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET")!;

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  { auth: { persistSession: false } }
);

async function findUserByCustomer(customerId: string): Promise<string | null> {
  const { data } = await supabase
    .from("stripe_customers")
    .select("user_id")
    .eq("stripe_customer_id", customerId)
    .maybeSingle();
  if (data?.user_id) return data.user_id;

  // Fall back to the email on the Stripe customer → match an auth user.
  const customer = await stripe.customers.retrieve(customerId);
  if (!customer || customer.deleted) return null;
  const email = (customer as Stripe.Customer).email;
  if (!email) return null;

  const { data: users } = await supabase.auth.admin.listUsers();
  const user = users.users.find((u) => u.email?.toLowerCase() === email.toLowerCase());
  if (!user) return null;

  await supabase.from("stripe_customers").upsert({
    user_id: user.id,
    stripe_customer_id: customerId
  });
  return user.id;
}

async function upsertEntitlement(sub: Stripe.Subscription, userId: string) {
  const priceId = sub.items.data[0]?.price.id || "";
  const plan = sub.items.data[0]?.price.lookup_key || priceId || "pro";
  await supabase.from("entitlements").upsert(
    {
      user_id: userId,
      plan,
      status: sub.status,
      stripe_subscription_id: sub.id,
      stripe_customer_id: typeof sub.customer === "string" ? sub.customer : sub.customer.id,
      current_period_end: new Date(sub.current_period_end * 1000).toISOString(),
      updated_at: new Date().toISOString()
    },
    { onConflict: "stripe_subscription_id" }
  );
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return new Response("method not allowed", { status: 405 });

  const sig = req.headers.get("stripe-signature");
  if (!sig) return new Response("no signature", { status: 400 });

  const payload = await req.text();
  let event: Stripe.Event;
  try {
    event = await stripe.webhooks.constructEventAsync(payload, sig, webhookSecret);
  } catch (err) {
    return new Response("invalid signature: " + (err as Error).message, { status: 400 });
  }

  try {
    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session;
        if (session.mode === "subscription" && session.customer && session.subscription) {
          const userId = await findUserByCustomer(session.customer as string);
          if (userId) {
            const sub = await stripe.subscriptions.retrieve(session.subscription as string);
            await upsertEntitlement(sub, userId);
          }
        }
        if (session.mode === "payment") {
          // One-time donation.
          await supabase.from("donations").insert({
            email: session.customer_details?.email ?? null,
            amount_cents: session.amount_total ?? 0,
            currency: session.currency ?? "usd",
            stripe_payment_intent: session.payment_intent as string
          });
        }
        break;
      }
      case "customer.subscription.updated":
      case "customer.subscription.created": {
        const sub = event.data.object as Stripe.Subscription;
        const userId = await findUserByCustomer(sub.customer as string);
        if (userId) await upsertEntitlement(sub, userId);
        break;
      }
      case "customer.subscription.deleted": {
        const sub = event.data.object as Stripe.Subscription;
        await supabase
          .from("entitlements")
          .update({ status: "canceled", updated_at: new Date().toISOString() })
          .eq("stripe_subscription_id", sub.id);
        break;
      }
    }
    return new Response("ok", { status: 200 });
  } catch (err) {
    console.error(err);
    return new Response("handler error: " + (err as Error).message, { status: 500 });
  }
});
