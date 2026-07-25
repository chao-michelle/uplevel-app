# UpLevel

A personalized static web app for UpLevel, a ~90-person private event. Each
attendee gets their own generated page (e.g. based on survey responses and
matches with other attendees), published as a static site via GitHub Pages.

## Project structure

```
/data                 raw/cleaned survey exports (gitignored) + demo-*.json (committed, synthetic)
/scripts              python scripts for cleaning, matching, table assignment, and page generation
/site                 generated static HTML output — this is what gets deployed
/site/uplevel/{slug}  one page per attendee
/site/lookbook        filterable directory of all attendees
/site/assets          shared CSS used across generated pages
/site-demo            generated preview site from synthetic data — gitignored, never deployed
```

## Pipeline

The pipeline has four stages:

1. **Clean** ([scripts/clean.py](scripts/clean.py)) — loads the raw
   registrant CSV export, drops admin/waiver columns, normalizes role
   fields into lists and dietary answers into clean text (or `null`), and
   writes one JSON record per attendee keyed by a name-derived slug.
2. **Match** ([scripts/match.py](scripts/match.py)) — compares each
   attendee's `asks` against everyone else's `offers` using simple
   keyword overlap and writes each attendee's top matches back onto their
   record. Real attendees.json has no `asks`/`offers` yet (Part 2 data),
   so running this against it today is a harmless no-op — every attendee
   just gets an empty match list.
3. **Assign tables** ([scripts/assign_tables.py](scripts/assign_tables.py))
   — a simplified stand-in for the eventual Phase 4 logic: deals
   attendees round-robin across N tables by primary role for a rough mix,
   with no optimization on matches or industries yet.
4. **Generate** ([scripts/generate_pages.py](scripts/generate_pages.py)) —
   reads the (optionally match/table-enriched) attendees JSON and renders
   one HTML page per attendee under `/site/uplevel/{slug}/`, plus a
   filterable directory page at `/site/lookbook/`. If an attendee record
   has `matches` and/or `table`, those render as real content; otherwise
   the page falls back to the original "coming soon" placeholders.

### Running end to end (real data, today)

Real `attendees.json` has no `asks`/`offers`/table data yet, so the real
pipeline for now is just clean → generate:

```bash
python scripts/clean.py          --input data/form-response.csv --output data/attendees.json
python scripts/generate_pages.py --input data/attendees.json --output-dir site/
```

Once Part 2 data (asks, offers, industries, sessions) is actually
collected from real attendees, the full four-stage pipeline (clean →
match → assign_tables → generate) becomes the real flow — see
[Demo mode](#demo-mode-synthetic-data) below for what that looks like end
to end, run today against synthetic data.

Each script is a standalone CLI so any stage can be re-run independently
once its input exists, and each has sensible defaults matching the paths
above so it also runs with no flags.

## Demo mode (synthetic data)

To preview the app before real Part 2 data arrives, [data/demo-attendees.json](data/demo-attendees.json)
holds 15 clearly-fake attendees (`Demo Founder One`, `demo1@example.com`,
etc.) with synthetic asks, offers, industries, and session picks —
including a few deliberately overlapping ask/offer pairs so the matcher
has something real to find.

Run the full four-stage pipeline against it, writing to `/site-demo`
instead of `/site`:

```bash
python scripts/match.py          --input data/demo-attendees.json --output data/demo-matches.json
python scripts/assign_tables.py  --input data/demo-matches.json --output data/demo-tables.json --table-size 5
python scripts/generate_pages.py --input data/demo-tables.json --output-dir site-demo/ --demo-banner
```

(There's no `clean` step for demo data — it's authored directly in the
already-cleaned schema, so cleaning a raw CSV doesn't apply.)

**`/site-demo` is for internal preview only — it is never deployed:**

- It's `.gitignore`d entirely, so it's never committed, regardless of
  what's in it.
- The GitHub Actions Pages workflow only watches `site/**`
  ([.github/workflows/deploy.yml](.github/workflows/deploy.yml)), so
  nothing under `/site-demo` can trigger a deploy even accidentally.
- `--demo-banner` stamps a visible "⚠ DEMO DATA" banner on every
  generated page as an extra guard against confusing it with the real
  site.
- The synthetic source data ([data/demo-attendees.json](data/demo-attendees.json))
  *is* committed (it's fake, so there's no PII concern) so teammates can
  regenerate the same preview after cloning the repo.

**Previewing `/site-demo` locally**, without deploying anything:

```bash
cd site-demo && python3 -m http.server 8000
```

Then open `http://localhost:8000/lookbook/` in a browser. Stop the
server with Ctrl+C when done. `/site-demo` is fully self-contained (it
gets its own copy of `assets/style.css`), so this works independently of
whatever's in `/site`.

## Deploying

The site is published straight from the `/site` folder using a GitHub
Actions workflow ([.github/workflows/deploy.yml](.github/workflows/deploy.yml))
that uploads `/site` as a Pages artifact and deploys it on every push to
`main` that touches `site/**`.

**One-time setup**, after pushing this repo to GitHub:

1. Go to the repo's **Settings → Pages**.
2. Under **Build and deployment → Source**, select **GitHub Actions**.
3. Push to `main` — the workflow builds and deploys automatically. The
   deployed URL shows up in the workflow run summary and in
   **Settings → Pages**.

You can also trigger a deploy manually from the **Actions** tab
(`Deploy site to GitHub Pages` → **Run workflow**).

This approach (a GitHub Actions deploy straight from `/site`) was chosen
over a `docs/` folder or a `gh-pages` branch because it needs no renaming
and no branch-syncing step — `/site` stays the source of truth and Pages
rebuilds from it automatically on every push.

## Data privacy note

This repo and its Pages site are **public** when deployed (private-repo
Pages needs a paid GitHub plan, which this project isn't using). Attendee
privacy relies on obscurity + de-indexing, not access control:

- **Per-attendee slugs are name-derived** (`jane-doe`, not a random token)
  — see `slugify()` in [scripts/clean.py](scripts/clean.py). This was a
  deliberate choice for readability, but it means URLs are **guessable**
  for anyone who knows (or reasonably infers) an attendee's name — the
  "unguessable slug" mitigation originally planned here does not actually
  hold with the current scheme. If stronger protection is wanted later,
  append a short random suffix to the slug (e.g. `jane-doe-x7k2`) —
  cheap to add in `clean.py` without changing anything else.
- **`site/robots.txt`** already disallows all crawling (`Disallow: /`) so
  well-behaved search engines won't index pages.
- **`noindex` meta tag** — every generated page (attendee pages and the
  lookbook) includes `<meta name="robots" content="noindex">`, since
  `robots.txt` only stops crawling, not indexing of a URL discovered
  elsewhere (e.g. linked from an email).
- **`/data` is gitignored** so raw and cleaned survey exports (names,
  emails, phone numbers, etc.) are never committed to the public repo.
- **The lookbook page (`/site/lookbook/`) lists every attendee on one
  page** — it's the highest-value target if this repo/site is public, more
  so than any single attendee page. Worth a deliberate decision before
  going live, not just relying on `noindex`.

None of this makes pages truly private — anyone with a page's URL can view
it. And note that generated pages in `/site` **are** committed (Pages
serves them from the repo), so attendee content that ends up on a page is
in public git history too, including past versions after edits/deletes.
Keep raw source data out of git entirely (`/data` is gitignored) and treat
anything written into `/site` as public and permanent.
