// Smartii update checker.
// Polls the GitHub Releases API for the newest published version and compares
// it to the running manifest version. Runs on an alarm every 30 minutes and
// on demand (the "Check now" button in options).
//
// NOTE: Chrome cannot auto-INSTALL an unpacked / Load-unpacked extension — that
// is a browser security limit, not something an extension can work around. So
// "auto-update" here means: detect a newer release, badge the toolbar icon, and
// hand the user a one-click link to the latest release. Packed CRX builds with
// an `update_url` are the only path to silent installs.

const SMARTII_REPO = "platret/Smartii";
const UPDATE_CACHE_KEY = "smartiiUpdate";
const UPDATE_ALARM = "smartii-update-check";
const UPDATE_PERIOD_MIN = 30;

// Numeric dot-version compare. Returns 1 if a>b, -1 if a<b, 0 if equal.
function cmpVersions(a, b) {
  const pa = String(a).split(".").map((n) => parseInt(n, 10) || 0);
  const pb = String(b).split(".").map((n) => parseInt(n, 10) || 0);
  const len = Math.max(pa.length, pb.length);
  for (let i = 0; i < len; i++) {
    const d = (pa[i] || 0) - (pb[i] || 0);
    if (d !== 0) return d > 0 ? 1 : -1;
  }
  return 0;
}

function setUpdateBadge(on) {
  try {
    chrome.action.setBadgeText({ text: on ? "↑" : "" });
    if (on) chrome.action.setBadgeBackgroundColor({ color: "#7C5CFF" });
  } catch (_) {
    // setBadge* can throw on some restricted contexts — non-fatal.
  }
}

async function checkForUpdate({ force } = {}) {
  const current = chrome.runtime.getManifest().version;
  try {
    const res = await fetch(
      `https://api.github.com/repos/${SMARTII_REPO}/releases/latest`,
      {
        headers: { Accept: "application/vnd.github+json" },
        cache: force ? "no-store" : "default"
      }
    );
    if (!res.ok) throw new Error("GitHub HTTP " + res.status);
    const rel = await res.json();
    const latest = (rel.tag_name || "").replace(/^v/i, "");
    const available = !!latest && cmpVersions(latest, current) > 0;
    const info = {
      current,
      latest: latest || current,
      available,
      url: rel.html_url || `https://github.com/${SMARTII_REPO}/releases/latest`,
      checkedAt: Date.now()
    };
    await chrome.storage.local.set({ [UPDATE_CACHE_KEY]: info });
    setUpdateBadge(available);
    return info;
  } catch (err) {
    return {
      current,
      latest: current,
      available: false,
      error: String(err?.message || err),
      checkedAt: Date.now()
    };
  }
}

// Register the recurring alarm and run an immediate check. Safe to call on both
// install and browser startup — alarms.create just replaces an existing one.
function scheduleUpdateChecks() {
  try {
    chrome.alarms.create(UPDATE_ALARM, {
      periodInMinutes: UPDATE_PERIOD_MIN,
      delayInMinutes: 1
    });
  } catch (_) {}
  checkForUpdate();
}

self.smartiiCheckUpdate = checkForUpdate;
self.smartiiScheduleUpdateChecks = scheduleUpdateChecks;
self.SMARTII_UPDATE = { UPDATE_ALARM, UPDATE_CACHE_KEY, UPDATE_PERIOD_MIN };
