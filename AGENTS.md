# passforme website

The website of passforme at `passforme.com`: the home page, the command
guide and the brand kit, static, one page per language (English at the
root, Portuguese under `pt/`). The code (Rust: the CLI,
the vault format, the sync server) is in the main repository,
[passforme/passforme](https://github.com/passforme/passforme), with its
own `AGENTS.md`. The guide is the project's user documentation: every
command and option, with examples.

**What is true only of one person's machines and accounts** (Cloudflare
account and token, local copies) goes in `AGENTS.local.md`, ignored by
Git, and never into a tracked file. Read it when it exists.

## Read first

- [`src/guide.html`](src/guide.html): **how to use passforme**, every
  command and option with examples in both languages, the text an agent
  needs to operate the CLI or to explain it. Read it before changing it;
  `site/guide.html` and `site/pt/guide.html` are written from it.
- The main repository's `docs/design.md`, `docs/threat-model.md` and
  `docs/cryptography.md`: how passforme works and why. The guide says
  what the CLI does; those say why it does it that way.

## Rules for working here

- **Everything in this repository is English** except the site's
  Portuguese texts: code, comments, docs, commit messages. The
  maintainer talks to agents in Portuguese; none of that reaches the
  repository.
- **Commits** follow Conventional Commits (`feat(site):`, `fix(site):`,
  `docs:`, `ci:`, `chore:`), are signed, and carry **no AI attribution**:
  no `Co-Authored-By`, no "Generated with", no session links. Outside
  contributions are signed off under the DCO (`git commit -s`), as
  `CONTRIBUTING.md` says.
- **Pages are edited in `src/` and written to `site/`** by
  `python3 tools/pages.py`, one file per language, committed together
  with the source; `site/*.html` and `site/pt/*.html` are never edited
  by hand. `python3 tools/check.py` passes before every commit (it fails
  on a stale page); CI runs it on every push.
- **The guide documents the CLI as it is.** When a command or option of
  `passforme` changes, the guide changes too, in a commit here that
  follows the one in the main repository (and the main repository's
  `CHANGELOG.md` says what changed). New examples are tried in a
  throwaway vault (`PASSFORME_DIR` in a temporary directory) before they
  are written down.

## Layout

```
src/                  the pages, both languages in one file each (edited here)
  index.html          home
  guide.html          command guide (every command, with examples)
  brand.html          brand kit: logo, mark, colours, fonts, icons, social images
  404.html            not found
site/                 published as is: the web root
  index.html          English pages, written by tools/pages.py from src/
  guide.html
  brand.html
  404.html            noindex; by existing, makes Pages answer 404 instead of the home
  pt/                 the same four pages in Portuguese
  sitemap.xml         every page in every language, by canonical URL (written too)
  robots.txt          allows everything, points at the sitemap
  favicon.ico         gold mark, 16/32/48 px
  brand/              the kit's files and its .zip, generated (below)
  assets/site.css     shared: fonts, colours (light and dark), top bar, buttons
  assets/site.js      shared: the language switch's memory and the first visit's redirect
  assets/home.css     home only
  assets/guide.css    guide only
  assets/guide.js     guide only: copy buttons, search
  assets/icon.svg     favicon (gold mark); apple-touch-icon.png, og.png beside it
  assets/brand.css    brand page only
  assets/brand.js     brand page only: click a swatch to copy its colour
  assets/fonts/       Bricolage Grotesque (titles), Source Sans 3 (text),
                      JetBrains Mono (code); SIL OFL, licences beside them
tools/pages.py        writes site/ from src/: one page per language, canonical, hreflang, switch
tools/check.py        the rules below, as a test (standard library only)
tools/brand.py        generates the brand kit and the site's icons
  _headers            response headers for Cloudflare Pages: the CSP and the rest
bin/deploy            publishes site/ to Cloudflare Pages from the laptop (below)
config/               deploy.env.example, versioned; deploy.env, ignored, the real values
README.md             for visitors of the repository: what the site is, preview, how to contribute
CONTRIBUTING.md       what a contributor reads first: the rules in short, DCO sign-off
SECURITY.md           how to report a weakness in the site (passforme itself: the main repository)
.github/              CI (check.py on every push), the GitHub Pages mirror, Dependabot for the actions
```

Preview: `python3 tools/pages.py`, then
`python3 -m http.server 8765 --bind 127.0.0.1 --directory site`
(English at `/`, Portuguese at `/pt/`).

## The site's rules

All but the last two are enforced by `tools/check.py`.

