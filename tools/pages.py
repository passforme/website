"""Writes the site's pages, one per language, from the bilingual sources.

    python3 tools/pages.py          # site/*.html, site/pt/*.html, site/sitemap.xml
    python3 tools/pages.py --check  # exit 1 if any of them is stale (tools/check.py runs it)

A source in src/ holds every language at once: an element with
data-lang="pt" next to its twin with data-lang="en" (hidden, in the body),
titles and meta tags included, and an image's alt text in data-alt-pt and
data-alt-en. English pages are written to site/ and Portuguese ones to
site/pt/, each keeping only its own language, with <html lang>, the
canonical URL, the hreflang alternates, the Open Graph locale and the
language switch (the empty <nav class="langs">) filled in. In site/pt/,
links to shared files (assets, brand, favicon) get a ../ prefix while links
between pages stay within the language. English ids and anchors written as
name-en in a source, to be unique while both languages share a file, lose
the suffix. Standard library only.
"""

import html.parser
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SITE = ROOT / "site"
ORIGIN = "https://passforme.com/"
LANGS = {
    "en": {"dir": "", "html": "en", "locale": "en_US", "hreflang": "en", "label": "EN", "switch": "Language"},
    "pt": {"dir": "pt/", "html": "pt-BR", "locale": "pt_BR", "hreflang": "pt-BR", "label": "PT", "switch": "Idioma"},
}
DEFAULT = "en"  # x-default: what a visitor of no known language gets
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SHARED = ("href", "src")


def clean_url(rel):
    """The URL Cloudflare Pages serves a file at: no index.html, no .html."""
    if rel.endswith("index.html"):
        rel = rel[: -len("index.html")]
    elif rel.endswith(".html"):
        rel = rel[: -len(".html")]
    return ORIGIN + rel


class Spans(html.parser.HTMLParser):
    """Finds the spans of the other language and the start tags to rewrite."""

    def __init__(self, text, keep):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.keep = keep
        self.lines = [0] + [i + 1 for i, ch in enumerate(text) if ch == "\n"]
        self.drop = []  # (start, end): elements of another language
        self.edits = []  # (start, end, new text): kept start tags with data-lang or data-alt-*
        self.stack = []  # (tag, start of a dropped element or None)

    def pos(self):
        line, offset = self.getpos()
        return self.lines[line - 1] + offset

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        start = self.pos()
        raw = self.get_starttag_text()
        end = start + len(raw)
        lang = a.get("data-lang")
        if lang and lang != self.keep:
            if tag in VOID:
                self.drop.append((start, end))
            else:
                self.stack.append((tag, start))
            return
        if lang or any(k.startswith("data-alt-") for k in a):
            self.edits.append((start, end, self.rewrite(raw, a)))
        if tag not in VOID:
            self.stack.append((tag, None))

    def handle_endtag(self, tag):
        while self.stack:
            t, dropped_from = self.stack.pop()
            if t == tag:
                if dropped_from is not None:
                    self.drop.append((dropped_from, self.text.index(">", self.pos()) + 1))
                break

    def rewrite(self, raw, a):
        if "data-lang" in a:
            raw = re.sub(r'\s+data-lang="[^"]*"', "", raw)
            raw = re.sub(r"\s+hidden(?=[\s/>])", "", raw, count=1)
        if "data-alt-" + self.keep in a:
            raw = re.sub(r'\s+alt="[^"]*"', "", raw)
            alt = a["data-alt-" + self.keep]
            raw = re.sub(r'\s+data-alt-(pt|en)="[^"]*"',
                         lambda m: f' alt="{alt}"' if m.group(1) == self.keep else "", raw)
        return raw


