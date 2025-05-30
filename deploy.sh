#!/bin/bash
mkdocs gh-deploy
git stash
git checkout gh-pages
echo "dynamicmacros.3dcoded.xyz" > CNAME
git add .
git commit -m "Add CNAME"
git push origin gh-pages
git checkout docs
git stash pop
git add .
git commit -m "chore: Deploy documentation"
git push origin docs