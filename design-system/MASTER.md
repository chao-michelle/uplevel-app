# UpLevel design system

Source of truth for colors, typography, and brand asset usage across the
UpLevel site. **Future styling work should build on this, not introduce
new hues, fonts, or ad hoc treatments.** If a change conflicts with
something documented here, update this file in the same change rather
than letting the two drift apart.

## Source assets

- [`site/assets/branding/uplevel-square.png`](../site/assets/branding/uplevel-square.png) —
  square logo treatment: navy italic serif "UPLEVEL" wordmark, lavender
  highlight block behind the tagline, black-and-white line-art Boston
  skyline.
- [`site/assets/branding/uplevel-rectangle.png`](../site/assets/branding/uplevel-rectangle.png) —
  wide banner version of the same, skyline as a light watermark behind the
  wordmark. Used as the hero banner (see below).

Both colors below were extracted by sampling actual pixels from these
files with Pillow (not eyeballed) — see the palette section for the exact
regions sampled. Re-run that sampling if the source assets are ever
replaced, rather than hand-picking new values.

## Color palette

| Token | Hex | Source / role |
|---|---|---|
| `--brand-navy` | `#102f76` | Sampled from the wordmark strokes and the tagline text in both source images (identical across 4 independent sample regions). This **is** `--accent`. |
| `--brand-lavender` | `#c5cae9` | Sampled from the highlight-block background behind the tagline (identical across both source images). |
| `--bg` | `#f8f8fb` | Page background — near-white, subtly navy-tinted rather than neutral gray. |
| `--surface` | `#ffffff` | Card/panel background. |
| `--text` | `#1c2233` | Body text — a dark navy-charcoal, not pure black, not the fully-saturated brand navy (that's reserved for headlines/links/accents so it doesn't get diluted by overuse). |
| `--text-muted` | `#5c6478` | Secondary text, eyebrows, captions. |
| `--border` | `#dfe2ea` | Default hairline borders. |
| `--accent` | `var(--brand-navy)` | Headlines, links, primary buttons, primary role tag. |
| `--accent-hover` | `#0c2359` | Hover/pressed state for accent-colored interactive elements. |
| `--accent-bg` | `#e8eaf6` | Light navy tint — hover backgrounds, primary tag chip background. Lighter/less saturated than the raw brand lavender, for use as ambient UI chrome. |
| `--tag-bg` | `#eef0f5` | Neutral chip background for generic "other role" tags. |
| `--industry-bg` | `var(--brand-lavender)` | Industry tag chips — deliberately the *exact* brand lavender, recreating how the source logo itself uses it (a saturated highlight block, not a muted tint). |
| `--industry-text` | `var(--brand-navy)` | Text on industry tags — same navy-on-lavender pairing the logo uses. |
| `--demo-bg` / `--demo-text` / `--demo-border` | `#fff4e5` / `#8a5a00` / `#f0c98a` | Demo-data warning banner. Intentionally **not** part of the brand family — this is a semantic caution color, kept distinct so it reads as "system warning," not "brand accent." |

**Rule: lavender is a background fill, never a text/foreground color.** At
`#c5cae9` it doesn't have enough contrast against white to work as text —
and that's not how the logo uses it either (it's always a block behind
navy text). If you need a lighter accent surface that isn't full lavender,
use `--accent-bg`, not a diluted lavender.

## Typography

- **Display (page titles / `<h1>` only):** `Playfair Display`, italic,
  weight 700 — closest freely-licensed match to the wordmark's tall,
  high-contrast Didone-style italic. Self-hosted at
  [`site/assets/fonts/PlayfairDisplay-Italic-Variable.woff2`](../site/assets/fonts/PlayfairDisplay-Italic-Variable.woff2)
  (~39KB, latin subset, a variable font covering weights 500–800) so pages
  keep making zero third-party network requests — this project
  deliberately avoids external requests elsewhere too (no CDN avatars,
  `robots.txt` disallow, etc.), and font loading shouldn't be the
  exception. Falls back to `Georgia, "Times New Roman", serif` if the
  woff2 fails to load.