def keep_language(text, keep):
    spans = Spans(text, keep)
    spans.feed(text)
    spans.close()
    drops = sorted(spans.drop)
    edits = [e for e in spans.edits if not any(s <= e[0] < t for s, t in drops)]
    # A dropped element alone on its line(s) takes the line(s) with it.
    widened = []
    for start, end in drops:
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        line_end = len(text) if line_end == -1 else line_end + 1
        if text[line_start:start].strip() == "" and text[end:line_end].strip() == "":
            start, end = line_start, line_end
        widened.append((start, end, ""))
    out, at = [], 0
    for start, end, new in sorted(widened + edits):
        out.append(text[at:start])
        out.append(new)
        at = end
    out.append(text[at:])
    return "".join(out)


def shared_links(text):
    """In site/pt/, links to files outside the language's directory get ../."""
    def fix(m):
        attr, value = m.group(1), m.group(2)
        path = re.split(r"[#?]", value, maxsplit=1)[0]
        if not path or "://" in value or value.startswith(("#", "/", "mailto:", "data:")) or path.endswith(".html"):
            return m.group(0)
        return f'{attr}="../{value}"'
    return re.sub(r'\b(href|src)="([^"]*)"', fix, text)


def render(name, lang):
    """One page of src/<name> in one language; returns (relative path, text)."""
    info = LANGS[lang]
    text = (SRC / name).read_text(encoding="utf-8")
    text = keep_language(text, lang)
    text = re.sub(r'(<html\b[^>]*?)\blang="[^"]*"', rf'\1lang="{info["html"]}"', text, count=1)
    if lang == "en":
        text = re.sub(r'\bid="([^"]*)-en"', r'id="\1"', text)
        text = re.sub(r'href="#([^"]*)-en"', r'href="#\1"', text)
    else:
        text = shared_links(text)
    rel = info["dir"] + name
    twins = {l: LANGS[l]["dir"] + name for l in LANGS}
    # The language switch: links to this page in every language.
    links = []
    for l, twin in twins.items():
        href = twin if lang == "en" else ("../" + twin if l == "en" else name)
        current = ' aria-current="true"' if l == lang else ""
        links.append(f'<a href="{href}" hreflang="{LANGS[l]["hreflang"]}" lang="{LANGS[l]["html"]}"{current}>{LANGS[l]["label"]}</a>')
    switch = f'<nav class="langs" aria-label="{info["switch"]}">' + "".join(links) + "</nav>"
    text, n = re.subn(r'<nav class="langs"[^>]*></nav>', switch, text, count=1)
    assert n == 1, f"{name}: no empty <nav class=\"langs\"> to fill"
    # The head: canonical, alternates, Open Graph locale.
    if name != "404.html":
        head = [f'<link rel="canonical" href="{clean_url(rel)}">']
        for l, twin in twins.items():
            head.append(f'<link rel="alternate" hreflang="{LANGS[l]["hreflang"]}" href="{clean_url(twin)}">')
        head.append(f'<link rel="alternate" hreflang="x-default" href="{clean_url(twins[DEFAULT])}">')
        head.append(f'<meta property="og:url" content="{clean_url(rel)}">')
        head.append(f'<meta property="og:locale" content="{info["locale"]}">')
        for l in LANGS:
            if l != lang:
                head.append(f'<meta property="og:locale:alternate" content="{LANGS[l]["locale"]}">')
        text = text.replace("</head>", "\n".join(head) + "\n</head>", 1)
    return rel, text


def outputs():
    pages = {}
    for src in sorted(SRC.glob("*.html")):
        for lang in LANGS:
            rel, text = render(src.name, lang)
            pages[rel] = text
    urls = [clean_url(rel) for rel in pages if not rel.endswith("404.html")]
    pages["sitemap.xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
        + "</urlset>\n"
    )
    return pages


def stale():
    """The outputs whose file on disk differs from what the sources give."""
    result = []
    for rel, text in outputs().items():
        path = SITE / rel
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            result.append(rel)
    return result


def main(argv):
    if argv[1:] == ["--check"]:
        for rel in stale():
            print(f"site/{rel} is stale: run python3 tools/pages.py", file=sys.stderr)
        return 1 if stale() else 0
    for rel, text in outputs().items():
        path = SITE / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"wrote site/{rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
