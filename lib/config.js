// Smartii build-time config.
// Fill these in to enable Smartii Pro (Godmode + cloud sync).
// Leaving them blank keeps the extension fully usable in BYO-API-key mode —
// only Pro features fail closed.
//
// Where to find these values:
//   SUPABASE_URL       → Project Settings → API → Project URL
//   SUPABASE_ANON_KEY  → Project Settings → API → anon public key (safe to ship)
//   SITE_URL           → URL of your GitHub Pages site, used as the magic-link
//                        redirect target after sign-in.
//
// Loaded by both background.js (importScripts) and options.html (<script>).

const SMARTII_CONFIG = {
  SUPABASE_URL: "",
  SUPABASE_ANON_KEY: "",
  SITE_URL: "https://platret.github.io/Smartii/"
};

if (typeof self !== "undefined") self.SMARTII_CONFIG = SMARTII_CONFIG;
if (typeof window !== "undefined") window.SMARTII_CONFIG = SMARTII_CONFIG;
