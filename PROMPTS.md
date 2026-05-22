# Smartii — Image-generation prompts

Two prompts. Run the **logo** prompt first, save the result, then feed the logo
into the **banner** prompt.

Tested wording works well on Midjourney, DALL·E 3 (ChatGPT image), Ideogram,
Imagen, and Flux. Tweak the trailing parameters (`--ar`, `--style`) as your
generator requires.

---

## 1 · Logo

> A modern app icon for an AI browser-assistant called **Smartii**. A bold,
> geometric, friendly letter **"S"** in white, set on a squircle (iOS-style
> rounded square) with a smooth diagonal gradient from deep violet
> `#7C5CFF` (top-left) to electric cyan `#4AD6FF` (bottom-right). The S has
> slightly playful, modern curves — subtly evoking a speech bubble and a
> spark/AI feel without literal symbols. Soft inner glow, no text, no
> outline, no shadow underneath, centered, perfectly symmetrical, flat
> vector style with very subtle glassy highlight on the top edge. Clean
> background (transparent or pure white). High detail, crisp edges,
> production-ready app icon. **1024×1024, square.**
>
> `--ar 1:1 --style raw --no text, letters other than S, watermark, gradient banding`

**Export the result at 1024×1024 PNG with transparent background**, then
downscale to:

- `icons/icon128.png` (128×128)
- `icons/icon48.png` (48×48)
- `icons/icon16.png` (16×16)

Drop them into `icons/` overwriting the placeholders.

---

## 2 · Banner (use the logo you just made)

> A wide hero banner for an open-source Chrome extension called **Smartii**.
> Place the provided **Smartii logo** (violet→cyan gradient squircle with a
> white "S") in the **left third**, vertically centered, large but not
> overwhelming. To the right of the logo, the wordmark **"Smartii"** in a
> modern geometric sans-serif (Inter / Geist / SF Pro feel), pure white,
> tight letter-spacing. Below the wordmark, in a thinner weight, the tagline
> **"AI at the bottom of your browser."** in a soft 70%-opacity white.
>
> Background: a deep near-black `#0D0D12` canvas with a soft radial bloom of
> violet `#7C5CFF` in the upper-left corner and a subtle cyan `#4AD6FF`
> bloom in the upper-right — both at low opacity, blended smoothly. Add a
> very faint horizontal grid or noise texture for depth. No other text, no
> logos, no UI mockups, no people.
>
> Cinematic, premium, calm, futuristic, developer-tool aesthetic.
> **1280×320 (4:1) wide banner.**
>
> `--ar 4:1 --style raw --no extra text, screenshots, UI panels, browser frames, characters, watermark`

Save as `banner.png` in the repo root and reference it from the top of
`README.md`:

```markdown
![Smartii](banner.png)
```

Then commit and amend the README with the banner.
