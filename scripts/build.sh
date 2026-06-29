#!/usr/bin/env bash
# Build the deployable site into _site/ -- the SINGLE source of truth for the
# deploy output, used by both local preview (scripts/serve.sh) and CI
# (.github/workflows/pages.yml). Produces:
#   - cv/suhwan_choi_cv.pdf   (LaTeX -> latexmk)
#   - blog-src/_site/         (Quarto blog render)
#   - suhwanchoi.me/blog/     (copied blog output)
#   - _site/                  (copy of suhwanchoi.me/ with the CV symlink
#                              replaced by the real PDF; this is what ships)
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
root="$(pwd)"
out="$root/_site"

# 1. CV PDF. (No output redirect: TeX writes compile errors to stdout, so
#    swallowing it would hide why a failed build failed.)
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd "$root/cv/suhwan_choi_cv.tex"

# 2. Blog. Quarto renders inside its own project directory; then we copy
#    that output into the static site tree consumed by the final assembly.
quarto render "$root/blog-src"
rm -rf "$root/suhwanchoi.me/blog"
mkdir -p "$root/suhwanchoi.me/blog"
cp -r "$root/blog-src/_site/." "$root/suhwanchoi.me/blog/"

# 3. Assemble _site/ with the CV symlink replaced by the real PDF. (The symlink
#    is dereferenced by tar on CI too; doing it explicitly also works on Windows,
#    where git checks the symlink out as a text stub.)
rm -rf "$out"
cp -r "$root/suhwanchoi.me" "$out"
rm -f "$out/suhwan_choi_cv.pdf"
cp "$root/cv/suhwan_choi_cv.pdf" "$out/suhwan_choi_cv.pdf"
