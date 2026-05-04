#!/usr/bin/env python3
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"


def read(path):
    return path.read_text(encoding="utf-8")


def frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    _, raw, body = text.split("---", 2)
    meta = {}
    for line in raw.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta, body.lstrip()


def render_liquid_basics(template, page, content):
    html = template
    html = html.replace("{% include header.html %}", read(ROOT / "_includes" / "header.html"))
    html = html.replace("{% include footer.html %}", read(ROOT / "_includes" / "footer.html"))
    html = html.replace("{{ content }}", content)
    html = re.sub(r"\{\% if page.description \%\}(.*?)\{\% endif \%\}", lambda m: m.group(1) if page.get("description") else "", html)
    replacements = {
        "{{ page.title | default: site.title }}": page.get("title", "Stratus Eye"),
        "{{ page.title | default: site.title | escape }}": page.get("title", "Stratus Eye"),
        "{{ page.description | escape }}": page.get("description", ""),
        "{{ page.url | absolute_url }}": "https://stratuseye.com" + page.get("permalink", "/"),
        "{{ '/assets/css/webflow.css' | relative_url }}": "/assets/css/webflow.css",
        "{{ '/assets/css/site.css' | relative_url }}": "/assets/css/site.css",
        "{{ '/assets/js/site.js' | relative_url }}": "/assets/js/site.js",
        "{{ '/assets/vendor/69d305208ce6a8c0cbe83de9_Stratus-Eye_Final_20102022_white-bg-131bde100a.png' | relative_url }}": "/assets/vendor/69d305208ce6a8c0cbe83de9_Stratus-Eye_Final_20102022_white-bg-131bde100a.png",
        "{{ '/assets/vendor/69d3054f2ea60beeaaf02583_Stratus-Eye_Final_25102022_Black-bg-icon-492bb22aa6.png' | relative_url }}": "/assets/vendor/69d3054f2ea60beeaaf02583_Stratus-Eye_Final_25102022_Black-bg-icon-492bb22aa6.png",
    }
    for src, dest in replacements.items():
        html = html.replace(src, dest)
    return html


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    layout = read(ROOT / "_layouts" / "default.html")
    for path in ROOT.glob("*.html"):
        meta, content = frontmatter(read(path))
        meta["permalink"] = meta.get("permalink", f"/{path.name}")
        output = SITE / ("index.html" if meta["permalink"] == "/" else meta["permalink"].lstrip("/"))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_liquid_basics(layout, meta, content), encoding="utf-8")
    for name in ["assets", "robots.txt"]:
        src = ROOT / name
        dest = SITE / name
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copyfile(src, dest)


if __name__ == "__main__":
    main()
