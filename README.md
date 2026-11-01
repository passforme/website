<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="site/brand/logo/logo-gold-on-dark.svg">
    <img src="site/brand/logo/logo-brass-on-light.svg" alt="passforme" width="440">
  </picture>
  <br>
  <strong>passforme.com: the home page, the command guide and the brand kit.</strong>
  <br>
  <sub>Static &middot; multilingual &middot; no build step</sub>
</p>

The site of [passforme](https://github.com/passforme/passforme), a
password vault only you can open, kept in sync by a server you run
yourself. It is where someone decides whether passforme is for them,
learns every command once they have it, and finds the logo when they
write about it:

- **Home**: what passforme keeps, how it protects it and for whom.
- **Command guide**: every command and option with a tried example, in
  every language of the site. It is the project's user documentation
  and follows the CLI release by release.
- **Brand kit**: logo, mark, colours, fonts, icons and social images,
  free to use when talking about the project, with a zip of the whole
  kit.

> **Status:** not online yet. `passforme.com` will serve `site/` as is,
> with nothing built. For now, preview it locally (below).

The site is plain HTML, CSS and JavaScript: no build step, no framework,
nothing loaded from another domain, not even fonts. The site of a
password manager should not tell anyone else who visits it, and it is
written to be served with a strict Content-Security-Policy that keeps
it that way.

## Preview

Needs only Python 3.

```sh
git clone https://github.com/passforme/website.git
cd website
python3 -m http.server 8765 --bind 127.0.0.1 --directory site
# http://127.0.0.1:8765
```

Each page has a language switch at the top; the choice is remembered in
the browser and nowhere else.

## Contributing

- **Every language.** Every text exists once per language of the site:
  an element with `data-lang="pt"` next to its twin with
  `data-lang="en" hidden`. If you can write only one of them, open the
  pull request anyway and say so.
- **The guide documents the CLI as released.** A new example is tried
  first in a throwaway vault (`PASSFORME_DIR` pointing at a temporary
  directory) before it is written down.
- **The check must pass.** `python3 tools/check.py` is what CI runs on
  every push: it fails on inline scripts or styles, resources from other
  domains, broken links and fragments, and a text missing in one of the
  languages.
- **The brand kit is generated.** `site/brand/`, the favicon, the icons
  and the social image come from `tools/brand.py`; change the palette or
  the mark there and run it, never the files. It needs fontTools, brotli
  and Chromium; its docstring says how.

The full rules, and the reasons behind them, are in
[`AGENTS.md`](AGENTS.md), written for the people and the agents who
work here.

## Security

The site keeps no accounts, has no forms and stores nothing about its
visitors. If you find a way to run a script on it, load something from
another domain, or otherwise break that, see
[`SECURITY.md`](SECURITY.md). Problems in passforme itself, the vault,
the CLI or the sync server, go to the
[main repository's policy](https://github.com/passforme/passforme/security/policy).

## License

The site is [AGPL-3.0-only](LICENSE), like passforme. The brand kit may
be used freely to talk about the project; the brand page says how. The
fonts in `site/assets/fonts/` and `site/brand/fonts/` keep their own
SIL Open Font License, included beside them.
