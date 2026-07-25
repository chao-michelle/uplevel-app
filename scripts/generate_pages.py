#!/usr/bin/env python3
"""Generate one static HTML page per attendee, plus a filterable lookbook page.

If an attendee record includes "matches" (from match.py) and/or "table"
(from assign_tables.py), those render as real content. Otherwise the page
falls back to the original "coming soon" placeholders, so this script
works unchanged for real attendees.json (no Part 2 data yet) and for an
enriched demo dataset alike.

Usage:
    python scripts/generate_pages.py --input data/attendees.json --output-dir site/
    python scripts/generate_pages.py --input data/demo-tables.json --output-dir site-demo/ --demo-banner
"""
from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

ROLE_TAG_DELIMITER = "|"

DEMO_BANNER = (
    '<div class="demo-banner">⚠ DEMO DATA — internal preview only, '
    "not real attendees</div>\n"
)

PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex">
  <title>{title}</title>
  <link rel="stylesheet" href="{css_path}">
</head>
<body>
{banner}<main>
"""

PAGE_TAIL = """</main>
</body>
</html>
"""


def esc(value: str | None) -> str:
    return html.escape(value) if value else ""


def role_tags_html(primary_role: str | None, other_roles: list, industries: list | None = None) -> str:
    items = []
    if primary_role:
        items.append(f'<li class="tag tag--primary">{esc(primary_role)}</li>')
    for role in other_roles:
        items.append(f'<li class="tag">{esc(role)}</li>')
    for industry in industries or []:
        items.append(f'<li class="tag tag--industry">{esc(industry)}</li>')
    if not items:
        return '<p class="section--placeholder"><em>No role information provided.</em></p>'
    return f'<ul class="tag-list">{"".join(items)}</ul>'


def render_asks_offers_section(attendee: dict) -> str:
    asks = attendee.get("asks") or []
    offers = attendee.get("offers") or []
    if not asks and not offers:
        return ""

    def list_html(items):
        return "".join(f"<li>{esc(item)}</li>" for item in items)

    return "".join([
        '<section class="section">\n',
        "  <h2>Asks &amp; Offers</h2>\n",
        '  <p class="eyebrow">Looking for</p>\n',
        f'  <ul class="plain-list">{list_html(asks)}</ul>\n',
        '  <p class="eyebrow">Can offer</p>\n',
        f'  <ul class="plain-list">{list_html(offers)}</ul>\n',
        "</section>\n",
    ])


def render_matches_section(attendee: dict) -> str:
    matches = attendee.get("matches")
    if not matches:
        return "".join([
            '<section class="section section--placeholder">\n',
            "  <h2>Your matches</h2>\n",
            "  <p>Coming after Part 2 data</p>\n",
            "</section>\n",
        ])

    cards = []
    for m in matches:
        cards.append("".join([
            '<article class="match-card">\n',
            f'  <h3><a href="../{esc(m["slug"])}/">{esc(m["full_name"])}</a></h3>\n',
            f'  <p class="match-reason">Their offer: &ldquo;{esc(m["their_offer"])}&rdquo;'
            f' matches your ask: &ldquo;{esc(m["your_ask"])}&rdquo;</p>\n',
            '  <ul class="tag-list">',
            "".join(f'<li class="tag">{esc(k)}</li>' for k in m["shared_keywords"]),
            "</ul>\n",
            "</article>\n",
        ]))

    return "".join([
        '<section class="section">\n',
        "  <h2>Your matches</h2>\n",
        *cards,
        "</section>\n",
    ])


def render_schedule_section(attendee: dict) -> str:
    table = attendee.get("table")
    sessions = attendee.get("sessions") or []
    if table is None and not sessions:
        return "".join([
            '<section class="section section--placeholder">\n',
            "  <h2>Your schedule</h2>\n",
            "  <p>Coming closer to the event</p>\n",
            "</section>\n",
        ])

    parts = ['<section class="section">\n', "  <h2>Your schedule</h2>\n"]
    if table is not None:
        parts.append(f"  <p>You're seated at <strong>Table {table}</strong></p>\n")
    if sessions:
        parts.append("  <ul class=\"plain-list\">")
        parts.append("".join(f"<li>{esc(s)}</li>" for s in sessions))
        parts.append("</ul>\n")
    parts.append("</section>\n")
    return "".join(parts)


def render_attendee_page(attendee: dict, demo: bool) -> str:
    name = esc(attendee["full_name"])
    body = [
        PAGE_HEAD.format(
            title=f"{name} · UpLevel",
            css_path="../../assets/style.css",
            banner=DEMO_BANNER if demo else "",
        ),
        '<a class="back-link" href="../../lookbook/">← Back to lookbook</a>\n',
        '<p class="eyebrow">UpLevel Attendee</p>\n',
        f"<h1>{name}</h1>\n",
        role_tags_html(attendee["primary_role"], attendee["other_roles"], attendee.get("industries")),
        "\n",
        render_asks_offers_section(attendee),
        render_matches_section(attendee),
        render_schedule_section(attendee),
        PAGE_TAIL,
    ]
    return "".join(body)


def render_attendee_card(attendee: dict) -> str:
    slug = attendee["slug"]
    name = esc(attendee["full_name"])
    primary_role = attendee["primary_role"] or ""
    other_roles = attendee["other_roles"]

    linkedin_html = ""
    if attendee["linkedin"]:
        linkedin_html = (
            f'<a class="linkedin-link" href="{esc(attendee["linkedin"])}" '
            f'target="_blank" rel="noopener noreferrer">LinkedIn ↗</a>'
        )

    return f"""<article class="attendee-card"
  data-primary-role="{esc(primary_role)}"
  data-other-roles="{esc(ROLE_TAG_DELIMITER.join(other_roles))}">
  <h3><a href="../uplevel/{slug}/">{name}</a></h3>
  {role_tags_html(primary_role or None, other_roles)}
  {linkedin_html}
