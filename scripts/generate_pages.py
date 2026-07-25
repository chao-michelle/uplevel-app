#!/usr/bin/env python3
"""Generate one static HTML page per attendee, plus a filterable lookbook page.

Usage:
    python scripts/generate_pages.py --input data/attendees.json --output-dir site/
"""
from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

ROLE_TAG_DELIMITER = "|"

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
<main>
"""

PAGE_TAIL = """</main>
</body>
</html>
"""


def esc(value: str | None) -> str:
    return html.escape(value) if value else ""


def role_tags_html(primary_role: str | None, other_roles: list) -> str:
    items = []
    if primary_role:
        items.append(f'<li class="tag tag--primary">{esc(primary_role)}</li>')
    for role in other_roles:
        items.append(f'<li class="tag">{esc(role)}</li>')
    if not items:
        return '<p class="section--placeholder"><em>No role information provided.</em></p>'
    return f'<ul class="tag-list">{"".join(items)}</ul>'


def render_attendee_page(attendee: dict) -> str:
    name = esc(attendee["full_name"])
    body = [
        PAGE_HEAD.format(title=f"{name} · UpLevel", css_path="../../assets/style.css"),
        '<a class="back-link" href="../../lookbook/">← Back to lookbook</a>\n',
        '<p class="eyebrow">UpLevel Attendee</p>\n',
        f"<h1>{name}</h1>\n",
        role_tags_html(attendee["primary_role"], attendee["other_roles"]),
        '\n<section class="section section--placeholder">\n',
        "  <h2>Your matches</h2>\n",
        "  <p>Coming after Part 2 data</p>\n",
        "</section>\n",
        '<section class="section section--placeholder">\n',
        "  <h2>Your schedule</h2>\n",
        "  <p>Coming closer to the event</p>\n",
        "</section>\n",
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


def render_lookbook_page(attendees: list) -> str:
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
        PAGE_HEAD.format(title="UpLevel Lookbook", css_path="../assets/style.css"),
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
    parser.add_argument("--input", default="data/attendees.json", help="Path to cleaned attendees JSON")
    parser.add_argument("--output-dir", default="site", help="Site root directory to write generated pages into")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        attendees_by_slug = json.load(f)

    attendees = sorted(attendees_by_slug.values(), key=lambda a: a["full_name"])

    site_root = Path(args.output_dir)
    uplevel_dir = site_root / "uplevel"
    lookbook_dir = site_root / "lookbook"

    shutil.rmtree(uplevel_dir, ignore_errors=True)
    shutil.rmtree(lookbook_dir, ignore_errors=True)
    uplevel_dir.mkdir(parents=True, exist_ok=True)
    lookbook_dir.mkdir(parents=True, exist_ok=True)

    for attendee in attendees:
        page_dir = uplevel_dir / attendee["slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(render_attendee_page(attendee), encoding="utf-8")

    (lookbook_dir / "index.html").write_text(render_lookbook_page(attendees), encoding="utf-8")

    print(f"Generated {len(attendees)} attendee page(s) under {uplevel_dir}/")
    print(f"Generated lookbook at {lookbook_dir}/index.html")


if __name__ == "__main__":
    main()
