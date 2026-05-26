// Smartii content script.
// Owns the floating bar at the bottom of the page and the small "Thinking..."
// pill that takes its place while a request is in flight.
//
// States:
//   closed   - nothing visible
//   expanded - full bar visible (input + buttons + optional answer below)
//   thinking - pill visible, bar hidden, request in flight
// On submit the bar hides immediately (so it doesn't end up in the screenshot
// and so the user sees the page again while the model thinks). When the
// response arrives the bar reopens with the answer.

(function () {
  if (window.__smartiiInjected) return;
  window.__smartiiInjected = true;

  let settings = null;
  let root, input, sendBtn, snapBtn, settingsBtn, closeBtn, output, statusEl, providerLabel;
  let pill;
  let pendingRequest = false;

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
    if (pill) {
      pill.style.setProperty("--smartii-accent", a.accent);
      pill.style.setProperty("--smartii-bottom", a.bottomOffset + "px");
      pill.classList.toggle("smartii-solid", a.theme === "solid");
      pill.classList.toggle("smartii-clear", a.theme === "clear");
    }
    if (providerLabel) providerLabel.textContent = settings.provider;
  }

  function build() {
    const logoUrl = chrome.runtime.getURL("icons/icon48.png");

    root = document.createElement("div");
    root.id = "smartii-root";
    root.className = "smartii-solid";
    root.innerHTML = `
      <div class="smartii-card">
        <div class="smartii-row">
          <div class="smartii-logo">
            <img src="${logoUrl}" alt="Smartii" />
          </div>
          <input class="smartii-input" type="text"
                 placeholder="Ask Smartii anything, or hit Solve to read the screen..." />
          <span class="smartii-meta" data-smartii-provider></span>
          <button class="smartii-btn smartii-ghost" data-smartii-snap title="Screenshot the page + solve">Solve</button>
          <button class="smartii-btn smartii-god" data-smartii-god title="Godmode — auto-solve everything (Pro)">⚡ God</button>
          <button class="smartii-btn" data-smartii-send title="Send (Enter)">Send</button>
          <button class="smartii-btn smartii-ghost" data-smartii-settings title="Settings">&#9881;</button>
          <button class="smartii-btn smartii-ghost" data-smartii-close title="Close (Esc)">&times;</button>
        </div>
        <div class="smartii-status" data-smartii-status></div>
        <div class="smartii-output" data-smartii-output></div>
      </div>
    `;
    document.documentElement.appendChild(root);

    pill = document.createElement("div");
    pill.id = "smartii-pill";
    pill.className = "smartii-solid";
    pill.innerHTML = `
      <div class="smartii-pill-inner" title="Smartii is thinking - click to reopen">
        <img src="${logoUrl}" alt="" />
        <span class="smartii-pill-text">Thinking</span>
        <span class="smartii-pill-dots"><i></i><i></i><i></i></span>
      </div>
    `;
    document.documentElement.appendChild(pill);
    pill.addEventListener("click", () => {
      // Reopen the bar but keep the in-flight indicator visible inside it.
      openBar();
      setStatus("Thinking...");
    });

    input = root.querySelector(".smartii-input");
    sendBtn = root.querySelector("[data-smartii-send]");
    snapBtn = root.querySelector("[data-smartii-snap]");
    settingsBtn = root.querySelector("[data-smartii-settings]");
    closeBtn = root.querySelector("[data-smartii-close]");
    output = root.querySelector("[data-smartii-output]");
    statusEl = root.querySelector("[data-smartii-status]");
    providerLabel = root.querySelector("[data-smartii-provider]");

    sendBtn.addEventListener("click", () => solve(false));
    snapBtn.addEventListener("click", () => solve(true));
    const godBtn = root.querySelector("[data-smartii-god]");
    godBtn?.addEventListener("click", async () => {
      const res = await chrome.runtime.sendMessage({ type: "CHECK_PRO" });
      if (res?.pro?.active) godmode();
      else godmodeLocked(res?.pro?.reason || "unknown");
    });
    settingsBtn.addEventListener("click", () => {
      chrome.runtime.sendMessage({ type: "OPEN_OPTIONS" });
    });
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

  // --- visibility helpers ---

  function openBar() {
    if (!root) build();
    pill?.classList.remove("smartii-pill-show");
    root.classList.add("smartii-open");
    setTimeout(() => input?.focus(), 50);
  }

  function hideBar() {
    root?.classList.remove("smartii-open");
  }

  function close() {
    hideBar();
    pill?.classList.remove("smartii-pill-show");
  }

  function toggle() {
    if (!root) build();
    if (root.classList.contains("smartii-open")) close();
    else openBar();
  }

  function showPill() {
    if (!pill) build();
    pill.classList.add("smartii-pill-show");
  }

  function hidePill() {
    pill?.classList.remove("smartii-pill-show");
  }

  function setStatus(text) {
    if (!statusEl) return;
    statusEl.textContent = text || "";
    statusEl.classList.toggle("smartii-show", !!text);
  }

  function setOutput(text) {
    if (!output) return;
    output.textContent = text || "";
    output.classList.toggle("smartii-show", !!text);
  }

  // --- helpers ---

  function grabPageText() {
    const sel = window.getSelection()?.toString();
    if (sel && sel.trim().length > 0) return sel.slice(0, 12000);
    const main = document.querySelector("main, article, [role=main]") || document.body;
    return (main.innerText || "").slice(0, 12000);
  }

  async function captureScreen() {
    const res = await chrome.runtime.sendMessage({ type: "CAPTURE_SCREEN" });
    if (!res?.ok) throw new Error(res?.error || "capture failed");
    return res.dataUrl;
  }

  // --- main flow ---

  async function solve(includeScreenshot) {
    if (pendingRequest) return; // ignore double-submits while in flight
    if (!settings) await loadSettings();

    if (!root) build();
    const userPrompt = (input?.value || "").trim();

    pendingRequest = true;
    setOutput("");
    setStatus("");

    // Bar goes away immediately; pill takes its place. Keeps the bar out
    // of the screenshot and gives the user the page back while the model thinks.
    hideBar();
    showPill();

    try {
      let imageDataUrl;
      let prompt = userPrompt;
      if (includeScreenshot) {
        // Give the browser a tick to actually render the hidden bar.
        await new Promise((r) => setTimeout(r, 220));
        imageDataUrl = await captureScreen();
        if (!prompt) {
          prompt = "Read the attached screenshot of the user's screen and solve / answer whatever is shown. Be direct.";
        }
      } else if (!prompt) {
        const pageText = grabPageText();
        prompt =
          "Help with the content on this page. Page text follows between <page> tags.\n<page>\n" +
          pageText +
          "\n</page>";
      }

      const res = await chrome.runtime.sendMessage({
        type: "SOLVE",
        prompt,
        imageDataUrl,
        provider: settings.provider,
        model: settings.model
      });

      pendingRequest = false;
      hidePill();

      if (!res?.ok) throw new Error(res?.error || "unknown error");

      openBar();
      setStatus("");
      setOutput(res.answer);
      if (input) input.value = "";
    } catch (err) {
      pendingRequest = false;
      hidePill();
      openBar();
      setStatus("");
      setOutput("Error: " + (err?.message || String(err)));
    }
  }

  // --- message routing ---

  async function godmode() {
    if (!settings) await loadSettings();
    if (!root) build();
    if (input) input.value = "";
    // Godmode prompt: pure auto-solve, no user input. Tells the model to read
    // EVERYTHING on screen and answer directly — useful for quizzes, homework,
    // code traces, error dialogs, anything visible.
    const godPrompt =
      "GODMODE: read the entire attached screenshot of the user's screen. " +
      "Identify the most important question, problem, code, error, or task on screen and " +
      "answer it directly and completely. If there are multiple questions, answer all of them, " +
      "numbered. If it's a multiple-choice question, give the correct letter AND the reasoning. " +
      "If it's code or an error, show the fix. Be precise. No filler.";
    await solveWithPrompt(godPrompt, true);
  }

  // Variant of solve() that takes a pre-built prompt and skips reading the input box.
  async function solveWithPrompt(prompt, includeScreenshot) {
    if (pendingRequest) return;
    if (!settings) await loadSettings();
    if (!root) build();

    pendingRequest = true;
    setOutput("");
    setStatus("");
    hideBar();
    showPill();

    try {
      let imageDataUrl;
      if (includeScreenshot) {
        await new Promise((r) => setTimeout(r, 220));
        imageDataUrl = await captureScreen();
      }
      const res = await chrome.runtime.sendMessage({
        type: "SOLVE",
        prompt,
        imageDataUrl,
        provider: settings.provider,
        model: settings.model
      });
      pendingRequest = false;
      hidePill();
      if (!res?.ok) throw new Error(res?.error || "unknown error");
      openBar();
      setStatus("");
      setOutput(res.answer);
    } catch (err) {
      pendingRequest = false;
      hidePill();
      openBar();
      setStatus("");
      setOutput("Error: " + (err?.message || String(err)));
    }
  }

  function godmodeLocked(reason) {
    if (!root) build();
    openBar();
    setStatus("");
    const reasons = {
      signed_out: "Godmode needs a Smartii Pro account. Open settings → Sign in.",
      no_entitlement: "Godmode is a Pro feature. Upgrade at smartii.app.",
      unconfigured: "Godmode is not configured in this build.",
      network_error: "Couldn't verify Pro status — check your connection."
    };
    setOutput(reasons[reason] || "Godmode is unavailable (" + reason + ").");
  }

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "TOGGLE") {
      if (!settings) loadSettings().then(toggle);
      else toggle();
    } else if (msg.type === "SOLVE_NOW") {
      if (!settings) loadSettings().then(() => solve(true));
      else solve(true);
    } else if (msg.type === "GODMODE") {
      godmode();
    } else if (msg.type === "GODMODE_LOCKED") {
      godmodeLocked(msg.reason);
    } else if (msg.type === "SETTINGS_UPDATED") {
      loadSettings();
    }
  });

  chrome.storage?.onChanged.addListener(() => loadSettings());

  loadSettings();
})();
