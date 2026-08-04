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
  <link rel="stylesheet" href="{assets}style.css">
  <link rel="icon" type="image/png" sizes="16x16" href="{assets}branding/favicon-16.png">
  <link rel="icon" type="image/png" sizes="32x32" href="{assets}branding/favicon-32.png">
  <link rel="icon" type="image/png" sizes="48x48" href="{assets}branding/favicon-48.png">
  <link rel="apple-touch-icon" href="{assets}branding/apple-touch-icon.png">
</head>
<body>
{banner}{hero}<main>
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
    """Renders the schedule as a single disclosure widget: collapsed by
    default (mobile), forced open via CSS at the desktop/tablet breakpoint
    where it becomes a right-rail panel instead. Same markup both ways —
    see .schedule-content / .schedule-toggle in style.css."""
    table = attendee.get("table")
    sessions = attendee.get("sessions") or []
    is_placeholder = table is None and not sessions

    if is_placeholder:
        body = "  <p>Coming closer to the event</p>\n"
    else:
        parts = []
        if table is not None:
            parts.append(f"  <p>You're seated at <strong>Table {table}</strong></p>\n")
        if sessions:
            parts.append("  <ul class=\"plain-list\">")
            parts.append("".join(f"<li>{esc(s)}</li>" for s in sessions))
            parts.append("</ul>\n")
        body = "".join(parts)

    section_class = "section schedule-panel" + (" section--placeholder" if is_placeholder else "")

    return "".join([
        f'<section class="{section_class}">\n',
        '  <h2><button type="button" class="schedule-toggle" aria-expanded="false" aria-controls="schedule-content">\n',
        "    Your schedule\n",
        '    <span class="toggle-icon" aria-hidden="true">▸</span>\n',
        "  </button></h2>\n",
        '  <div class="schedule-content" id="schedule-content">\n',
        body,
        "  </div>\n",
        "</section>\n",
    ])


SCHEDULE_TOGGLE_SCRIPT = """<script>
(function () {
  document.querySelectorAll(".schedule-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var expanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!expanded));
      document.getElementById(btn.getAttribute("aria-controls")).classList.toggle("is-open", !expanded);
    });
  });
})();
</script>
"""


def render_attendee_page(attendee: dict, demo: bool) -> str:
    """Layout: schedule comes first in source order (so it's the top
    section on mobile with no JS reordering needed), then the main
    column. .page-layout in style.css uses CSS grid-template-areas to
    place schedule as a right rail next to (not above) main at the
    tablet/desktop breakpoint — same markup both ways."""
    name = esc(attendee["full_name"])
    body = [
        PAGE_HEAD.format(
            title=f"{name} · UpLevel",
            assets="../../assets/",
            banner=DEMO_BANNER if demo else "",
            hero="",
        ),
        '<a class="back-link" href="../../lookbook/">← Back to lookbook</a>\n',
        '<p class="eyebrow">UpLevel Attendee</p>\n',
        f"<h1>{name}</h1>\n",
        role_tags_html(attendee["primary_role"], attendee["other_roles"], attendee.get("industries")),
        '\n<div class="page-layout">\n',
        '<aside class="schedule-area">\n',
        render_schedule_section(attendee),
        "</aside>\n",
        '<div class="main-area">\n',
        render_asks_offers_section(attendee),
        render_matches_section(attendee),
        "</div>\n",
        "</div>\n",
        SCHEDULE_TOGGLE_SCRIPT,
        PAGE_TAIL,
    ]
    return "".join(body)


AVATAR_PALETTE = [
    ("#2f5d50", "#ffffff"),
    ("#33478a", "#ffffff"),
    ("#8a5a00", "#ffffff"),
    ("#7a3b69", "#ffffff"),
    ("#3b6e8f", "#ffffff"),
    ("#6b6b6b", "#ffffff"),
]


def initials(full_name: str) -> str:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def avatar_html(attendee: dict, size: int = 48) -> str:
    """Real photo if attendee has a photo_url (none do yet — no field
    collects this today); otherwise a generated initials avatar, so cards
    look finished either way with no external image requests."""
    name = attendee["full_name"]
    photo_url = attendee.get("photo_url")
    if photo_url:
        return f'<img class="avatar" src="{esc(photo_url)}" alt="{esc(name)}" width="{size}" height="{size}" loading="lazy">'

    idx = sum(ord(c) for c in name) % len(AVATAR_PALETTE)
    bg, fg = AVATAR_PALETTE[idx]
    return (
        f'<svg class="avatar" width="{size}" height="{size}" viewBox="0 0 48 48" role="img" aria-label="{esc(name)}">'
        f'<rect width="48" height="48" rx="24" fill="{bg}"/>'
        f'<text x="24" y="25" text-anchor="middle" dominant-baseline="central" '
        f'font-family="system-ui, sans-serif" font-size="18" font-weight="600" fill="{fg}">{esc(initials(name))}</text>'
        "</svg>"
    )


def render_attendee_card(attendee: dict) -> str:
    slug = attendee["slug"]
    name = esc(attendee["full_name"])
    primary_role = attendee["primary_role"] or ""
    other_roles = attendee["other_roles"]
    # Only the first industry shows on the card front — enough to scan at a
    # glance without cluttering the card; the full list is on their page.
    primary_industry = (attendee.get("industries") or [None])[0]

    linkedin_html = ""
    if attendee["linkedin"]:
        linkedin_html = (
            f'<a class="linkedin-link" href="{esc(attendee["linkedin"])}" '
            f'target="_blank" rel="noopener noreferrer">LinkedIn ↗</a>'
        )

    return f"""<article class="attendee-card"
  data-primary-role="{esc(primary_role)}"
  data-other-roles="{esc(ROLE_TAG_DELIMITER.join(other_roles))}">
  <div class="attendee-card-header">
    {avatar_html(attendee)}
    <div class="attendee-card-heading">
      <h3><a href="../uplevel/{slug}/">{name}</a></h3>
      {role_tags_html(primary_role or None, other_roles, [primary_industry] if primary_industry else None)}
    </div>
  </div>
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
  var checkboxes = Array.prototype.slice.call(document.querySelectorAll('input[data-filter-group]'));
  var clearBtn = document.getElementById("clear-filters");

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
    clearBtn.hidden = (primary.length === 0 && other.length === 0);
  }

  checkboxes.forEach(function (box) {
    box.addEventListener("change", applyFilters);
  });

  clearBtn.addEventListener("click", function () {
    checkboxes.forEach(function (box) { box.checked = false; });
    applyFilters();
  });

  applyFilters();
})();
</script>
"""

    hero = (
        '<img class="hero-banner" src="../assets/branding/uplevel-rectangle.png" '
        'alt="UpLevel — Women Investors &amp; Founders Moving the Needle Together, '
        'Boston skyline">\n'
    )

    return "".join([
        PAGE_HEAD.format(
            title="UpLevel Lookbook",
            assets="../assets/",
            banner=DEMO_BANNER if demo else "",
            hero=hero,
        ),
        "<h1>Lookbook</h1>\n",
        '<p class="eyebrow">All UpLevel attendees</p>\n',
        '<div class="filter-bar">\n',
        '  <div class="filter-bar-header">\n',
        "    <span>Filters</span>\n",
        '    <button type="button" id="clear-filters" class="clear-filters" hidden>Clear filters</button>\n',
        "  </div>\n",
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
