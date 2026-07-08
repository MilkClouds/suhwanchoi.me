#!/usr/bin/env bash
# Build the deployable site into _site/ -- the SINGLE source of truth for the
# deploy output, used by both local preview (site/scripts/serve.sh) and CI
# (.github/workflows/pages.yml). Produces:
#   - site/cv/suhwan_choi_cv.pdf   (LaTeX -> latexmk)
#   - site/blog/_site/             (Quarto blog render)
#   - site/public/blog/            (copied blog output)
#   - _site/                       (copy of site/public/ with the CV symlink
#                                   replaced by the real PDF; this is what ships)
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."
root="$(pwd)"
out="$root/_site"

# 1. CV PDF. (No output redirect: TeX writes compile errors to stdout, so
#    swallowing it would hide why a failed build failed.)
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd "$root/site/cv/suhwan_choi_cv.tex"

# 2. Blog. Quarto renders inside its own project directory; then we copy
#    that output into the static site tree consumed by the final assembly.
quarto render "$root/site/blog"
rm -rf "$root/site/public/blog"
mkdir -p "$root/site/public/blog"
cp -r "$root/site/blog/_site/." "$root/site/public/blog/"

# 3. Assemble _site/ with the CV symlink replaced by the real PDF. (The symlink
#    is dereferenced by tar on CI too; doing it explicitly also works on Windows,
#    where git checks the symlink out as a text stub.)
rm -rf "$out"
cp -r "$root/site/public" "$out"
rm -f "$out/suhwan_choi_cv.pdf"
cp "$root/site/cv/suhwan_choi_cv.pdf" "$out/suhwan_choi_cv.pdf"
