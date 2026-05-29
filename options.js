// Smartii options page
const $ = (sel) => document.querySelector(sel);

const DEFAULTS = {
  provider: "gemini",
  model: "",
  apiKeys: {},
  appearance: {
    theme: "solid",
    accent: "#7C5CFF",
    width: 720,
    cornerRadius: 18,
    bottomOffset: 24,
    schoolMode: false
  },
  systemPrompt:
    "You are Smartii, a fast, helpful assistant. The user pressed a keybind to summon you. If an image of the user's screen is attached, read everything visible (questions, code, errors, UI) and directly solve or answer it. Be concise unless asked otherwise."
};

let state = structuredClone(DEFAULTS);

function renderProviders() {
  const grid = $("#providerGrid");
  grid.innerHTML = "";
  for (const p of Object.values(SMARTII_PROVIDERS)) {
    const el = document.createElement("div");
    el.className = "provider-card" + (p.id === state.provider ? " active" : "");
    el.dataset.id = p.id;
    el.innerHTML = `
      <div class="name">${p.label}</div>
      <span class="tier tier-${p.tier}">${p.tier}</span>
    `;
    el.addEventListener("click", () => {
      state.provider = p.id;
      renderProviders();
      renderActiveProvider();
    });
    grid.appendChild(el);
  }
}

function renderActiveProvider() {
  const p = SMARTII_PROVIDERS[state.provider];
  $("#activeProviderLabel").textContent = p.label;
  $("#providerHelp").innerHTML = `
    <strong>${p.label}</strong> — ${p.instructions}<br/>
    <span class="small">
      🔗 Sign up: <a href="${p.signupUrl}" target="_blank" rel="noopener">${p.signupUrl}</a><br/>
      🔑 Get API key: <a href="${p.keyUrl}" target="_blank" rel="noopener">${p.keyUrl}</a>
    </span>
  `;
  $("#apiKey").value = state.apiKeys[p.id] || "";

  const modelSel = $("#model");
  modelSel.innerHTML = "";
  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = `Default — ${p.defaultModel}`;
  modelSel.appendChild(blank);
  for (const m of p.models) {
    const opt = document.createElement("option");
    opt.value = m;
    opt.textContent = m + (m === p.defaultModel ? "  (default)" : "");
    modelSel.appendChild(opt);
  }
  modelSel.value = state.model || "";
}

function renderAppearance() {
  const a = state.appearance;
  $("#theme").value = a.theme;
  $("#accent").value = a.accent;
  $("#width").value = a.width;
  $("#cornerRadius").value = a.cornerRadius;
  $("#bottomOffset").value = a.bottomOffset;
  $("#schoolMode").checked = !!a.schoolMode;
  $("#systemPrompt").value = state.systemPrompt;
}

function bindAppearanceInputs() {
  $("#theme").addEventListener("change", (e) => (state.appearance.theme = e.target.value));
  $("#accent").addEventListener("input", (e) => (state.appearance.accent = e.target.value));
  $("#width").addEventListener("input", (e) => (state.appearance.width = +e.target.value || 720));
  $("#cornerRadius").addEventListener("input", (e) => (state.appearance.cornerRadius = +e.target.value || 0));
  $("#bottomOffset").addEventListener("input", (e) => (state.appearance.bottomOffset = +e.target.value || 0));
  $("#schoolMode").addEventListener("change", (e) => (state.appearance.schoolMode = e.target.checked));
  $("#systemPrompt").addEventListener("input", (e) => (state.systemPrompt = e.target.value));
  $("#apiKey").addEventListener("input", (e) => {
    state.apiKeys[state.provider] = e.target.value;
  });
  $("#model").addEventListener("change", (e) => (state.model = e.target.value));
}

async function load() {
  const stored = await chrome.storage.sync.get(null);
  state = {
    ...DEFAULTS,
    ...stored,
    appearance: { ...DEFAULTS.appearance, ...(stored.appearance || {}) },
    apiKeys: { ...DEFAULTS.apiKeys, ...(stored.apiKeys || {}) }
  };
  renderProviders();
  renderActiveProvider();
  renderAppearance();
}

async function save() {
  await chrome.storage.sync.set(state);
  const tabs = await chrome.tabs.query({});
  for (const t of tabs) {
    if (!t.id) continue;
    chrome.tabs.sendMessage(t.id, { type: "SETTINGS_UPDATED" }).catch(() => {});
  }
  const s = $("#saveStatus");
  s.textContent = "Saved ✓";
  setTimeout(() => (s.textContent = ""), 1800);
}

