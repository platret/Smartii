// Smartii service worker
// Responsibilities:
//   - Handle the Ctrl+Shift+S keybind → tell the active tab to toggle the bar
//   - Handle Alt+Shift+S → screenshot + solve immediately
//   - Handle Ctrl+Shift+G → Godmode (Pro): auto-solve everything visible, no input needed
//   - Capture full-screen screenshots via chrome.tabs.captureVisibleTab
//   - Proxy provider calls (some providers reject CORS from content scripts)
//   - Verify Pro entitlement against the smartii.app backend (Supabase)

importScripts("lib/config.js");
importScripts("lib/providers.js");
importScripts("lib/entitlement.js");
importScripts("lib/update.js");

const DEFAULTS = {
  provider: "gemini",
  model: "",
  apiKeys: {},
  appearance: {
    theme: "solid",        // "solid" | "clear" (glass)
    accent: "#7C5CFF",
    width: 720,
    cornerRadius: 18,
    bottomOffset: 24,
    schoolMode: false      // discreet: no backgrounds/shadows/loader, faint text only
  },
  systemPrompt:
    "You are Smartii, a fast, helpful assistant. The user pressed a keybind to summon you. If an image of the user's screen is attached, read everything visible (questions, code, errors, UI) and directly solve or answer it. Be concise unless asked otherwise."
};

async function getSettings() {
  const stored = await chrome.storage.sync.get(null);
  return {
    ...DEFAULTS,
    ...stored,
    appearance: { ...DEFAULTS.appearance, ...(stored.appearance || {}) },
    apiKeys: { ...DEFAULTS.apiKeys, ...(stored.apiKeys || {}) }
  };
}

chrome.runtime.onInstalled.addListener(async ({ reason }) => {
  if (reason === "install") {
    await chrome.storage.sync.set(DEFAULTS);
    chrome.runtime.openOptionsPage();
  }
  if (reason === "update") {
    // We're now running the new version — clear any stale "update available"
    // badge from the previous version.
    try { await chrome.action.setBadgeText({ text: "" }); } catch (_) {}
  }
  self.smartiiScheduleUpdateChecks();
});

// Re-arm the alarm after a browser restart (alarms survive, but a fresh check
// on startup keeps the badge accurate).
chrome.runtime.onStartup.addListener(() => self.smartiiScheduleUpdateChecks());

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === self.SMARTII_UPDATE.UPDATE_ALARM) self.smartiiCheckUpdate();
});

// Clicking the extension icon toggles the bar on the active tab.
// If the page is restricted (chrome://, web store, etc.), fall back to opening settings.
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab?.id) {
    chrome.runtime.openOptionsPage();
    return;
  }
  const ok = await sendToTab(tab.id, { type: "TOGGLE" });
  if (!ok) chrome.runtime.openOptionsPage();
});

chrome.commands.onCommand.addListener(async (command) => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;
  if (command === "toggle-smartii") {
    sendToTab(tab.id, { type: "TOGGLE" });
  } else if (command === "solve-now") {
    sendToTab(tab.id, { type: "SOLVE_NOW" });
  } else if (command === "godmode") {
    const pro = await self.smartiiCheckPro();
    if (!pro.active) {
      sendToTab(tab.id, { type: "GODMODE_LOCKED", reason: pro.reason });
      return;
    }
    sendToTab(tab.id, { type: "GODMODE" });
  }
});

// Try to deliver a message to the content script. If it isn't loaded
// (the user installed Smartii after this tab was already open, or
// chrome navigated since), inject it programmatically and retry.
// Returns true on success, false if the page can't host extensions.
async function sendToTab(tabId, msg) {
  try {
    await chrome.tabs.sendMessage(tabId, msg);
    return true;
  } catch (_) {
    // Content script wasn't there. Inject it.
  }
  try {
    await chrome.scripting.insertCSS({
      target: { tabId },
      files: ["content.css"]
    });
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content.js"]
    });
    await chrome.tabs.sendMessage(tabId, msg);
    return true;
  } catch (err) {
    // chrome://, chrome-extension://, Web Store, or similar restricted URL.
    console.warn("[Smartii] cannot run on this page:", err?.message || err);
    return false;
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    try {
      if (msg.type === "GET_SETTINGS") {
        sendResponse({ ok: true, settings: await getSettings() });
        return;
      }
      if (msg.type === "OPEN_OPTIONS") {
        chrome.runtime.openOptionsPage();
        sendResponse({ ok: true });
        return;
      }
      if (msg.type === "CAPTURE_SCREEN") {
        const dataUrl = await chrome.tabs.captureVisibleTab({ format: "png" });
        sendResponse({ ok: true, dataUrl });
        return;
      }
      if (msg.type === "SOLVE") {
        const settings = await getSettings();
        const providerId = msg.provider || settings.provider;
        const apiKey = settings.apiKeys[providerId];
        if (!apiKey) {
          sendResponse({
            ok: false,
            error:
              "No API key set for " +
              providerId +
              ". Open Smartii settings (extension icon) to add one."
          });
          return;
        }
        const answer = await self.smartiiCallProvider(providerId, apiKey, {
          prompt: msg.prompt,
          imageDataUrl: msg.imageDataUrl,
          model: msg.model || settings.model || undefined
        });
        sendResponse({ ok: true, answer });
        return;
      }
      if (msg.type === "CHECK_PRO") {
        sendResponse({ ok: true, pro: await self.smartiiCheckPro({ force: msg.force }) });
        return;
      }
      if (msg.type === "CHECK_UPDATE") {
        sendResponse({ ok: true, update: await self.smartiiCheckUpdate({ force: msg.force }) });
        return;
      }
      if (msg.type === "RELOAD_EXTENSION") {
        // Hot-reload from disk. After an external `git pull` (or replacing the
        // folder's files), this loads the new code instantly — no trip to
        // chrome://extensions. chrome.runtime.reload() restarts the extension
        // using whatever is currently on disk.
        sendResponse({ ok: true });
        setTimeout(() => chrome.runtime.reload(), 150);
        return;
      }
      if (msg.type === "SIGN_IN") {
        sendResponse(await self.smartiiSignIn(msg.email));
        return;
      }
      if (msg.type === "SIGN_OUT") {
        await self.smartiiSignOut();
        sendResponse({ ok: true });
        return;
      }
      sendResponse({ ok: false, error: "Unknown message type: " + msg.type });
    } catch (err) {
      sendResponse({ ok: false, error: err?.message || String(err) });
    }
  })();
  return true; // async
});
