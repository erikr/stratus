#!/usr/bin/env python3
import hashlib
import html
import re
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/Users/erik/Downloads/stratuseye.com")
CSS_URL = "https://cdn.prod.website-files.com/691a69efa40eff57e0094efb/css/stratus-eye.webflow.shared.1b9e063d3.min.css"
ASSET_DIR = ROOT / "assets" / "vendor"
CSS_DIR = ROOT / "assets" / "css"
JS_DIR = ROOT / "assets" / "js"


def read(path):
    return path.read_text(encoding="utf-8")


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def asset_name(url):
    parsed = urllib.parse.urlparse(url)
    raw_name = urllib.parse.unquote(Path(parsed.path).name)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", raw_name).strip("-")
    if not safe:
        safe = "asset"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    stem = Path(safe).stem
    suffix = Path(safe).suffix
    return f"{stem}-{digest}{suffix}"


def extract_urls(text):
    urls = set()
    for match in re.finditer(r'(?:src|href)="(https://cdn\.prod\.website-files\.com/[^"]+)"', text):
        url = html.unescape(match.group(1))
        if "/js/" not in url and "/css/" not in url:
            urls.add(url)
    for match in re.finditer(r"srcset=\"([^\"]+)\"", text):
        for url in re.findall(r"https://cdn\.prod\.website-files\.com/[^\s,]+", html.unescape(match.group(1))):
            if "/js/" not in url and "/css/" not in url:
                urls.add(url)
    for match in re.finditer(r"url\((['\"]?)(https://cdn\.prod\.website-files\.com/.+?)\1\)", text):
        url = html.unescape(match.group(0)).rstrip(",")
        url = html.unescape(match.group(2))
        if "/js/" not in url and "/css/" not in url:
            urls.add(url)
    return urls


def download_assets(urls):
    mapping = {}
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for url in sorted(urls):
        name = asset_name(url)
        dest = ASSET_DIR / name
        mapping[url] = f"assets/vendor/{name}"
        if dest.exists():
            continue
        try:
            dest.write_bytes(fetch(url))
        except Exception as exc:
            print(f"warn: failed to download {url}: {exc}", file=sys.stderr)
    return mapping


def rewrite_urls(text, mapping):
    # Longer URLs first so srcset variants do not partially rewrite each other.
    for url in sorted(mapping, key=len, reverse=True):
        text = text.replace(url, mapping[url])
        text = text.replace(html.escape(url, quote=True), mapping[url])
    text = re.sub(r'href="conditions/([^"]+)"', r'href="\1"', text)
    text = re.sub(r'href="\.\./([^"]+)"', r'href="\1"', text)
    text = re.sub(r'href="others/(hipaa-notice|privacy-policy)\.html"', r'href="\1.html"', text)
    text = re.sub(r'href="/others/(hipaa-notice|privacy-policy)\.html"', r'href="\1.html"', text)
    text = re.sub(r'href="/(index|contact|dr-tran|pricing-and-financing|cataract-surgery-suwanee-ga|dry-eye|glaucoma|macular-degeneration-suwanee-ga|diabetic-retinopathy-suwanee-ga|hipaa-notice|privacy-policy)\.html"', r'href="\1.html"', text)
    text = text.replace('href="index.html#"', 'href="contact.html"')
    text = text.replace('href="/index.html#"', 'href="contact.html"')
    return text


def metadata(doc, filename):
    title = re.search(r"<title>(.*?)</title>", doc, re.S)
    desc = re.search(r'<meta\s+content="([^"]*)"\s+name="description"', doc, re.S)
    return {
        "title": html.unescape(title.group(1).strip()) if title else "Stratus Eye",
        "description": html.unescape(desc.group(1).strip()) if desc else "",
        "permalink": "/" if filename == "index.html" else f"/{filename}",
    }


def body_parts(doc):
    body = re.search(r"<body[^>]*>(.*)</body>", doc, re.S).group(1)
    nav_match = re.search(r'(<div[^>]+role="banner"[^>]*>.*?</div>)<section', body, re.S)
    if not nav_match:
        raise RuntimeError("could not locate navbar")
    nav = nav_match.group(1)
    footer_match = re.search(r"(<footer\b.*?</footer>)", body, re.S)
    footer = footer_match.group(1) if footer_match else ""
    content_start = nav_match.end(1)
    content_end = footer_match.start(1) if footer_match else len(body)
    content = body[content_start:content_end]
    content = re.sub(r"<script\b.*?</script>", "", content, flags=re.S)
    return nav, content, footer


def strip_active_classes(fragment):
    fragment = fragment.replace(' aria-current="page"', "")
    fragment = fragment.replace(" w--current", "")
    return fragment


def yaml_escape(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    CSS_DIR.mkdir(parents=True, exist_ok=True)
    JS_DIR.mkdir(parents=True, exist_ok=True)
    raw_css = fetch(CSS_URL).decode("utf-8")
    docs = {path.name: read(path) for path in sorted(SOURCE.glob("*.html"))}
    all_urls = set(extract_urls(raw_css))
    for doc in docs.values():
        all_urls.update(extract_urls(doc))
    mapping = download_assets(all_urls)
    css = rewrite_urls(raw_css, mapping)
    write(CSS_DIR / "webflow.css", css)

    nav, _, footer = body_parts(docs["index.html"])
    write(ROOT / "_includes" / "header.html", rewrite_urls(strip_active_classes(nav), mapping))
    write(ROOT / "_includes" / "footer.html", rewrite_urls(strip_active_classes(footer), mapping))

    for filename, doc in docs.items():
        meta = metadata(doc, filename)
        _, content, _ = body_parts(doc)
        content = rewrite_urls(content, mapping)
        content = content.replace(' style="opacity:0"', '')
        content = re.sub(r"\s*<script\b.*?</script>\s*", "", content, flags=re.S)
        front = [
            "---",
            "layout: default",
            f"title: {yaml_escape(meta['title'])}",
            f"description: {yaml_escape(meta['description'])}",
            f"permalink: {meta['permalink']}",
            "---",
            "",
        ]
        write(ROOT / filename, "\n".join(front) + content + "\n")

    shutil.copyfile(SOURCE / "robots.txt", ROOT / "robots.txt")


if __name__ == "__main__":
    main()
