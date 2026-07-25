# UpLevel

A personalized static web app for UpLevel, a ~90-person private event. Each
attendee gets their own generated page (e.g. based on survey responses and
matches with other attendees), published as a static site via GitHub Pages.

## Project structure

```
/data                 raw and cleaned survey exports — gitignored, not committed
/scripts              python scripts for cleaning, matching, and page generation
/site                 generated static HTML output
/site/uplevel/{slug}  one page per attendee
/site/lookbook        filterable directory of all attendees
/site/assets          shared CSS used across generated pages
```

## Pipeline

The pipeline has three stages:

1. **Clean** ([scripts/clean.py](scripts/clean.py)) — loads the raw
   registrant CSV export, drops admin/waiver columns, normalizes role
   fields into lists and dietary answers into clean text (or `null`), and
   writes one JSON record per attendee keyed by a name-derived slug.
2. **Match** ([scripts/match.py](scripts/match.py)) — placeholder;
   matching/groupings logic isn't built yet.
3. **Generate** ([scripts/generate_pages.py](scripts/generate_pages.py)) —
   reads `attendees.json` and renders one HTML page per attendee under
   `/site/uplevel/{slug}/`, plus a filterable directory page at
   `/site/lookbook/`.

### Running end to end

```bash
python scripts/clean.py         --input data/form-response.csv --output data/attendees.json
python scripts/match.py         # not implemented yet
python scripts/generate_pages.py --input data/attendees.json --output-dir site/
```

Each script is a standalone CLI so any stage can be re-run independently
once its input exists. `clean.py` and `generate_pages.py` also work with
no flags — they default to the paths above.

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
