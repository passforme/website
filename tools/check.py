"""Checks the site against the rules in AGENTS.md. Run by CI on every push.

    python3 tools/check.py

Standard library only. Fails (exit 1) on:
- in src/, the bilingual sources: language twins (data-lang="pt"/"en")
  that do not pair up, a twin in the body not hidden, a <title> without
  data-lang, or an image with alt text but no data-alt-pt/-en;
- in site/, the pages tools/pages.py writes from them, one language each:
  a page stale against its source, or one still carrying data-lang;
  inline scripts, <style> blocks, style= or on*= attributes (they would
  break the strict Content-Security-Policy); scripts, stylesheets, images
  or fonts from another domain; links to other sites without
  target="_blank" and rel="noopener"; local links or files that do not
  exist, and #fragments with no such id; a page without its canonical
  URL and hreflang alternates (https://passforme.com/ plus the path
  without .html, as Cloudflare Pages serves it), a 404.html that is not
  noindex, a missing robots.txt, or a sitemap.xml that does not list
  every page.
"""

import html.parser
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "tools"))
import pages as generator  # noqa: E402

HEAD_TAGS = {"title", "meta", "link"}  # twins here need no hidden


class Page(html.parser.HTMLParser):
    def __init__(self, path, root):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.bilingual = root == SRC
        self.rel = path.relative_to(root).as_posix()
        self.ids = set()
        self.refs = []  # (tag, attribute, value, attrs)
        self.errors = []
        self.lang = {"pt": 0, "en": 0}
        self.html_lang = None
        self.canonical = []
        self.alternates = {}
        self.robots = None
        self.titles_without_lang = 0

    def error(self, msg):
        self.errors.append(f"{self.rel}:{self.getpos()[0]}: {msg}")

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html_lang = a.get("lang")
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "style":
            self.error("<style> block; use a file in assets/")
        if "style" in a:
            self.error(f"style= attribute on <{tag}>")
        for name in a:
            if name.startswith("on"):
                self.error(f"{name}= attribute on <{tag}>")
        if tag == "script" and "src" not in a:
            self.error("inline <script>; use a file in assets/")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical.append(a.get("href", ""))
        if tag == "link" and a.get("rel") == "alternate" and "hreflang" in a:
            self.alternates[a["hreflang"]] = a.get("href", "")
        if tag == "meta" and a.get("name") == "robots":
            self.robots = a.get("content", "")
        if tag == "title" and "data-lang" not in a:
            self.titles_without_lang += 1
        lang = a.get("data-lang")
        if lang in self.lang:
            self.lang[lang] += 1
            if lang == "en" and "hidden" not in a and tag not in HEAD_TAGS:
                self.error(f'<{tag} data-lang="en"> without hidden')
        if self.bilingual and tag == "img" and a.get("alt") and not ("data-alt-pt" in a and "data-alt-en" in a):
            self.error(f"image {a.get('src')} has alt text but no data-alt-pt/-en")
        for attr in ("href", "src"):
            if a.get(attr):
                self.refs.append((tag, attr, a[attr], a))


def parse(path, root):
    page = Page(path, root)
    page.feed(path.read_text(encoding="utf-8"))
    page.close()
    return page


def check():
    errors = []

    # The sources: both languages, paired.
    sources = sorted(SRC.glob("*.html"))
    for path in sources:
        page = parse(path, SRC)
        errors += page.errors
        if page.lang["pt"] != page.lang["en"]:
            errors.append(f"{page.rel}: {page.lang['pt']} Portuguese texts but {page.lang['en']} English ones")
        if page.titles_without_lang:
            errors.append(f"{page.rel}: <title> without data-lang (one per language, please)")

    # The generated pages: current, one language each, serving as they are.
    for rel in generator.stale():
        errors.append(f"site/{rel} is stale: run python3 tools/pages.py")
    parsed = {}
    for lang, info in generator.LANGS.items():
        for path in sorted(SITE.glob(info["dir"] + "*.html")):
          page = parse(path, SITE)
          parsed[path.resolve()] = page
          errors += page.errors
          if page.lang["pt"] or page.lang["en"]:
              errors.append(f"{page.rel}: data-lang left in a generated page")
          name = path.name
          if page.html_lang != generator.LANGS[lang]["html"]:
              errors.append(f'{page.rel}: <html lang="{page.html_lang}"> for a {lang} page')
          if name == "404.html":
              if "noindex" not in (page.robots or ""):
                  errors.append(f'{page.rel}: needs <meta name="robots" content="noindex">')
              continue
          twins = {l: generator.LANGS[l]["dir"] + name for l in generator.LANGS}
          canonical = generator.clean_url(page.rel)
          if page.canonical != [canonical]:
              errors.append(f'{page.rel}: needs exactly one <link rel="canonical" href="{canonical}">')
          expected = {generator.LANGS[l]["hreflang"]: generator.clean_url(t) for l, t in twins.items()}
          expected["x-default"] = generator.clean_url(twins[generator.DEFAULT])
          if page.alternates != expected:
              errors.append(f"{page.rel}: hreflang alternates should be {expected}")

    for page in parsed.values():
        for tag, attr, value, attrs in page.refs:
            url = urlsplit(value)
            where = f"{page.rel}: <{tag} {attr}={value!r}>"
            if url.scheme in ("http", "https"):
                if tag == "link" and attrs.get("rel") in ("canonical", "alternate"):
                    continue  # names a page, loads nothing
                if tag != "a":
                    errors.append(f"{where} loads from another domain")
                elif attrs.get("target") != "_blank" or "noopener" not in attrs.get("rel", ""):
                    errors.append(f'{where} needs target="_blank" rel="noopener"')
                continue
            if url.scheme in ("mailto", "tel") or value.startswith("//"):
                if value.startswith("//"):
                    errors.append(f"{where} loads from another domain")
                continue
            file = (page.path.parent / url.path).resolve() if url.path else page.path.resolve()
            if not file.is_relative_to(SITE) or not file.exists():
                errors.append(f"{where} points to a missing file")
                continue
            if url.fragment and file.suffix == ".html":
                ids = parsed[file].ids if file in parsed else set()
                if url.fragment not in ids:
                    errors.append(f"{where} points to a missing #{url.fragment}")

    # CSS may load fonts and images too: only local ones.
    for css in SITE.glob("assets/*.css"):
        for line_no, line in enumerate(css.read_text(encoding="utf-8").splitlines(), 1):
            if "url(" in line and ("http:" in line or "https:" in line or "url(//" in line):
                errors.append(f"assets/{css.name}:{line_no}: url() from another domain")

    if not (SITE / "404.html").exists():
        errors.append("site/404.html is missing (without it, Cloudflare Pages serves the home for every unknown path)")
    if not (SITE / "robots.txt").exists():
        errors.append("site/robots.txt is missing")
    sitemap = SITE / "sitemap.xml"
    if not sitemap.exists():
        errors.append("site/sitemap.xml is missing")
    else:
        listed = sitemap.read_text(encoding="utf-8")
        for page in parsed.values():
            for url in page.canonical:
                if f"<loc>{url}</loc>" not in listed:
                    errors.append(f"site/sitemap.xml does not list {url}")

    return len(sources), len(parsed), errors


def main():
    sources, generated, errors = check()
    for e in errors:
        print(e, file=sys.stderr)
    if errors:
        print(f"{len(errors)} problem(s)", file=sys.stderr)
        return 1
    print(f"ok: {sources} sources, {generated} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