- **Static and self-contained**: plain HTML, CSS and JS, nothing built
  when publishing (`site/` is served as committed) and no framework; the
  only generation is `tools/pages.py`, run by whoever edits `src/`, like
  `tools/brand.py`. Nothing is loaded from another domain — not even fonts,
  which are served from `assets/fonts/` (Google Fonts would show every
  visitor's address to Google, wrong for a password manager's site).
- **No inline scripts or styles**, so the site can be served with a strict
  Content-Security-Policy (`default-src 'self'`).
- **Every text exists in every language of the site**, in `src/`: an
  element with `data-lang="pt"` next to its twin with `data-lang="en"`
  (`hidden` in the body), `<title>` and `<meta>` included; image alt
  texts in `data-alt-pt` / `data-alt-en`; the guide's search placeholder
  in `guide.js`. English ids and anchors that would clash with the
  Portuguese ones are written `name-en` and lose the suffix in `site/`.
  Each page gets its own URL per language, with `hreflang` alternates,
  so a search engine indexes both; the switch in the top bar links to
  the twin, `site.js` remembers the choice and, on a first visit, sends
  a `pt-*` browser to `pt/`. Only names stay the same across languages
  (passforme, GitHub, file names, font names).
- **Every page names its canonical URL** and its alternates,
  `https://passforme.com/` plus the path without `.html`, the form
  Cloudflare Pages serves it at (`/guide`, `/pt/guide`); the mirrors
  (`passforme.pages.dev`, GitHub Pages) carry the same tags and so defer
  to the site. `404.html` is `noindex` and, by existing, makes Pages
  answer 404 instead of serving the home for every unknown path.
  `sitemap.xml` lists every page and `robots.txt` points at it.
- **Links to other sites open in a new tab** (`target="_blank" rel="noopener"`):
  GitHub, the font foundries. Links inside the site stay in the same tab.
- **Examples are generic**: `pfm.example.com`, `you@example.com`. Nothing
  from anyone's own setup (hostnames, tailnet, paths, programs).
- The site calls itself open source and links
  **https://github.com/passforme**, the project's official home, from
  every page.

## Brand kit

`site/brand/`, `site/favicon.ico`, `site/assets/icon.svg`,
`site/assets/apple-touch-icon.png` and `site/assets/og.png` are
**generated by `tools/brand.py`**; never edit them by hand. The palette
and the mark are defined once there (the colours match the tokens in
`assets/site.css`), the wordmark is the site's Bricolage Grotesque turned
into outlines, and headless Chromium renders the PNGs, so changing a
colour is one edit and one run. Two colourways: **gold** `#e0ac5c`
(the main one, used by the site) with a brass keyhole, and **brass**
`#8a5a12` with a gold one; the mark and the logo also come with the
keyhole cut out (`-cutout`, one even-odd path, no mask: a hole the
background shows through), black (`-black`, ink) and white (`-white`,
sheet). The logo and the wordmark come for light and dark backgrounds
and in one colour. `brand.html` shows all of it and offers
it for download, with the zip of the whole kit. The main repository's
README shows two of the logos from its own copy, `docs/brand/`: when
the kit changes, copy them there again. The fonts ship unmodified
(woff2) with their OFL texts.

## Fonts

From the `@fontsource-variable` packages (Bricolage Grotesque 5.3.0,
Source Sans 3 5.3.1, JetBrains Mono 5.3.0), latin subset, variable:
Bricolage with its weight, width and optical-size axes (titles use
`"opsz" 96`), the other two with weight.

## Deployment

Cloudflare Pages, in the project's own Cloudflare account, serving
`site/` as is on `passforme.com` and `www`; the redirect from `www` to
the apex is a Redirect Rule of the zone, not a `_redirects` file (Pages
does not redirect by host). Nothing is built. `site/_headers` carries the
Content-Security-Policy (`default-src 'self'`, which the rules above make
possible) and the other security headers; change the site's rules and
the CSP together. Pages serves `guide.html` as `/guide` (and
`pt/guide.html` as `/pt/guide`), redirecting the `.html` form; links
inside the site keep the file name, which `tools/check.py` can verify
exists.

`bin/deploy` publishes from the laptop: it runs `tools/check.py`, then
uploads `site/` with `wrangler pages deploy` (direct upload, no Git
integration). It reads `config/deploy.env`, ignored by Git, whose
versioned twin `config/deploy.env.example` documents the variables; the
API token is never written to a file but produced by a command, such as
`passforme get <item> --stdout`. A mirror at
https://passforme.github.io/website/ is published by
`.github/workflows/pages.yml` on every push to `main`, for the days the
main host is down; it cannot send headers, so it is not the site.

**No releases, no `CHANGELOG.md`**: the site has no versions, what is
on `main` is what is published. A change to the CLI is recorded in the
main repository's `CHANGELOG.md`, and the guide follows it.
