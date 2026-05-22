// Smartii provider registry
// Each provider declares: id, label, tier (free|paid|mixed), endpoint, defaultModel,
// supportsVision, signupUrl, keyUrl, instructions, and a request builder.

const PROVIDERS = {
  groq: {
    id: "groq",
    label: "Groq (free tier)",
    tier: "free",
    defaultModel: "llama-3.3-70b-versatile",
    models: [
      "llama-3.3-70b-versatile",
      "llama-3.1-8b-instant",
      "llama-3.2-90b-vision-preview",
      "mixtral-8x7b-32768"
    ],
    supportsVision: true, // only certain models
    signupUrl: "https://console.groq.com/",
    keyUrl: "https://console.groq.com/keys",
    instructions:
      "Sign in to console.groq.com, open API Keys, create a new key, and paste it below. Groq offers a generous free tier with very fast inference. Pick a *-vision-preview model to send screenshots."
  },
  openrouter: {
    id: "openrouter",
    label: "OpenRouter (many free + paid models)",
    tier: "mixed",
    defaultModel: "meta-llama/llama-3.3-70b-instruct:free",
    models: [
      "meta-llama/llama-3.3-70b-instruct:free",
      "google/gemini-2.0-flash-exp:free",
      "qwen/qwen-2.5-vl-72b-instruct:free",
      "deepseek/deepseek-chat:free",
      "anthropic/claude-3.5-sonnet",
      "openai/gpt-4o",
      "google/gemini-pro-1.5"
    ],
    supportsVision: true,
    signupUrl: "https://openrouter.ai/",
    keyUrl: "https://openrouter.ai/keys",
    instructions:
      "Create an account at openrouter.ai, go to Keys, generate one and paste below. Any model ending in ':free' costs nothing. Vision-capable free models include qwen-2.5-vl and gemini-2.0-flash-exp."
  },
  gemini: {
    id: "gemini",
    label: "Google Gemini (free tier)",
    tier: "free",
    defaultModel: "gemini-2.0-flash",
    models: [
      "gemini-2.0-flash",
      "gemini-2.5-flash",
      "gemini-2.5-pro",
      "gemini-1.5-flash",
      "gemini-1.5-pro"
    ],
    supportsVision: true,
    signupUrl: "https://aistudio.google.com/",
    keyUrl: "https://aistudio.google.com/app/apikey",
    instructions:
      "Visit aistudio.google.com, click 'Get API key', create one in a new project, and paste below. Free tier includes generous quotas for gemini-2.0-flash and gemini-1.5-flash."
  },
  anthropic: {
    id: "anthropic",
    label: "Anthropic Claude (paid)",
    tier: "paid",
    defaultModel: "claude-sonnet-4-6",
    models: [
      "claude-opus-4-7",
      "claude-sonnet-4-6",
      "claude-haiku-4-5-20251001"
    ],
    supportsVision: true,
    signupUrl: "https://console.anthropic.com/",
    keyUrl: "https://console.anthropic.com/settings/keys",
    instructions:
      "Sign in to console.anthropic.com, add billing, then create an API key under Settings → API Keys. Paste it below. No free tier, but credits are sometimes offered to new accounts."
  },
  openai: {
    id: "openai",
    label: "OpenAI ChatGPT (paid)",
    tier: "paid",
    defaultModel: "gpt-4o",
    models: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-mini"],
    supportsVision: true,
    signupUrl: "https://platform.openai.com/",
    keyUrl: "https://platform.openai.com/api-keys",
    instructions:
      "Sign in to platform.openai.com, add billing, open API keys and create a new key. Paste below. gpt-4o-mini is the cheapest vision-capable option."
  },
  perplexity: {
    id: "perplexity",
    label: "Perplexity (paid)",
    tier: "paid",
    defaultModel: "sonar",
    models: ["sonar", "sonar-pro", "sonar-reasoning", "sonar-reasoning-pro"],
    supportsVision: false,
    signupUrl: "https://www.perplexity.ai/settings/api",
    keyUrl: "https://www.perplexity.ai/settings/api",
    instructions:
      "Open perplexity.ai → Settings → API, add a payment method and generate a key. Paste below. Perplexity is great for live web-grounded answers but does not accept images."
  },
  huggingface: {
    id: "huggingface",
    label: "Hugging Face Inference (free tier)",
    tier: "free",
    defaultModel: "meta-llama/Llama-3.3-70B-Instruct",
    models: [
      "meta-llama/Llama-3.3-70B-Instruct",
      "Qwen/Qwen2.5-72B-Instruct",
      "mistralai/Mistral-7B-Instruct-v0.3"
    ],
    supportsVision: false,
    signupUrl: "https://huggingface.co/join",
    keyUrl: "https://huggingface.co/settings/tokens",
    instructions:
      "Create a free Hugging Face account, go to Settings → Access Tokens and create a 'Read' token. Paste below. Free tier has rate limits; vision support varies by model."
  }
};

