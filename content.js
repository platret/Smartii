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
  let pill, tip;
  let pendingRequest = false;
  let lastAnswer = "";
  let lastEscAt = 0;            // for double-Esc panic
  let convo = [];              // recent {q, a} turns for follow-up context
  let tipTimer = null;

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
    root.classList.toggle("smartii-stealth", !!a.schoolMode);
    root.classList.toggle("smartii-disguise", !!a.disguise);
    if (pill) {
      pill.style.setProperty("--smartii-accent", a.accent);
      pill.style.setProperty("--smartii-bottom", a.bottomOffset + "px");
      pill.classList.toggle("smartii-solid", a.theme === "solid");
      pill.classList.toggle("smartii-clear", a.theme === "clear");
      pill.classList.toggle("smartii-stealth", !!a.schoolMode || !!a.disguise);
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
        <div class="smartii-cookie" data-smartii-cookie>
          <span class="smartii-cookie-text">🍪 This site uses cookies to enhance your experience.</span>
          <span class="smartii-cookie-btns"><b data-smartii-cookie-ok>Accept</b> · <span>Reject</span></span>
        </div>
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

    // Stealth answer tooltip — a tiny floating chip used when "stealth answers"
    // is on (and in disguise mode). Anchored near a field or screen corner.
    tip = document.createElement("div");
    tip.id = "smartii-tip";
    document.documentElement.appendChild(tip);
    tip.addEventListener("click", () => hideTip());

    // In disguise mode "Accept" just dismisses the fake cookie banner.
    root.querySelector("[data-smartii-cookie-ok]")?.addEventListener("click", (e) => {
      e.stopPropagation();
      close();
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

    // Double-tap Escape anywhere on the page = panic (instant hide + wipe).
    document.addEventListener(
      "keydown",
      (e) => {
        if (e.key !== "Escape") return;
        const now = Date.now();
        if (now - lastEscAt < 500) {
          panic();
          lastEscAt = 0;
        } else {
          lastEscAt = now;
        }
      },
      true
    );
  }

  // --- visibility helpers ---

  function openBar() {
    if (!root) build();
    root.style.display = ""; // clear any panic hard-hide
    pill?.classList.remove("smartii-pill-show");
    root.classList.add("smartii-open");
    // In disguise mode there's no input to focus — it's all keybind-driven.
    if (!settings?.appearance?.disguise) setTimeout(() => input?.focus(), 50);
  }

  function hideBar() {
    root?.classList.remove("smartii-open");
  }

  function close() {
    hideBar();
    pill?.classList.remove("smartii-pill-show");
  }

  // Panic: instantly nuke everything visible and wipe the last answer/history.
  // No fade — display:none immediately so a glance catches nothing.
  function panic() {
    pendingRequest = false;
    lastAnswer = "";
    convo = [];
    if (input) input.value = "";
    setOutput("");
    hideTip();
    if (root) {
      root.classList.remove("smartii-open");
      root.style.display = "none";
    }
    pill?.classList.remove("smartii-pill-show");
  }

  // --- stealth answer tooltip ---

  function showTip(text, anchorEl) {
    if (!tip) build();
    tip.textContent = text;
    if (anchorEl && anchorEl.getBoundingClientRect) {
      const r = anchorEl.getBoundingClientRect();
      tip.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 280)) + "px";
      tip.style.top = Math.min(r.bottom + 6, window.innerHeight - 40) + "px";
      tip.style.right = "auto";
      tip.style.bottom = "auto";
    } else {
      tip.style.right = "18px";
      tip.style.bottom = "18px";
      tip.style.left = "auto";
      tip.style.top = "auto";
    }
    tip.classList.add("smartii-tip-show");
    clearTimeout(tipTimer);
    tipTimer = setTimeout(hideTip, 9000);
  }

  function hideTip() {
    tip?.classList.remove("smartii-tip-show");
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
    return mathify(
      s
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
        .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>')
    );
  }

  // Lightweight equation rendering — handles the LaTeX/math the models actually
  // emit for school work (fractions, powers, roots, common symbols) without
  // bundling a full TeX engine. Input is already HTML-escaped.
  function mathify(s) {
    if (!/[\\^_]|\\frac|\\sqrt/.test(s)) return s;
    return s
      // strip math delimiters \( \) \[ \]
      .replace(/\\[()[\]]/g, "")
      // \frac{a}{b}
      .replace(/\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}/g,
        '<span class="smartii-frac"><sup>$1</sup><sub>$2</sub></span>')
      // \sqrt{x}
      .replace(/\\sqrt\s*\{([^{}]*)\}/g, "&radic;<span class=\"smartii-root\">$1</span>")
      // superscripts / subscripts
      .replace(/\^\{([^{}]*)\}/g, "<sup>$1</sup>")
      .replace(/\^(-?[0-9A-Za-z]+)/g, "<sup>$1</sup>")
      .replace(/_\{([^{}]*)\}/g, "<sub>$1</sub>")
      .replace(/_(-?[0-9A-Za-z]+)/g, "<sub>$1</sub>")
      // common symbols
      .replace(/\\cdot/g, "·").replace(/\\times/g, "×").replace(/\\div/g, "÷")
      .replace(/\\pm/g, "±").replace(/\\leq?\b/g, "≤").replace(/\\geq?\b/g, "≥")
      .replace(/\\neq\b/g, "≠").replace(/\\approx\b/g, "≈").replace(/\\infty\b/g, "∞")
      .replace(/\\pi\b/g, "π").replace(/\\theta\b/g, "θ").replace(/\\Delta\b/g, "Δ")
      .replace(/\\(?:to|rightarrow)\b/g, "→").replace(/\\Rightarrow\b/g, "⇒")
      .replace(/\\left|\\right/g, "");
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

      // Follow-up: a typed question (no screenshot) carries the recent Q&A so
      // the user can ask "explain step 2" without re-capturing.
      let sendPrompt = prompt;
      if (!includeScreenshot && userPrompt && convo.length) {
        const history = convo
          .slice(-3)
          .map((t) => `Q: ${t.q}\nA: ${t.a}`)
          .join("\n\n");
        sendPrompt =
          "Earlier in this conversation:\n" + history +
          "\n\nFollow-up question: " + userPrompt;
      }

      const res = await chrome.runtime.sendMessage({
        type: "SOLVE",
        prompt: sendPrompt,
        imageDataUrl,
        provider: settings.provider,
        model: settings.model
      });

      pendingRequest = false;
      hidePill();

      if (!res?.ok) throw new Error(res?.error || "unknown error");

      // Remember the turn for follow-ups (cap history).
      convo.push({ q: userPrompt || "(screen)", a: res.answer });
      if (convo.length > 6) convo.shift();

      if (stealthAnswersOn()) {
        // Don't open the bar — drop a discreet tooltip in the corner.
        lastAnswer = res.answer;
        showTip(res.answer, null);
      } else {
        openBar();
        setStatus("");
        setAnswer(res.answer);
      }
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

  const MAX_FIELDS = 120; // bound the prompt size on pathological pages

  // Walk the WHOLE DOM (including same-origin iframes) for every fillable
  // control — text inputs, textareas, dropdowns, contenteditable — whether or
  // not it's currently scrolled into view, so Godmode never misses a field.
  // We only drop controls that are genuinely unusable (hidden, disabled,
  // zero-size) or part of Smartii's own UI. Index order is the contract with
  // the model.
  function collectFillableFields() {
    const sel =
      'input, textarea, select, [contenteditable=""], [contenteditable="true"]';
    const skipTypes = [
      "hidden", "submit", "button", "image", "file", "reset", "color"
      // note: checkbox/radio ARE included now (handled specially on fill)
    ];
    const out = [];

    const scan = (rootDoc) => {
      let nodes;
      try {
        nodes = rootDoc.querySelectorAll(sel);
      } catch (_) {
        return; // cross-origin doc, skip
      }
      for (const el of nodes) {
        if (out.length >= MAX_FIELDS) return;
        if (el.closest("#smartii-root, #smartii-pill")) continue;
        const tag = el.tagName.toLowerCase();
        const type = (el.getAttribute("type") || "").toLowerCase();
        if (tag === "input" && skipTypes.includes(type)) continue;
        if (el.disabled || el.readOnly) continue;
        const r = el.getBoundingClientRect();
        // Keep zero-size only if it's not actually rendered-away; most real
        // fields have a box. Truly hidden controls (display:none) report 0×0.
        if (r.width < 2 && r.height < 2) continue;
        const st = el.ownerDocument.defaultView?.getComputedStyle(el);
        if (st && (st.visibility === "hidden" || st.display === "none" || +st.opacity === 0)) continue;
        out.push({ i: out.length, el, tag, type, ctx: describeField(el) });
      }
    };

    scan(document);
    // Same-origin iframes (some quiz pages embed the form in one).
    for (const frame of document.querySelectorAll("iframe")) {
      if (out.length >= MAX_FIELDS) break;
      let doc;
      try {
        doc = frame.contentDocument;
      } catch (_) {
        doc = null;
      }
      if (doc) scan(doc);
    }
    return out;
  }

  function describeField(el) {
    const bits = [];
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute("type") || "").toLowerCase();

    let label;
    if (el.id) {
      const l = el.ownerDocument.querySelector(`label[for="${CSS.escape(el.id)}"]`);
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
    if (near && near.length < 220) bits.push('near="' + clip(near, 140) + '"');

    if (tag === "select") {
      // Give the model the exact option set so it can choose a valid one.
      const opts = [...el.options].map((o) => clip(o.text, 50)).filter(Boolean);
      if (opts.length) bits.push("options=[" + opts.map((o) => JSON.stringify(o)).join(",") + "]");
      const sel = el.options[el.selectedIndex];
      if (sel) bits.push('current="' + clip(sel.text, 50) + '"');
    } else if (type === "checkbox" || type === "radio") {
      bits.push("kind=" + type, "checked=" + (el.checked ? "true" : "false"));
    } else {
      const val = el.isContentEditable ? el.textContent : el.value;
      if (val) bits.push('current="' + clip(val, 40) + '"');
    }
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
      const type = (el.getAttribute("type") || "").toLowerCase();
      try {
        el.focus({ preventScroll: true });
        if (el.isContentEditable) {
          el.textContent = value;
        } else if (el.tagName === "SELECT") {
          const want = value.trim().toLowerCase();
          const opt =
            [...el.options].find((o) => o.value === value || o.text.trim() === value) ||
            [...el.options].find(
              (o) =>
                o.value.toLowerCase() === want ||
                o.text.trim().toLowerCase() === want ||
                o.text.trim().toLowerCase().includes(want)
            );
          if (!opt) continue;
          el.value = opt.value;
        } else if (type === "checkbox" || type === "radio") {
          const on = /^(true|1|yes|on|checked|x|✓)$/i.test(value.trim());
          if (type === "radio" && !on) continue; // only the chosen radio gets set
          el.checked = type === "radio" ? true : on;
          el.dispatchEvent(new Event("click", { bubbles: true }));
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

  function stealthAnswersOn() {
    const a = settings?.appearance || {};
    return !!a.stealthAnswers || !!a.disguise;
  }

  // After filling, optionally click the page's submit button. Prefer a submit
  // inside the same form as the filled fields; fall back to a button whose text
  // looks like "submit / done / check" (multilingual).
  function autoSubmit(fields) {
    const SUBMIT_RE =
      /\b(submit|send|done|finish|check|verify|continue|next|ok|fertig|abgeben|prüfen|weiter|absenden|bestätigen|valider|enviar|comprobar)\b/i;
    const forms = new Set(fields.map((f) => f.el.form).filter(Boolean));
    const candidates = [];
    for (const form of forms) {
      candidates.push(...form.querySelectorAll('button, input[type="submit"], input[type="button"]'));
    }
    if (!candidates.length) {
      candidates.push(...document.querySelectorAll('button, input[type="submit"]'));
    }
    const pick = candidates.find((b) => {
      const label = (b.value || b.innerText || b.getAttribute("aria-label") || "").trim();
      return SUBMIT_RE.test(label);
    }) || candidates.find((b) => (b.type || "").toLowerCase() === "submit");
    if (pick) {
      pick.click();
      return true;
    }
    return false;
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
      "Below is the COMPLETE list of fillable fields on the page (read straight from the " +
      "DOM, so it includes fields that may be partly off-screen), each as " +
      "`#index <tag:type> context`:\n" +
      manifest +
      "\n\nSolve everything shown and decide what every field should contain. Rules:\n" +
      "- Provide a value for EVERY field index above unless it genuinely must stay empty. Do not skip any.\n" +
      '- For <select> fields, "value" MUST be one of the exact strings listed in that field\'s options=[...].\n' +
      '- For checkbox/radio fields, use "value":"true" to tick it or "false" to leave it.\n' +
      "- For a fraction laid out as separate numerator/denominator boxes, fill each box with its single number.\n" +
      'Respond with ONLY a JSON object — no markdown, no prose:\n' +
      '{"fills":[{"i":0,"value":"3"},{"i":1,"value":"29"}],"note":"one short line with the final answer"}\n' +
      'Use the integer field index in "i". "value" is the exact text to put in that field.';

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

      const a = settings.appearance || {};
      const parsed = parseFillJson(res.answer);

      if (parsed && Array.isArray(parsed.fills) && parsed.fills.length) {
        const n = applyFills(fields, parsed.fills);
        const note = parsed.note ? parsed.note.trim() : "";
        const summary = (note ? note + "\n\n" : "") + `**✓ Filled ${n} field${n === 1 ? "" : "s"}** on the page.`;

        if (a.autoSubmit) {
          // small beat so framework state settles before submitting
          setTimeout(() => autoSubmit(fields), 250);
        }

        if (stealthAnswersOn()) {
          lastAnswer = note || res.answer;
          if (note) showTip(note, fields[parsed.fills[0]?.i]?.el || null);
        } else {
          openBar();
          setStatus("");
          setAnswer(summary);
          if (a.autoHide) setTimeout(close, 2000);
        }
      } else {
        // Model didn't return usable JSON — show whatever it said.
        if (stealthAnswersOn()) {
          lastAnswer = res.answer;
          showTip(res.answer, null);
        } else {
          openBar();
          setStatus("");
          setAnswer(res.answer);
        }
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
      convo.push({ q: "(screen)", a: res.answer });
      if (convo.length > 6) convo.shift();
      if (stealthAnswersOn()) {
        lastAnswer = res.answer;
        showTip(res.answer, null);
      } else {
        openBar();
        setStatus("");
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
    } else if (msg.type === "PANIC") {
      panic();
    } else if (msg.type === "SETTINGS_UPDATED") {
      loadSettings();
    }
  });

  chrome.storage?.onChanged.addListener(() => loadSettings());

  loadSettings();
})();
