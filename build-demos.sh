#!/usr/bin/env bash
# build-demos.sh — regenerate every demo page shown by the website into
# docs/example/. Run this after changing the tool or the sample transcript,
# then commit the results.

set -euo pipefail
cd "$(dirname "$0")"

TOOL="python3 aichatprocess.py"
EX="docs/example"
SRC="$EX/aichat.txt"

# Main chat page (+ derived Word version) and its CSS. Default theme.
$TOOL --source "$SRC" --output "$EX/aichat.html" --css "$EX/aichat.css" \
      --write-css overwrite --title "AI Chat — Example" --word-output

# A math-enabled copy of the chat page (KaTeX), for the example page to link.
$TOOL --source "$SRC" --output "$EX/aichat-math.html" --css "$EX/aichat.css" \
      --write-css never --title "AI Chat — Example (math)" --math

# Theme demos. Point --css-template at a nonexistent file so the bundled theme
# wins (an existing template would otherwise take precedence over --theme).
for t in dark minimal warm; do
  $TOOL --source "$SRC" --output "$EX/themes/example-$t.html" \
        --css "$EX/themes/example-$t.css" --theme "$t" \
        --css-template ".no-template" --write-css overwrite \
        --title "AI Chat — $t theme"
done

# Word-style demos.
mkdir -p "$EX/word"
for s in default compact plain; do
  $TOOL --source "$SRC" --output /tmp/_discard.html --css /tmp/_discard.css \
        --write-css overwrite --word-output "$EX/word/word-$s.html" \
        --word-style "$s" --title "AI Chat — Word ($s)"
done
rm -f /tmp/_discard.html /tmp/_discard.css

echo "Demos regenerated into $EX/"
