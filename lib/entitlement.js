// Smartii Pro entitlement check.
// Talks to a Supabase project (configured in lib/config.js) over REST.
//   - Sign in: magic-link OTP delivered by Supabase Auth.
//   - Verify Pro: SELECT one row from public.entitlements WHERE user_id = auth.uid
//     AND status = 'active' AND (current_period_end IS NULL OR current_period_end > now()).
//   - Cache the result in chrome.storage.local for 6h so we don't hit the network
//     on every Godmode press.
//
// Self-hosted: edit lib/config.js to point SUPABASE_URL + SUPABASE_ANON_KEY at
// your own project. The extension fails *closed* (Pro = false) if config is
// missing — Godmode just stays locked, the rest of the extension keeps working.

const PRO_CACHE_KEY = "smartiiProCache";
const SESSION_KEY = "smartiiSession";
const PRO_CACHE_TTL_MS = 6 * 60 * 60 * 1000;

function getConfig() {
  const c = self.SMARTII_CONFIG || {};
  return {
    url: c.SUPABASE_URL || "",
    anon: c.SUPABASE_ANON_KEY || "",
    siteUrl: c.SITE_URL || "https://platret.github.io/Smartii/"
  };
}

async function loadSession() {
  const { [SESSION_KEY]: s } = await chrome.storage.local.get(SESSION_KEY);
  return s || null;
}

async function saveSession(session) {
  if (!session) {
    await chrome.storage.local.remove(SESSION_KEY);
    return;
  }
  await chrome.storage.local.set({ [SESSION_KEY]: session });
}

async function refreshSession(session) {
  const { url, anon } = getConfig();
  if (!url || !anon || !session?.refresh_token) return null;
  const res = await fetch(`${url}/auth/v1/token?grant_type=refresh_token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: anon
    },
    body: JSON.stringify({ refresh_token: session.refresh_token })
  });
  if (!res.ok) return null;
  const next = await res.json();
  const merged = {
    access_token: next.access_token,
    refresh_token: next.refresh_token || session.refresh_token,
    expires_at: Math.floor(Date.now() / 1000) + (next.expires_in || 3600),
    user: next.user || session.user
  };
  await saveSession(merged);
  return merged;
}

async function ensureFreshSession() {
  const s = await loadSession();
  if (!s) return null;
  const now = Math.floor(Date.now() / 1000);
  if (s.expires_at && s.expires_at - now < 60) {
    return await refreshSession(s);
  }
  return s;
}

// Send a magic-link email. Supabase delivers a code; user pastes it back here.
// We use the "send-otp" endpoint so the same email works for sign-up and sign-in.
async function signIn(email) {
  const { url, anon, siteUrl } = getConfig();
  if (!url || !anon) {
    return { ok: false, error: "Smartii Pro is not configured in this build." };
  }
  const res = await fetch(`${url}/auth/v1/otp`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: anon
    },
    body: JSON.stringify({
      email,
      create_user: true,
      options: { email_redirect_to: siteUrl }
    })
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      detail = (await res.json())?.msg || detail;
    } catch (_) {}
    return { ok: false, error: detail };
  }
  return { ok: true, message: "Magic link sent to " + email + ". Check your inbox." };
}

async function signOut() {
  await chrome.storage.local.remove([SESSION_KEY, PRO_CACHE_KEY]);
}

// Read the entitlements row through Supabase's REST (PostgREST).
// RLS policy must allow `auth.uid() = user_id`.
async function fetchEntitlement(session) {
  const { url, anon } = getConfig();
  const res = await fetch(
    `${url}/rest/v1/entitlements?select=status,plan,current_period_end&user_id=eq.${session.user.id}&order=current_period_end.desc.nullslast&limit=1`,
    {
      headers: {
        apikey: anon,
        Authorization: "Bearer " + session.access_token,
        Accept: "application/json"
      }
    }
  );
  if (!res.ok) throw new Error("entitlement HTTP " + res.status);
  const rows = await res.json();
  return rows[0] || null;
}

async function checkPro({ force } = {}) {
  // Local unlock — for self-hosters and developers running an unpacked build
  // with no Supabase backend configured. Set from the options page
  // ("Unlock Godmode locally"). Wins over everything so Godmode works on any
  // Chromium browser without a server. Stored in storage.local (per-device),
  // never synced, never shipped on.
  const { smartiiProOverride } = await chrome.storage.local.get("smartiiProOverride");
  if (smartiiProOverride) return { active: true, plan: "self-host" };

  const { url, anon } = getConfig();
  if (!url || !anon) {
    return { active: false, reason: "unconfigured" };
  }

  if (!force) {
    const { [PRO_CACHE_KEY]: cached } = await chrome.storage.local.get(PRO_CACHE_KEY);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.value;
    }
  }

  const session = await ensureFreshSession();
  if (!session) return { active: false, reason: "signed_out" };

  let value = { active: false, reason: "no_entitlement" };
  try {
    const row = await fetchEntitlement(session);
    if (row && row.status === "active") {
      const stillValid =
        !row.current_period_end ||
        new Date(row.current_period_end).getTime() > Date.now();
      if (stillValid) {
        value = { active: true, plan: row.plan || "pro" };
      }
    }
  } catch (err) {
    value = { active: false, reason: "network_error", error: String(err?.message || err) };
  }

  await chrome.storage.local.set({
    [PRO_CACHE_KEY]: { value, expiresAt: Date.now() + PRO_CACHE_TTL_MS }
  });
  return value;
}

self.smartiiCheckPro = checkPro;
self.smartiiSignIn = signIn;
self.smartiiSignOut = signOut;
self.smartiiSession = ensureFreshSession;
