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
    bottomOffset: 24
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
  $("#systemPrompt").value = state.systemPrompt;
}

function bindAppearanceInputs() {
  $("#theme").addEventListener("change", (e) => (state.appearance.theme = e.target.value));
  $("#accent").addEventListener("input", (e) => (state.appearance.accent = e.target.value));
  $("#width").addEventListener("input", (e) => (state.appearance.width = +e.target.value || 720));
  $("#cornerRadius").addEventListener("input", (e) => (state.appearance.cornerRadius = +e.target.value || 0));
  $("#bottomOffset").addEventListener("input", (e) => (state.appearance.bottomOffset = +e.target.value || 0));
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

document.addEventListener("DOMContentLoaded", () => {
  bindAppearanceInputs();
  $("#save").addEventListener("click", save);
  load();
});
