"""Checks the site against the rules in AGENTS.md. Run by CI on every push.

    python3 tools/check.py

Standard library only. Fails (exit 1) on:
- inline scripts, <style> blocks, style= or on*= attributes (they would
  break the strict Content-Security-Policy);
- scripts, stylesheets, images or fonts from another domain;
- links to other sites without target="_blank" and rel="noopener";
- local links or files that do not exist, and #fragments with no such id;
- a page whose Portuguese and English twins (data-lang="pt"/"en") do not
  pair up, an English twin not hidden, a page without data-title-pt/-en,
  or an image with alt text but no data-alt-pt/-en.
"""

import html.parser
import sys
from pathlib import Path
from urllib.parse import urlsplit

SITE = Path(__file__).resolve().parent.parent / "site"


class Page(html.parser.HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = set()
        self.refs = []  # (tag, attribute, value, attrs)
        self.errors = []
        self.lang = {"pt": 0, "en": 0}
        self.in_script = False
        self.script_text = ""
        self.html_attrs = {}

    def error(self, msg):
        self.errors.append(f"{self.path.name}:{self.getpos()[0]}: {msg}")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html_attrs = a
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "style":
            self.error("<style> block; use a file in assets/")
        if "style" in a:
            self.error(f"style= attribute on <{tag}>")
        for name in a:
            if name.startswith("on"):
                self.error(f"{name}= attribute on <{tag}>")
        if tag == "script":
            if "src" not in a:
                self.error("inline <script>; use a file in assets/")
            self.in_script = True
        lang = a.get("data-lang")
        if lang in self.lang:
            self.lang[lang] += 1
            if lang == "en" and "hidden" not in a:
                self.error(f'<{tag} data-lang="en"> without hidden')
        if tag == "img" and a.get("alt") and not ("data-alt-pt" in a and "data-alt-en" in a):
            self.error(f"image {a.get('src')} has alt text but no data-alt-pt/-en")
        for attr in ("href", "src"):
            if a.get(attr):
                self.refs.append((tag, attr, a[attr], a))

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False


def check():
    pages = {p.name: p for p in sorted(SITE.glob("*.html"))}
    parsed = {}
    errors = []
    for name, path in pages.items():
        page = Page(path)
        page.feed(path.read_text(encoding="utf-8"))
        page.close()
        parsed[name] = page
        errors += page.errors
        if page.lang["pt"] != page.lang["en"]:
            errors.append(
                f"{name}: {page.lang['pt']} Portuguese texts but {page.lang['en']} English ones"
            )
        if not ("data-title-pt" in page.html_attrs and "data-title-en" in page.html_attrs):
            errors.append(f"{name}: <html> without data-title-pt/-en")

    for name, page in parsed.items():
        for tag, attr, value, attrs in page.refs:
            url = urlsplit(value)
            where = f"{name}: <{tag} {attr}={value!r}>"
            if url.scheme in ("http", "https"):
                if tag != "a":
                    errors.append(f"{where} loads from another domain")
                elif attrs.get("target") != "_blank" or "noopener" not in attrs.get("rel", ""):
                    errors.append(f'{where} needs target="_blank" rel="noopener"')
                continue
            if url.scheme in ("mailto", "tel") or value.startswith("//"):
                if value.startswith("//"):
                    errors.append(f"{where} loads from another domain")
                continue
            target = name if not url.path else url.path
            file = (SITE / target).resolve()
            if not file.is_relative_to(SITE) or not file.exists():
                errors.append(f"{where} points to a missing file")
                continue
            if url.fragment and file.suffix == ".html":
                ids = parsed[file.name].ids if file.name in parsed else set()
                if url.fragment not in ids:
                    errors.append(f"{where} points to a missing #{url.fragment}")

    # CSS may load fonts and images too: only local ones.
    for css in SITE.glob("assets/*.css"):
        text = css.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), 1):
            if "url(" in line and ("http:" in line or "https:" in line or "url(//" in line):
                errors.append(f"{css.name}:{line_no}: url() from another domain")

    return pages, errors


def main():
    pages, errors = check()
    for e in errors:
        print(e, file=sys.stderr)
    if errors:
        print(f"{len(errors)} problem(s)", file=sys.stderr)
        return 1
    print(f"ok: {len(pages)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