// Build the HTTP request for a given provider + payload.
// payload: { prompt: string, imageDataUrl?: string, model?: string }
function buildRequest(providerId, apiKey, payload) {
  const provider = PROVIDERS[providerId];
  if (!provider) throw new Error("Unknown provider: " + providerId);
  const model = payload.model || provider.defaultModel;
  const userText = payload.prompt || "Solve / explain what's on the screen.";
  const hasImage = !!payload.imageDataUrl;

  switch (providerId) {
    case "groq":
    case "openrouter":
    case "openai": {
      const url =
        providerId === "groq"
          ? "https://api.groq.com/openai/v1/chat/completions"
          : providerId === "openrouter"
          ? "https://openrouter.ai/api/v1/chat/completions"
          : "https://api.openai.com/v1/chat/completions";
      const content = hasImage
        ? [
            { type: "text", text: userText },
            { type: "image_url", image_url: { url: payload.imageDataUrl } }
          ]
        : userText;
      return {
        url,
        init: {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + apiKey,
            ...(providerId === "openrouter"
              ? { "HTTP-Referer": "https://github.com/platret/Smartii", "X-Title": "Smartii" }
              : {})
          },
          body: JSON.stringify({
            model,
            messages: [{ role: "user", content }],
            max_tokens: 2048
          })
        },
        parse: (data) => data.choices?.[0]?.message?.content ?? JSON.stringify(data)
      };
    }
    case "gemini": {
      const parts = [{ text: userText }];
      if (hasImage) {
        const [meta, b64] = payload.imageDataUrl.split(",");
        const mime = /data:(.*?);/.exec(meta)?.[1] || "image/png";
        parts.push({ inline_data: { mime_type: mime, data: b64 } });
      }
      return {
        url: `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(
          apiKey
        )}`,
        init: {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contents: [{ role: "user", parts }] })
        },
        parse: (data) =>
          data.candidates?.[0]?.content?.parts?.map((p) => p.text).join("") ??
          JSON.stringify(data)
      };
    }
    case "anthropic": {
      const content = hasImage
        ? [
            {
              type: "image",
              source: {
                type: "base64",
                media_type:
                  /data:(.*?);/.exec(payload.imageDataUrl)?.[1] || "image/png",
                data: payload.imageDataUrl.split(",")[1]
              }
            },
            { type: "text", text: userText }
          ]
        : [{ type: "text", text: userText }];
      return {
        url: "https://api.anthropic.com/v1/messages",
        init: {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-api-key": apiKey,
            "anthropic-version": "2023-06-01",
            "anthropic-dangerous-direct-browser-access": "true"
          },
          body: JSON.stringify({
            model,
            max_tokens: 2048,
            messages: [{ role: "user", content }]
          })
        },
        parse: (data) =>
          data.content?.map((c) => c.text).join("") ?? JSON.stringify(data)
      };
    }
    case "perplexity": {
      return {
        url: "https://api.perplexity.ai/chat/completions",
        init: {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + apiKey
          },
          body: JSON.stringify({
            model,
            messages: [{ role: "user", content: userText }]
          })
        },
        parse: (data) => data.choices?.[0]?.message?.content ?? JSON.stringify(data)
      };
    }
    case "huggingface": {
      return {
        url: `https://api-inference.huggingface.co/models/${model}`,
        init: {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + apiKey
          },
          body: JSON.stringify({
            inputs: userText,
            parameters: { max_new_tokens: 1024, return_full_text: false }
          })
        },
        parse: (data) =>
          Array.isArray(data)
            ? data[0]?.generated_text ?? JSON.stringify(data)
            : data.generated_text ?? JSON.stringify(data)
      };
    }
    default:
      throw new Error("Unsupported provider " + providerId);
  }
}

async function callProvider(providerId, apiKey, payload) {
  const { url, init, parse } = buildRequest(providerId, apiKey, payload);
  const res = await fetch(url, init);
  const raw = await res.text();
  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    data = { raw };
  }
  if (!res.ok) {
    const msg =
      data?.error?.message ||
      data?.error ||
      data?.message ||
      `HTTP ${res.status}`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return parse(data);
}

// Export to both worker and window scopes
if (typeof self !== "undefined") {
  self.SMARTII_PROVIDERS = PROVIDERS;
  self.smartiiBuildRequest = buildRequest;
  self.smartiiCallProvider = callProvider;
}