</article>"""


def render_lookbook_page(attendees: list, demo: bool) -> str:
    primary_roles = sorted({a["primary_role"] for a in attendees if a["primary_role"]})
    other_roles = sorted({role for a in attendees for role in a["other_roles"]})

    primary_filter_options = "\n".join(
        f'''      <label class="filter-option">
        <input type="checkbox" data-filter-group="primary-role" value="{esc(role)}">
        {esc(role)}
      </label>'''
        for role in primary_roles
    )
    other_filter_options = "\n".join(
        f'''      <label class="filter-option">
        <input type="checkbox" data-filter-group="other-role" value="{esc(role)}">
        {esc(role)}
      </label>'''
        for role in other_roles
    )

    cards = "\n".join(render_attendee_card(a) for a in attendees)

    script = """<script>
(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll(".attendee-card"));
  var countEl = document.getElementById("result-count");

  function selectedValues(group) {
    var boxes = document.querySelectorAll('input[data-filter-group="' + group + '"]:checked');
    return Array.prototype.map.call(boxes, function (b) { return b.value; });
  }

  function applyFilters() {
    var primary = selectedValues("primary-role");
    var other = selectedValues("other-role");
    var visible = 0;

    cards.forEach(function (card) {
      var cardPrimary = card.getAttribute("data-primary-role") || "";
      var cardOther = (card.getAttribute("data-other-roles") || "").split("|").filter(Boolean);

      var matchesPrimary = primary.length === 0 || primary.indexOf(cardPrimary) !== -1;
      var matchesOther = other.length === 0 || other.some(function (r) {
        return cardOther.indexOf(r) !== -1;
      });

      var show = matchesPrimary && matchesOther;
      card.hidden = !show;
      if (show) visible++;
    });

    countEl.textContent = visible + " of " + cards.length + " attendees";
  }

  document.querySelectorAll('input[data-filter-group]').forEach(function (box) {
    box.addEventListener("change", applyFilters);
  });

  applyFilters();
})();
</script>
"""

    return "".join([
        PAGE_HEAD.format(title="UpLevel Lookbook", css_path="../assets/style.css", banner=DEMO_BANNER if demo else ""),
        "<h1>Lookbook</h1>\n",
        '<p class="eyebrow">All UpLevel attendees</p>\n',
        '<div class="filter-bar">\n',
        '  <div class="filter-group">\n',
        '    <span class="filter-group-label">Primary role</span>\n',
        '    <div class="filter-options">\n',
        primary_filter_options + "\n",
        "    </div>\n",
        "  </div>\n",
        '  <div class="filter-group">\n',
        '    <span class="filter-group-label">Other roles</span>\n',
        '    <div class="filter-options">\n',
        other_filter_options + "\n",
        "    </div>\n",
        "  </div>\n",
        "</div>\n",
        f'<p class="result-count" id="result-count">{len(attendees)} of {len(attendees)} attendees</p>\n',
        '<div class="attendee-grid">\n',
        cards + "\n",
        "</div>\n",
        script,
        PAGE_TAIL,
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/attendees.json", help="Path to attendees JSON (optionally enriched with matches/table)")
    parser.add_argument("--output-dir", default="site", help="Site root directory to write generated pages into")
    parser.add_argument("--assets-source", default="site/assets", help="Directory to copy shared assets (CSS) from")
    parser.add_argument("--demo-banner", action="store_true", help="Add a visible 'demo data' banner to every generated page")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        attendees_by_slug = json.load(f)

    attendees = sorted(attendees_by_slug.values(), key=lambda a: a["full_name"])

    site_root = Path(args.output_dir)
    uplevel_dir = site_root / "uplevel"
    lookbook_dir = site_root / "lookbook"
    assets_dir = site_root / "assets"

    shutil.rmtree(uplevel_dir, ignore_errors=True)
    shutil.rmtree(lookbook_dir, ignore_errors=True)
    uplevel_dir.mkdir(parents=True, exist_ok=True)
    lookbook_dir.mkdir(parents=True, exist_ok=True)

    assets_source = Path(args.assets_source)
    if assets_source.resolve() != assets_dir.resolve():
        shutil.copytree(assets_source, assets_dir, dirs_exist_ok=True)

    for attendee in attendees:
        page_dir = uplevel_dir / attendee["slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(render_attendee_page(attendee, args.demo_banner), encoding="utf-8")

    (lookbook_dir / "index.html").write_text(render_lookbook_page(attendees, args.demo_banner), encoding="utf-8")

    print(f"Generated {len(attendees)} attendee page(s) under {uplevel_dir}/")
    print(f"Generated lookbook at {lookbook_dir}/index.html")


if __name__ == "__main__":
    main()
