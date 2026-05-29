# Smartii — feature ideas

A backlog of things Smartii could do. Ordered roughly by value-to-effort.
Items marked ✅ already shipped.

## Shipped recently
- ✅ **Markdown answers** — model output is rendered (code blocks, lists, bold,
  links) instead of raw text, so code is readable and copy-pasteable.
- ✅ **Copy button** — one click copies the full answer to the clipboard.
- ✅ **Local Godmode unlock** — self-hosted / unpacked builds can enable Godmode
  from the options page without a Pro backend (per-device, never synced).
- ✅ **Cleaner screenshots** — the "Thinking" pill no longer lands in the captured
  image, so the model never sees Smartii's own UI.

## High value, low effort
- **Follow-up / conversation** — keep the last answer in context so the user can
  ask "explain step 2" without re-screenshotting. Store a short message history
  per tab in memory.
- **Region screenshot** — drag a rectangle to capture only part of the page
  instead of the whole viewport. Better for dense pages and privacy.
- **Re-run / regenerate** — a button to re-ask the same prompt (handy when a free
  model gives a weak answer).
- **Streaming responses** — stream tokens into the output box instead of waiting
  for the full reply. Most providers support SSE; feels 3× faster.
- **Answer history** — a small log of the last N answers per tab, reachable from
  the bar, so nothing is lost when you close it.
- **Quick actions on selection** — when text is selected, offer "Explain",
  "Summarize", "Translate", "Fix grammar" chips.

## Medium effort
- **Multi-shot Godmode** — for long pages/exams, auto-scroll + capture several
  screens and answer everything across them.
- **Per-site provider/model** — remember "use Claude on github.com, Gemini
  elsewhere".
- **Prompt templates / slash commands** — `/eli5`, `/code`, `/tr fr` expand into
  full prompts. Editable in settings.
- **Voice input** — Web Speech API to dictate the question.
- **PDF / canvas awareness** — detect embedded PDFs and grab text directly rather
  than only screenshotting.
- **Export answer** — save an answer as markdown or copy as an image.
- **Token / cost meter** — rough per-request cost estimate for paid providers.

## Bigger bets
- **Local model support** — talk to Ollama / LM Studio on `localhost` for a fully
  offline, free, private mode.
- **Agentic actions** — let the model click/fill the page (fill a form, click the
  correct answer) via the content script, with a confirm step.
- **Team / shared prompts** — sync a prompt library across a team (Pro).
- **Mobile companion** — a bookmarklet or PWA share-target for Android Chrome.

## Monetization / Pro
- **Smartii-hosted key** — a managed-key tier so non-technical users don't need
  their own API key (Pro covers inference).
- **Usage analytics for the owner** — privacy-respecting counts of Godmode usage
  to inform pricing.
