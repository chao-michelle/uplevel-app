# UpLevel

A personalized static web app for UpLevel, a ~90-person private event. Each
attendee gets their own generated page (e.g. based on survey responses and
matches with other attendees), published as a static site via GitHub Pages.

## Project structure

```
/data                         raw/cleaned survey exports (gitignored) + demo-*.json (committed, synthetic)
/scripts                      python scripts for cleaning, matching, table assignment, and page generation
/site                         generated static HTML output — this is what gets deployed
/site/profile/{slug}          public profile per attendee — what lookbook cards link to
/site/uplevel/{private_slug}  private full page (schedule, matches) — never linked, direct-send only
/site/lookbook                filterable directory of all attendees, links to /profile only
/site/assets                  shared CSS, fonts, and brand assets used across generated pages
/site-demo                    generated preview site from synthetic data — gitignored, never deployed
/design-system                MASTER.md — colors, typography, and brand asset usage; the source
                               of truth for any future styling work
```

**Public vs. private pages**: every attendee gets two separate pages, not
one. `/profile/{slug}/` is public — name, roles, industries, LinkedIn —
and is the only thing the lookbook (or anyone's match list) ever links
to. `/uplevel/{private_slug}/` adds asks/offers, matches, and schedule,
and is reachable only via the direct link sent to that specific person.
The two use *different* slugs on purpose: `slug` is name-derived
(`jane-doe`) and fine to be guessable since the profile page is meant to
be public anyway; `private_slug` is a random token (`jane-doe-a8f3c9d2`)
generated once in `clean.py` and kept stable across re-runs, specifically
so that seeing someone's public profile never lets you derive their
private URL.

Styling changes should start from [design-system/MASTER.md](design-system/MASTER.md),
not a fresh palette — it documents the exact brand colors/fonts and why
they were chosen, sampled from the actual logo assets rather than
generated generically.

## Pipeline

The pipeline has four stages:

1. **Clean** ([scripts/clean.py](scripts/clean.py)) — loads the raw
   registrant CSV export, drops admin/waiver columns, normalizes role
   fields into lists and dietary answers into clean text (or `null`), and
   writes one JSON record per attendee keyed by a name-derived slug. Also
   generates each attendee's `private_slug` (a random token, not derived
   from their name) — reused from the existing output on re-runs (matched
   by email) so a person's private link never silently changes.
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
   *two* pages per attendee: a public profile at `/site/profile/{slug}/`
   and a private full page at `/site/uplevel/{private_slug}/`, plus a
   filterable lookbook at `/site/lookbook/` that links only to the public
   profiles. If an attendee record has `matches` and/or `table`, the
   private page renders those as real content; otherwise it falls back to
   the original "coming soon" placeholders. Match cards on the private
   page link to the matched person's *public* profile, never their
   private page.

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
privacy relies on obscurity + de-indexing, not access control — with one
important distinction now that pages are split into public/private:

- **Public profile pages (`/profile/{slug}/`) are meant to be found** —
  that's the point, they're what the lookbook links to. Their slug is
  name-derived and guessable on purpose; there's nothing sensitive on
  them (name, roles, industries, LinkedIn — all already visible in the
  lookbook itself).
- **Private pages (`/uplevel/{private_slug}/`) hold the sensitive
  content** — asks/offers, match recommendations, table/schedule — and
  use a *separate*, randomly-generated slug (see `make_private_slug()` in
  [scripts/clean.py](scripts/clean.py)) that cannot be derived from the
  public slug or from an attendee's name. Nothing in the generated site
  links to a private page except the attendee's own "Back to lookbook"
  and match links, which point to *other* people's public profiles, never
  their private pages. Verified by grepping every generated HTML file for
  any `href` referencing `/uplevel/` — there are none outside a person's
  own page.
- **`site/robots.txt`** disallows all crawling (`Disallow: /`) so
  well-behaved search engines won't index either page type.
- **`noindex` meta tag** on every generated page, since `robots.txt` only
  stops crawling, not indexing of a URL discovered elsewhere (e.g. linked
  from an email).
- **`/data` is gitignored** so raw and cleaned survey exports (names,
  emails, phone numbers, private slugs, etc.) are never committed to the
  public repo.

None of this is real access control — anyone who obtains a private URL
(e.g. it leaks from an email, or a link gets forwarded) can still view
that page; there's no login. What this design actually prevents is the
specific failure mode that prompted it: *other attendees browsing the
public lookbook* reaching someone's schedule or match list. It does not
protect against someone deliberately sharing or leaking their own private
link.

**Important caveat, not new but worth restating here**: this repo is
public (required for free-tier Pages), and generated pages are committed
to it — so every `private_slug` value is visible to anyone who browses
`site/uplevel/` in the GitHub file tree, not just people using the
deployed website. That's the same "public repo = public git history"
tradeoff already true for every other name/role/LinkedIn value on this
site; the private/public page split raises the bar from "click a lookbook
card" to "think to check the source repo," but doesn't eliminate that
route entirely. Closing it fully would mean either a paid plan for
private-repo Pages, or generating pages at deploy time from data that
never gets committed — both bigger changes than this one, and worth a
deliberate decision rather than a silent one.

Also note that generated pages in `/site` **are** committed (Pages serves
them from the repo), so attendee content that ends up on a page — public
or private — is in public git history too, including past versions after
edits/deletes. Keep raw source data out of git entirely (`/data` is
gitignored) and treat anything written into `/site` as public and
permanent, private slug included.
