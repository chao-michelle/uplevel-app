# UpLevel

A personalized static web app for UpLevel, a ~90-person private event. Each
attendee gets their own generated page (e.g. based on survey responses and
matches with other attendees), published as a static site via GitHub Pages.

## Project structure

```
/data          raw and cleaned survey exports (csv) — gitignored, not committed
/scripts       python scripts for cleaning, matching, and page generation
/site          generated static HTML output, one page per attendee
/site/assets   shared CSS/images used across generated pages
```

## Pipeline

The pipeline has three stages, each a placeholder script for now:

1. **Clean** ([scripts/clean.py](scripts/clean.py)) — normalize a raw survey
   export into a clean CSV.
2. **Match** ([scripts/match.py](scripts/match.py)) — compute attendee
   matches/groupings from the cleaned data.
3. **Generate** ([scripts/generate.py](scripts/generate.py)) — render one
   HTML page per attendee into `/site`.

### Running end to end

```bash
pip install -r requirements.txt

python scripts/clean.py    --input data/raw_survey.csv --output data/clean_survey.csv
python scripts/match.py    --input data/clean_survey.csv --output data/matches.csv
python scripts/generate.py --input data/matches.csv --output-dir site/
```

Each script is a standalone CLI so any stage can be re-run independently
once its input exists.

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

GitHub Pages sites on free-tier repos are public if the repo is public,
regardless of how obscure the per-attendee URLs are. Before generating and
deploying real attendee pages, decide how this event's guest list and any
personal survey data should be handled — e.g. keeping the repo private
(GitHub Pro/Team/Enterprise support private-repo Pages), using unguessable
per-attendee slugs, and/or adding `noindex` meta tags to keep pages out of
search engines. `/data` is gitignored by default so raw and cleaned survey
exports are never committed.
