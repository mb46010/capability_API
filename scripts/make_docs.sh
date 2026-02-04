#!/bin/bash
set -e

echo "🚀 Building documentation..."
mkdocs build

echo "🔧 Patching Kroki-generated SVGs to fix XML namespace issues..."
# Fixes 'Namespace prefix xlink for href on image is not defined' error
# by injecting the missing xmlns:xlink declaration into the root <svg> tag.
find site -name "*.svg" -exec sed -i 's/<svg /<svg xmlns:xlink="http:\/\/www.w3.org\/1999\/xlink" /' {} +

echo "✅ Documentation built and patched successfully!"
