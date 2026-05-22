// Smartii content script — injects the floating bar at the bottom-middle of the page.

(function () {
  if (window.__smartiiInjected) return;
  window.__smartiiInjected = true;

  let settings = null;
  let root, input, sendBtn, snapBtn, closeBtn, output, status, providerLabel;
  let lastCapture = null;

  async function loadSettings() {
    const res = await chrome.runtime.sendMessage({ type: "GET_SETTINGS" });
    settings = res?.settings;
    applyAppearance();
  }

  function applyAppearance() {
    if (!root || !settings) return;
    const a = settings.appearance;
    root.style.setProperty("--smartii-accent", a.accent);
    root.style.setProperty("--smartii-width", a.width + "px");
    root.style.setProperty("--smartii-radius", a.cornerRadius + "px");
    root.style.setProperty("--smartii-bottom", a.bottomOffset + "px");
    root.classList.toggle("smartii-solid", a.theme === "solid");
    root.classList.toggle("smartii-clear", a.theme === "clear");
    if (providerLabel) {
      providerLabel.textContent = settings.provider;
    }
  }

  function build() {
    root = document.createElement("div");
    root.id = "smartii-root";
    root.className = "smartii-solid";
    const logoUrl = chrome.runtime.getURL("icons/icon48.png");
    root.innerHTML = `
      <div class="smartii-card">
        <div class="smartii-row">
          <div class="smartii-logo">
            <img src="${logoUrl}" alt="Smartii" />
          </div>
          <input class="smartii-input" type="text"
                 placeholder="Ask Smartii anything, or hit Solve to read the screen…" />
          <span class="smartii-meta" data-smartii-provider></span>
          <button class="smartii-btn smartii-ghost" data-smartii-snap title="Screenshot + solve (Ctrl+Shift+Enter)">📸 Solve</button>
          <button class="smartii-btn" data-smartii-send>Send</button>
          <button class="smartii-btn smartii-ghost" data-smartii-close title="Close (Esc)">✕</button>
        </div>
        <div class="smartii-status" data-smartii-status></div>
        <div class="smartii-output" data-smartii-output></div>
      </div>
    `;
    document.documentElement.appendChild(root);

    input = root.querySelector(".smartii-input");
    sendBtn = root.querySelector("[data-smartii-send]");
    snapBtn = root.querySelector("[data-smartii-snap]");
    closeBtn = root.querySelector("[data-smartii-close]");
    output = root.querySelector("[data-smartii-output]");
    status = root.querySelector("[data-smartii-status]");
    providerLabel = root.querySelector("[data-smartii-provider]");

    sendBtn.addEventListener("click", () => solve(false));
    snapBtn.addEventListener("click", () => solve(true));
    closeBtn.addEventListener("click", close);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        solve(e.ctrlKey || e.metaKey);
      } else if (e.key === "Escape") {
        close();
      }
    });
  }

  function open() {
    if (!root) build();
    root.classList.add("smartii-open");
    setTimeout(() => input?.focus(), 50);
  }

  function close() {
    root?.classList.remove("smartii-open");
  }

  function toggle() {
    if (!root) build();
    if (root.classList.contains("smartii-open")) close();
    else open();
  }

  function setStatus(text) {
    if (!status) return;
    status.textContent = text || "";
    status.classList.toggle("smartii-show", !!text);
  }

  function setOutput(text) {
    if (!output) return;
    output.textContent = text || "";
    output.classList.toggle("smartii-show", !!text);
  }

  // Grab the visible content of the page as text (used when there's no key for a vision model).
  function grabPageText() {
    const sel = window.getSelection()?.toString();
    if (sel && sel.trim().length > 0) return sel.slice(0, 12000);
    const main = document.querySelector("main, article, [role=main]") || document.body;
    return (main.innerText || "").slice(0, 12000);
  }

  async function captureScreen() {
    const res = await chrome.runtime.sendMessage({ type: "CAPTURE_SCREEN" });
    if (!res?.ok) throw new Error(res?.error || "capture failed");
    lastCapture = res.dataUrl;
    return res.dataUrl;
  }

  async function solve(includeScreenshot) {
    if (!settings) await loadSettings();
    open();
    const userPrompt = input.value.trim();
    setOutput("");
    setStatus("Thinking…");

    try {
      let imageDataUrl;
      let prompt = userPrompt;
      if (includeScreenshot) {
        setStatus("Capturing screen…");
        imageDataUrl = await captureScreen();
        if (!prompt) {
          prompt = "Read the attached screenshot of the user's screen and solve / answer whatever is shown. Be direct.";
        }
      } else if (!prompt) {
        // No prompt and no screenshot → fall back to page text
        const pageText = grabPageText();
        prompt =
          "Help with the content on this page. Page text follows between <page> tags.\n<page>\n" +
          pageText +
          "\n</page>";
      }

      setStatus("Calling " + settings.provider + "…");
      const res = await chrome.runtime.sendMessage({
        type: "SOLVE",
        prompt,
        imageDataUrl,
        provider: settings.provider,
        model: settings.model
      });
      if (!res?.ok) throw new Error(res?.error || "unknown error");
      setStatus("");
      setOutput(res.answer);
    } catch (err) {
      setStatus("");
      setOutput("⚠ " + (err?.message || String(err)));
    }
  }

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "TOGGLE") {
      if (!settings) loadSettings().then(toggle);
      else toggle();
    } else if (msg.type === "SOLVE_NOW") {
      if (!settings) loadSettings().then(() => solve(true));
      else solve(true);
    } else if (msg.type === "SETTINGS_UPDATED") {
      loadSettings();
    }
  });

  // Re-apply appearance when settings change in storage.
  chrome.storage?.onChanged.addListener(() => loadSettings());

  loadSettings();
})();