- **Body (everything else):** the existing system-font stack
  (`system-ui, -apple-system, "Segoe UI", sans-serif`) — filters, buttons,
  tags, `<h2>` section headers, lookbook cards, all body copy.

**Rule: the serif italic is a display face for page titles only — never
apply it to `<h2>` section headers, lookbook card names, buttons, or
anything data-dense.** It's used exactly once per page (the `<h1>`). This
was an explicit constraint, not an oversight — a page with 85 attendee
cards rendered in an ornate italic would be unreadable and would cheapen
the treatment. `<h2>` stays sans-serif and semibold instead.

## Hero banner

`uplevel-rectangle.png` renders full-width (`.hero-banner`, outside
`<main>`'s content column, so it isn't constrained to the 960px reading
width) at the top of:
- `/site/lookbook/` and `/site-demo/lookbook/`
- `/site/index.html` (landing page)

**Not used on individual attendee pages** — the skyline line-art is busy
at full detail, and repeating it behind dense per-attendee content
(asks/offers, matches, schedule) would compete with that content rather
than frame it. If a future page wants a lighter brand touch, consider a
cropped/faded portion rather than the full banner.

## Favicon

Derived from `uplevel-square.png`, **not used as-is** — at 16–32px the
full illustration (wordmark + tagline + skyline) is illegible. Two
alternatives were tested at actual pixel size before deciding:
1. Full wordmark text, cropped tight — confirmed illegible even at 32px
   (just a blue smear, not readable as "UPLEVEL").
2. **Skyline silhouette** (a square crop around the twin-tower + Custom
   House clock cluster, recolored from black to `--brand-navy` instead of
   staying black/white) — reads as a distinct two-tower shape at 32/48px,
   weaker but still recognizable at 16px. This is what's live.

Generated files in `site/assets/branding/`: `favicon-16.png`,
`favicon-32.png`, `favicon-48.png`, `apple-touch-icon.png` (180×180).
Regenerate with the crop/recolor logic if the source logo ever changes —
the exact crop coordinates are only in the conversation history, not
scripted, so a future regen means re-deriving the crop box by eye against
the new asset.

## Verified contrast ratios

Computed (not eyeballed) against actual WCAG luminance formulas for every
foreground/background pairing actually used in the CSS:

| Pairing | Ratio | Result |
|---|---|---|
| `--text` on `--bg` | 14.94:1 | AAA |
| `--text-muted` on `--bg` | 5.58:1 | AA |
| `--accent` (h1/links) on white | 12.42:1 | AAA |
| `--industry-text` on `--industry-bg` | 7.69:1 | AAA |
| `--accent` on `--accent-bg` (primary tag) | 10.37:1 | AAA |
| `--text` on `--surface` | 15.84:1 | AAA |
| `--demo-text` on `--demo-bg` | 5.45:1 | AA |

Every pairing clears WCAG AA (4.5:1); most clear AAA (7:1). If a future
color addition doesn't hit at least AA against its intended background,
don't ship it — adjust the shade rather than accepting a fail.

## Typography pairing, independently cross-checked

Playfair Display + a clean sans body font is a recognized pairing for
"elegant, editorial" contexts (not just this project's own reasoning) —
confirms the direction without dictating the specific sans-serif, which
stays the existing system-font stack here rather than a second
self-hosted font, to avoid adding another network-independence tradeoff
beyond the one already made for the display face.

## Applying this system to new pages/features

- Pull colors from the CSS custom properties above (`site/assets/style.css`
  `:root`), never hardcode a hex value that isn't already one of these
  tokens.
- New "brand moment" UI (a badge, a highlight block) should default to
  the navy-on-lavender pairing already established, not a new color.
- New page-level headings get the serif italic treatment; everything
  inside a page (including section headers) stays sans-serif.
- If a future prompt asks for "a palette" or "a new color" without
  referencing this file, point back to it rather than generating a
  generic one — that's the mistake this file exists to prevent.
