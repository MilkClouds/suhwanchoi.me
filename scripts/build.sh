#!/usr/bin/env bash
# Build the deployable site into _site/ -- the SINGLE source of truth for the
# deploy output, used by both local preview (scripts/serve.sh) and CI
# (.github/workflows/pages.yml). Produces:
#   - cv/suhwan_choi_cv.pdf   (LaTeX -> latexmk)
#   - suhwanchoi.me/blog/     (Quarto)
#   - _site/                  (copy of suhwanchoi.me/ with the CV symlink
#                              replaced by the real PDF; this is what ships)
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
root="$(pwd)"
out="$root/_site"

# 1. CV PDF. (No output redirect: TeX writes compile errors to stdout, so
#    swallowing it would hide why a failed build failed.)
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd "$root/cv/suhwan_choi_cv.tex"

# 2. Blog (renders into suhwanchoi.me/blog/ per blog-src/_quarto.yml).
quarto render "$root/blog-src"

# 3. Assemble _site/ with the CV symlink replaced by the real PDF. (The symlink
#    is dereferenced by tar on CI too; doing it explicitly also works on Windows,
#    where git checks the symlink out as a text stub.)
rm -rf "$out"
cp -r "$root/suhwanchoi.me" "$out"
rm -f "$out/suhwan_choi_cv.pdf"
cp "$root/cv/suhwan_choi_cv.pdf" "$out/suhwan_choi_cv.pdf"
