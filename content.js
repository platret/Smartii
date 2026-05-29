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
  let actionsEl, copyBtn;
  let pill;
  let pendingRequest = false;
  let lastAnswer = "";

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
        <div class="smartii-actions" data-smartii-actions>
          <button class="smartii-btn smartii-ghost smartii-copy" data-smartii-copy title="Copy answer">Copy</button>
        </div>
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
    actionsEl = root.querySelector("[data-smartii-actions]");
    copyBtn = root.querySelector("[data-smartii-copy]");

    copyBtn?.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(lastAnswer || "");
        copyBtn.textContent = "Copied ✓";
        setTimeout(() => (copyBtn.textContent = "Copy"), 1400);
      } catch (_) {
        copyBtn.textContent = "Copy failed";
        setTimeout(() => (copyBtn.textContent = "Copy"), 1400);
      }
    });

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

  // Plain error / status text — no markdown, no copy affordance.
  function setOutput(text) {
    if (!output) return;
    lastAnswer = text || "";
    output.textContent = lastAnswer;
    output.classList.toggle("smartii-show", !!text);
    actionsEl?.classList.remove("smartii-show");
  }

  // Model answers arrive as markdown. Render a safe subset (code blocks,
  // inline code, bold/italic, headings, lists, links) and reveal the Copy
  // button. Everything is HTML-escaped before any formatting is applied.
  function setAnswer(md) {
    if (!output) return;
    lastAnswer = md || "";
    if (!md) {
      output.textContent = "";
      output.classList.remove("smartii-show");
      actionsEl?.classList.remove("smartii-show");
      return;
    }
    output.innerHTML = renderMarkdown(md);
    output.classList.add("smartii-show");
    actionsEl?.classList.add("smartii-show");
  }

  function escapeHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function inline(s) {
    // s is already HTML-escaped.
    return s
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
      .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
  }

  function renderMarkdown(md) {
    const escaped = escapeHtml(md);
    // Pull fenced code blocks out first so their contents aren't formatted.
    const blocks = [];
    const withoutCode = escaped.replace(/```[a-z]*\n?([\s\S]*?)```/gi, (_, code) => {
      blocks.push(code.replace(/\n$/, ""));
      return " " + (blocks.length - 1) + " ";
    });

    const lines = withoutCode.split("\n");
    const html = [];
    let listType = null; // "ul" | "ol" | null

    const closeList = () => {
      if (listType) {
        html.push(`</${listType}>`);
        listType = null;
      }
    };

    for (const raw of lines) {
      const line = raw.replace(/\r$/, "");
      const codePh = /^ (\d+) $/.exec(line.trim());
      if (codePh) {
        closeList();
        html.push("<pre><code>" + blocks[Number(codePh[1])] + "</code></pre>");
        continue;
      }
      const h = /^(#{1,4})\s+(.*)$/.exec(line);
      if (h) {
        closeList();
        const lvl = Math.min(h[1].length + 2, 6); // # -> h3
        html.push(`<h${lvl}>${inline(h[2])}</h${lvl}>`);
        continue;
      }
      const ol = /^\s*\d+\.\s+(.*)$/.exec(line);
      const ul = /^\s*[-*]\s+(.*)$/.exec(line);
      if (ol) {
        if (listType !== "ol") { closeList(); html.push("<ol>"); listType = "ol"; }
        html.push("<li>" + inline(ol[1]) + "</li>");
        continue;
      }
      if (ul) {
        if (listType !== "ul") { closeList(); html.push("<ul>"); listType = "ul"; }
        html.push("<li>" + inline(ul[1]) + "</li>");
        continue;
      }
      if (line.trim() === "") {
        closeList();
        continue;
      }
      closeList();
      html.push("<p>" + inline(line) + "</p>");
    }
    closeList();
    return html.join("");
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

    // Bar goes away immediately; gives the user the page back while the model
    // thinks. For screenshot mode we hold the pill until *after* capture so it
    // never lands in the shot — otherwise the model "sees" our own UI.
    hideBar();
    if (!includeScreenshot) showPill();

    try {
      let imageDataUrl;
      let prompt = userPrompt;
      if (includeScreenshot) {
        // Give the browser a tick to actually clear the hidden bar.
        await new Promise((r) => setTimeout(r, 220));
        imageDataUrl = await captureScreen();
        showPill();
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
      setAnswer(res.answer);
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

  // Godmode prompt: pure auto-solve, no user input. Tells the model to read
  // EVERYTHING on screen and answer directly — useful for quizzes, homework,
  // code traces, error dialogs, anything visible.
  const GOD_PROMPT =
    "GODMODE: read the entire attached screenshot of the user's screen. " +
    "Identify the most important question, problem, code, error, or task on screen and " +
    "answer it directly and completely. If there are multiple questions, answer all of them, " +
    "numbered. If it's a multiple-choice question, give the correct letter AND the reasoning. " +
    "If it's code or an error, show the fix. Be precise. No filler.";

  async function godmode() {
    if (!settings) await loadSettings();
    if (!root) build();
    if (input) input.value = "";
    // If the page has fields the user could type into, Godmode fills them in
    // directly instead of just printing the answer. Otherwise it falls back to
    // the classic read-and-answer behavior.
    const fields = collectFillableFields();
    if (fields.length) {
      await godmodeFill(fields);
      return;
    }
    await solveWithPrompt(GOD_PROMPT, true);
  }

  // --- Godmode auto-fill (agentic) ----------------------------------------

  function clip(s, n) {
    s = String(s || "").replace(/\s+/g, " ").trim();
    return s.length > n ? s.slice(0, n) + "…" : s;
  }

  // Find inputs/textareas/selects/contenteditable that are on screen, enabled,
  // and not part of Smartii's own UI. Index order is the contract with the model.
  function collectFillableFields() {
    const sel =
      'input, textarea, select, [contenteditable=""], [contenteditable="true"]';
    const skipTypes = [
      "hidden", "submit", "button", "image", "file", "reset",
      "checkbox", "radio", "range", "color"
    ];
    const out = [];
    for (const el of document.querySelectorAll(sel)) {
      if (el.closest("#smartii-root, #smartii-pill")) continue;
      const tag = el.tagName.toLowerCase();
      const type = (el.getAttribute("type") || "").toLowerCase();
      if (tag === "input" && skipTypes.includes(type)) continue;
      if (el.disabled || el.readOnly) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      // Only fields inside the captured viewport (the screenshot is what the
      // model sees, so anything off-screen has no visual context).
      if (r.bottom <= 0 || r.top >= innerHeight || r.right <= 0 || r.left >= innerWidth) continue;
      const st = getComputedStyle(el);
      if (st.visibility === "hidden" || st.display === "none" || +st.opacity === 0) continue;
      out.push({ i: out.length, el, tag, type, ctx: describeField(el) });
    }
    return out;
  }

  function describeField(el) {
    const bits = [];
    let label;
    if (el.id) {
      const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (l) label = l.innerText;
    }
    if (!label) {
      const wrap = el.closest("label");
      if (wrap) label = wrap.innerText;
    }
    label =
      label ||
      el.getAttribute("aria-label") ||
      el.getAttribute("placeholder") ||
      el.name ||
      el.getAttribute("title");
    if (label) bits.push('label="' + clip(label, 80) + '"');
    const near = el.parentElement?.innerText || "";
    if (near && near.length < 200) bits.push('near="' + clip(near, 120) + '"');
    const val = el.isContentEditable ? el.textContent : el.value;
    if (val) bits.push('current="' + clip(val, 40) + '"');
    return bits.join(" ") || "(no label)";
  }

  // React/Vue track value through the property setter, so set it the native way
  // and fire input+change so the framework's state updates too.
  function setNativeValue(el, value) {
    const proto =
      el.tagName === "TEXTAREA"
        ? HTMLTextAreaElement.prototype
        : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
    if (setter) setter.call(el, value);
    else el.value = value;
  }

  function flashField(el) {
    const prevOutline = el.style.outline;
    const prevOffset = el.style.outlineOffset;
    el.style.outline = "2px solid var(--smartii-accent, #7c5cff)";
    el.style.outlineOffset = "1px";
    setTimeout(() => {
      el.style.outline = prevOutline;
      el.style.outlineOffset = prevOffset;
    }, 1800);
  }

  function applyFills(fields, fills) {
    let n = 0;
    for (const f of fills) {
      const field = fields[f && f.i];
      if (!field) continue;
      const el = field.el;
      const value = String(f.value ?? "");
      try {
        el.focus({ preventScroll: true });
        if (el.isContentEditable) {
          el.textContent = value;
        } else if (el.tagName === "SELECT") {
          const opt = [...el.options].find(
            (o) => o.value === value || o.text.trim() === value
          );
          if (!opt) continue;
          el.value = opt.value;
        } else {
          setNativeValue(el, value);
        }
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
        flashField(el);
        n++;
      } catch (_) {
        // skip a field we can't write to; keep going
      }
    }
    return n;
  }

  // The model is asked for strict JSON, but be tolerant of code fences / stray
  // prose around it.
  function parseFillJson(text) {
    if (!text) return null;
    let t = text.trim().replace(/^```[a-z]*\s*/i, "").replace(/```\s*$/, "");
    const start = t.indexOf("{");
    const end = t.lastIndexOf("}");
    if (start === -1 || end === -1 || end < start) return null;
    try {
      return JSON.parse(t.slice(start, end + 1));
    } catch {
      return null;
    }
  }

  async function godmodeFill(fields) {
    if (pendingRequest) return;
    if (!settings) await loadSettings();

    const manifest = fields
      .map((f) => `#${f.i} <${f.tag}${f.type ? ":" + f.type : ""}> ${f.ctx}`)
      .join("\n");
    const prompt =
      "GODMODE AUTO-FILL. A screenshot of the user's screen is attached. " +
      "The page has these fillable fields (index → context, including any current value):\n" +
      manifest +
      "\n\nSolve everything shown on screen and decide what each field should contain. " +
      'Respond with ONLY a JSON object — no markdown, no prose:\n' +
      '{"fills":[{"i":0,"value":"3"}],"note":"one short line with the answer"}\n' +
      'Use the integer field index in "i". "value" is the exact text to type into that field. ' +
      "Only include fields you are confident about; omit any that should stay blank.";

    pendingRequest = true;
    setOutput("");
    setStatus("");
    hideBar();

    try {
      await new Promise((r) => setTimeout(r, 220));
      const imageDataUrl = await captureScreen();
      showPill();
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
      const parsed = parseFillJson(res.answer);
      if (parsed && Array.isArray(parsed.fills) && parsed.fills.length) {
        const n = applyFills(fields, parsed.fills);
        const note = parsed.note ? parsed.note.trim() + "\n\n" : "";
        setAnswer(note + `**✓ Filled ${n} field${n === 1 ? "" : "s"}** on the page.`);
      } else {
        // Model didn't return usable JSON — show whatever it said.
        setAnswer(res.answer);
      }
    } catch (err) {
      pendingRequest = false;
      hidePill();
      openBar();
      setStatus("");
      setOutput("Error: " + (err?.message || String(err)));
    }
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
    if (!includeScreenshot) showPill();

    try {
      let imageDataUrl;
      if (includeScreenshot) {
        await new Promise((r) => setTimeout(r, 220));
        imageDataUrl = await captureScreen();
        showPill();
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
      setAnswer(res.answer);
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
