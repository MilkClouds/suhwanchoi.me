# suhwanchoi.me

Personal website, blog, and CV repository. Originally based on [jonbarron.github.io](https://github.com/jonbarron/jonbarron.github.io).

## Structure

- `suhwanchoi.me/` — homepage and static assets, deployed to [suhwanchoi.me](https://suhwanchoi.me) via GitHub Actions. The `suhwanchoi.me/blog/` subtree is built from `blog-src/` by Quarto and is **not tracked** in git (see `.gitignore`).
- `blog-src/` — Quarto source for the blog. Posts live in `blog-src/posts/*.qmd`. Renders into `suhwanchoi.me/blog/`.
- `cv/` — CV LaTeX source. The built `cv/suhwan_choi_cv.pdf` is reachable from the site at `/suhwan_choi_cv.pdf` via a tracked symlink in `suhwanchoi.me/`.
- `milkclouds/` — [GitHub profile](https://github.com/MilkClouds/milkclouds) (git submodule).

## How to build CV

1. Install LaTeX Workshop extension for VSCode
2. Open `cv/suhwan_choi_cv.tex` in VSCode
3. Press `Option+Command+B` to build
4. Built PDF is at `cv/suhwan_choi_cv.pdf`

## How to serve website locally

The homepage is hand-written HTML; the blog is rendered by Quarto.

```bash
# Build the blog (writes into suhwanchoi.me/blog/)
quarto render blog-src

# Serve the whole site
python3 -m http.server --directory suhwanchoi.me 8000
# → open http://localhost:8000/
```

For live blog editing with auto-reload:

```bash
quarto preview blog-src
```

(The preview server is for blog content only; it won't show the homepage.)

## How to add a blog post

1. Create `blog-src/posts/<slug>.qmd` with front matter:
   ```yaml
   ---
   title: "Post title"
   description: "One-sentence summary used for previews + the listing page."
   date: 2026-04-27
   categories: [tag1, tag2]
   ---
   ```
2. Write Markdown. Cite from `blog-src/refs.bib` with `[@key]`. Math, footnotes, cross-refs all supported by Pandoc.
3. `quarto render blog-src` to preview locally.
4. Commit `blog-src/` (output is gitignored) and push to `main` — CI rebuilds and redeploys.

## Deployment

Pushing to `main` triggers `.github/workflows/pages.yml`:

1. `quarto-dev/quarto-actions/setup@v2` installs Quarto.
2. `quarto render blog-src` rebuilds the blog into `suhwanchoi.me/blog/`.
3. `actions/upload-pages-artifact@v4` packages `suhwanchoi.me/` (with symlinks dereferenced — that's how the CV at `/suhwan_choi_cv.pdf` resolves to `cv/suhwan_choi_cv.pdf`).
4. `actions/deploy-pages@v5` publishes.