// --- Smartii Pro UI ---

async function loadProSection() {
  const site = (window.SMARTII_CONFIG && window.SMARTII_CONFIG.SITE_URL) || "https://platret.github.io/Smartii/";
  const upgrade = $("#proUpgrade");
  const manage = $("#proManage");
  if (upgrade) upgrade.href = site + "#pricing";
  if (manage) manage.href = site + "#account";

  const res = await chrome.runtime.sendMessage({ type: "CHECK_PRO" });
  const pro = res?.pro || { active: false, reason: "unknown" };
  const session = await chrome.storage.local.get("smartiiSession");
  const email = session?.smartiiSession?.user?.email;

  if (email) {
    $("#proSignedOut").hidden = true;
    $("#proSignedIn").hidden = false;
    $("#proEmailLabel").textContent = email;
    $("#proPlanLabel").textContent = pro.active
      ? `Pro · ${pro.plan || "active"}`
      : `Free · ${pro.reason || "no entitlement"}`;
  } else {
    $("#proSignedOut").hidden = false;
    $("#proSignedIn").hidden = true;
  }
}

async function loadSelfHostToggle() {
  const box = $("#proOverride");
  if (!box) return;
  const { smartiiProOverride } = await chrome.storage.local.get("smartiiProOverride");
  box.checked = !!smartiiProOverride;
  box.addEventListener("change", async () => {
    await chrome.storage.local.set({ smartiiProOverride: box.checked });
    // Bust the 6h Pro cache so Godmode unlocks/locks immediately.
    await chrome.storage.local.remove("smartiiProCache");
    await chrome.runtime.sendMessage({ type: "CHECK_PRO", force: true });
    loadProSection();
  });
}

// --- Update checker UI ---

function renderUpdate(info) {
  const status = $("#updateStatus");
  const link = $("#updateLink");
  if (!status || !link) return;
  const cur = chrome.runtime.getManifest().version;
  if (!info) {
    status.textContent = `You're on v${cur}.`;
    link.hidden = true;
    return;
  }
  if (info.error) {
    status.textContent = `Couldn't reach GitHub (${info.error}). You're on v${cur}.`;
    link.hidden = true;
    return;
  }
  if (info.available) {
    status.textContent = `Update available — v${info.latest} (you have v${info.current}).`;
    link.href = info.url;
    link.textContent = `Download v${info.latest} →`;
    link.hidden = false;
  } else {
    status.textContent = `You're up to date (v${info.current}).`;
    link.hidden = true;
  }
}

async function loadUpdateSection() {
  const { smartiiUpdate } = await chrome.storage.local.get("smartiiUpdate");
  renderUpdate(smartiiUpdate);
  $("#checkUpdate")?.addEventListener("click", async () => {
    $("#updateStatus").textContent = "Checking…";
    const res = await chrome.runtime.sendMessage({ type: "CHECK_UPDATE", force: true });
    renderUpdate(res?.update);
  });
  $("#reloadExt")?.addEventListener("click", async () => {
    await chrome.runtime.sendMessage({ type: "RELOAD_EXTENSION" });
    // The extension restarts; this page will lose its connection. Give feedback.
    $("#updateStatus").textContent = "Reloading Smartii from disk…";
  });
}

function bindProInputs() {
  $("#proSignIn")?.addEventListener("click", async () => {
    const email = $("#proEmail").value.trim();
    if (!email) {
      $("#proStatus").textContent = "Enter your email first.";
      return;
    }
    $("#proStatus").textContent = "Sending…";
    const res = await chrome.runtime.sendMessage({ type: "SIGN_IN", email });
    $("#proStatus").textContent = res?.ok ? res.message : (res?.error || "Failed.");
  });
  $("#proSignOut")?.addEventListener("click", async () => {
    await chrome.runtime.sendMessage({ type: "SIGN_OUT" });
    await loadProSection();
  });
  $("#proRefresh")?.addEventListener("click", async () => {
    const res = await chrome.runtime.sendMessage({ type: "CHECK_PRO", force: true });
    const pro = res?.pro || {};
    $("#proPlanLabel").textContent = pro.active
      ? `Pro · ${pro.plan || "active"}`
      : `Free · ${pro.reason || "no entitlement"}`;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindAppearanceInputs();
  bindProInputs();
  $("#save").addEventListener("click", save);
  load();
  loadProSection();
  loadSelfHostToggle();
  loadUpdateSection();
});
