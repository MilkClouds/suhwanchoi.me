# suhwanchoi.me

Personal website and CV repository. Originally based on [jonbarron.github.io](https://github.com/jonbarron/jonbarron.github.io).

## Structure

- `suhwanchoi.me/` - Homepage, deployed to [suhwanchoi.me](https://suhwanchoi.me) via GitHub Actions
- `cv/` - CV LaTeX source and built PDF
- `milkclouds/` - [GitHub profile](https://github.com/MilkClouds/milkclouds) (submodule)

## How to build CV

1. Install LaTeX Workshop extension for VSCode
2. Open `cv/suhwan_choi_cv.tex` in VSCode
3. Press `Option+Command+B` to build
4. Built PDF is at `cv/suhwan_choi_cv.pdf`

## How to serve website locally

1. Run `python3 -m http.server` in the `suhwanchoi.me/` directory
2. Open `localhost:8000` in the browser
