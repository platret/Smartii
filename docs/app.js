// Smartii landing page logic.
// Three responsibilities:
//   1. Stripe — mount the Pricing Table, wire donation buttons, hide if unconfigured.
//   2. Supabase auth — magic-link sign-in via the auth REST API. Session lives in localStorage.
//   3. Entitlement display — show plan + portal link once the user is signed in.

const C = window.SMARTII_CONFIG || {};

// --- Stripe Pricing Table -------------------------------------------------

(function mountPricingTable() {
  const mount = document.getElementById("stripeTable");
  const fallback = document.getElementById("pricingFallback");
  if (!mount) return;
  if (!C.STRIPE_PRICING_TABLE_ID || !C.STRIPE_PUBLISHABLE_KEY) {
    mount.hidden = true;
    if (fallback) fallback.hidden = false;
    return;
  }
  mount.setAttribute("pricing-table-id", C.STRIPE_PRICING_TABLE_ID);
  mount.setAttribute("publishable-key", C.STRIPE_PUBLISHABLE_KEY);
  // Forward signed-in email so Stripe Checkout pre-fills.
  const session = loadSession();
  const email = session?.user?.email;
  if (email) {
    mount.setAttribute("customer-email", email);
    mount.setAttribute("client-reference-id", session.user.id);
  }
})();

// --- Donations ------------------------------------------------------------

(function wireDonations() {
  const container = document.getElementById("donateAmounts");
  const fallback = document.getElementById("donateFallback");
  if (!container) return;
  if (!C.STRIPE_DONATION_LINK) {
    container.hidden = true;
    if (fallback) fallback.hidden = false;
    return;
  }
  container.querySelectorAll("button[data-amount]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const cents = Number(btn.dataset.amount) * 100;
      const url = new URL(C.STRIPE_DONATION_LINK);
      // Stripe Payment Links read `prefilled_amount` for "customer chooses amount" links.
      url.searchParams.set("prefilled_amount", String(cents));
      window.open(url.toString(), "_blank", "noopener");
    });
  });
})();

// --- Supabase auth (REST, no SDK to keep this page tiny) ------------------

const SESSION_KEY = "smartii_session";

function loadSession() {
  try {
    const s = JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
    if (!s || !s.access_token) return null;
    return s;
  } catch {
    return null;
  }
}

function saveSession(s) {
  if (s) localStorage.setItem(SESSION_KEY, JSON.stringify(s));
  else localStorage.removeItem(SESSION_KEY);
}

async function refreshSession(s) {
  if (!C.SUPABASE_URL || !C.SUPABASE_ANON_KEY || !s?.refresh_token) return null;
  const res = await fetch(`${C.SUPABASE_URL}/auth/v1/token?grant_type=refresh_token`, {
    method: "POST",
    headers: { "Content-Type": "application/json", apikey: C.SUPABASE_ANON_KEY },
    body: JSON.stringify({ refresh_token: s.refresh_token })
  });
  if (!res.ok) return null;
  const next = await res.json();
  const merged = {
    access_token: next.access_token,
    refresh_token: next.refresh_token || s.refresh_token,
    expires_at: Math.floor(Date.now() / 1000) + (next.expires_in || 3600),
    user: next.user || s.user
  };
  saveSession(merged);
  return merged;
}

async function getValidSession() {
  let s = loadSession();
  if (!s) return null;
  if (s.expires_at && s.expires_at - Math.floor(Date.now() / 1000) < 60) {
    s = await refreshSession(s);
  }
  return s;
}

// Magic links return as `#access_token=...&refresh_token=...&...` on this page.
// Pluck them out of the hash, persist, and strip the URL.
(function consumeMagicLinkHash() {
  if (!location.hash || !location.hash.includes("access_token=")) return;
  const params = new URLSearchParams(location.hash.slice(1));
  const access = params.get("access_token");
  const refresh = params.get("refresh_token");
  const expiresIn = Number(params.get("expires_in") || 3600);
  if (!access || !refresh) return;
  // Get user info from access_token's /auth/v1/user.
  fetch(`${C.SUPABASE_URL}/auth/v1/user`, {
    headers: { apikey: C.SUPABASE_ANON_KEY, Authorization: "Bearer " + access }
  })
    .then((r) => (r.ok ? r.json() : null))
    .then((user) => {
      saveSession({
        access_token: access,
        refresh_token: refresh,
        expires_at: Math.floor(Date.now() / 1000) + expiresIn,
        user
      });
      history.replaceState(null, "", location.pathname + location.search);
      renderAccount();
    });
})();

async function fetchEntitlement(session) {
  if (!C.SUPABASE_URL || !C.SUPABASE_ANON_KEY || !session) return null;
  const res = await fetch(
    `${C.SUPABASE_URL}/rest/v1/entitlements?select=status,plan,current_period_end&user_id=eq.${session.user.id}&order=current_period_end.desc.nullslast&limit=1`,
    {
      headers: {
        apikey: C.SUPABASE_ANON_KEY,
        Authorization: "Bearer " + session.access_token,
        Accept: "application/json"
      }
    }
  );
  if (!res.ok) return null;
  const rows = await res.json();
  return rows[0] || null;
}

async function renderAccount() {
  const signedOut = document.getElementById("acctSignedOut");
  const signedIn = document.getElementById("acctSignedIn");
  if (!signedOut || !signedIn) return;
  const s = await getValidSession();
  if (!s) {
    signedOut.hidden = false;
    signedIn.hidden = true;
    return;
  }
  signedOut.hidden = true;
  signedIn.hidden = false;
  document.getElementById("acctEmailLabel").textContent = s.user?.email || "(unknown)";

  const ent = await fetchEntitlement(s);
  const label = document.getElementById("acctPlanLabel");
  if (ent && ent.status === "active") {
    label.textContent = `Pro · ${ent.plan} · renews ${
      ent.current_period_end ? new Date(ent.current_period_end).toLocaleDateString() : "auto"
    }`;
  } else {
    label.textContent = "Free plan — upgrade above to unlock Godmode.";
  }
  const portal = document.getElementById("acctPortal");
  if (C.STRIPE_PORTAL_LINK) {
    portal.href = C.STRIPE_PORTAL_LINK;
    portal.hidden = false;
  }
}

(function wireAuth() {
  const form = document.getElementById("acctSignInForm");
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("acctEmail").value.trim();
    const status = document.getElementById("acctStatus");
    if (!email) return;
    if (!C.SUPABASE_URL || !C.SUPABASE_ANON_KEY) {
      status.textContent = "Auth is not configured yet. Edit docs/config.js.";
      return;
    }
    status.textContent = "Sending…";
    const res = await fetch(`${C.SUPABASE_URL}/auth/v1/otp`, {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: C.SUPABASE_ANON_KEY },
      body: JSON.stringify({
        email,
        create_user: true,
        options: { email_redirect_to: location.origin + location.pathname }
      })
    });
    status.textContent = res.ok
      ? "Magic link sent. Check your inbox."
      : "Failed: " + (await res.text());
  });

  document.getElementById("acctSignOut")?.addEventListener("click", () => {
    saveSession(null);
    renderAccount();
  });

  renderAccount();
})();
