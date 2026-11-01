# Security policy

This repository is the static site at `passforme.com`: pages, styles,
scripts, fonts and images, with no accounts, no forms and no data about
its visitors. A weakness here is a way to change what visitors of a
password manager's site see, or to learn who they are, so please report
it privately and give us time to fix it before it is made public.

## Reporting a vulnerability

Write to **hello@passforme.com**, or use GitHub's private vulnerability
reporting ("Report a vulnerability" under the repository's Security
tab). Say what you found and how to reproduce it.

Problems in passforme itself (the vault, the CLI, the sync server) go
to the [main repository's policy](https://github.com/passforme/passforme/security/policy).

## What counts

- A way to run a script, or load a resource, that is not in this
  repository: the site is meant to be served with `default-src 'self'`.
- Anything that sends a visitor's address or activity to a third party.
- Content that misleads a visitor about where passforme comes from: a
  link to another download, another "official" source.

Mistakes in the guide are issues, not vulnerabilities; please open one.

## Supported versions

The site has no versions. What is on `main` is what is published, and a
fix is deployed as soon as it is merged.
