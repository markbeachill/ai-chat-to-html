#!/usr/bin/env bash
# build-downloads.sh — assemble the zip files offered on the download page into
# docs/downloads/. Run after changing the tool, then commit the zips.
#
# Produces two zips:
#   aichat-tool.zip      Just the tool: script, template, requirements, a short
#                        readme. The minimum needed to run it.
#   aichat-tool-full.zip The tool plus the example transcript and outputs and a
#                        getting-started copy of the instructions.

set -euo pipefail
cd "$(dirname "$0")"

OUT="docs/downloads"
mkdir -p "$OUT"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# ---- slim: just the tool -------------------------------------------------- #
SLIM="$WORK/ai-chat-to-html"
mkdir -p "$SLIM"
cp aichatprocess.py aichat-template.css requirements.txt conversation-collector-prompt.md "$SLIM/"

cat > "$SLIM/README.txt" <<'EOF'
AI Chat to HTML — the tool
==========================

This is the tool on its own. To use it:

1. Install Python 3 (see https://markbeachill.github.io/ai-chat-to-html/setup.html).
2. In this folder, install the one dependency:
       pip install -r requirements.txt
3. Put your transcript in a file called aichat.txt (or aichat.md), then run:
       python3 aichatprocess.py

You'll get aichat.html and aichat.css. For options (themes, a Word version,
maths), run:
       python3 aichatprocess.py --help

Full instructions: https://markbeachill.github.io/ai-chat-to-html/
Optional collector prompt: conversation-collector-prompt.md
MIT licensed.
EOF
cp LICENSE "$SLIM/LICENSE"

( cd "$WORK" && zip -rq "ai-chat-to-html-tool.zip" "ai-chat-to-html" )
mv "$WORK/ai-chat-to-html-tool.zip" "$OUT/"

# ---- full: tool + examples + instructions --------------------------------- #
FULL="$WORK/ai-chat-to-html-full"
mkdir -p "$FULL"
cp aichatprocess.py aichat-template.css requirements.txt conversation-collector-prompt.md LICENSE "$FULL/"
cp "$SLIM/README.txt" "$FULL/README.txt"

# example transcript + a freshly generated set of outputs
mkdir -p "$FULL/example"
cp docs/example/aichat.txt "$FULL/example/"
cp docs/example/aichat.html docs/example/aichat.css "$FULL/example/"
cp docs/example/aichat-word.html docs/example/aichat-word.css "$FULL/example/"

# a plain-text getting-started note
cat > "$FULL/INSTRUCTIONS.txt" <<'EOF'
AI Chat to HTML — getting started
=================================

Three steps:

1. COPY & PASTE the conversation into example/aichat.txt (or your own file).
   Mark each turn with a line containing [USER] or [CHATBOT].

2. EDIT the text: tidy wording, trim, remove anything unwanted.

3. CONVERT:  python3 aichatprocess.py --source example/aichat.txt

Useful options:
   --theme dark|minimal|warm     change the web page look
   --word-output                 also make a version to paste into Word
   --math                        render $...$ / $$...$$ maths (web page only)
   --help                        full list

Online instructions, examples and styling gallery:
   https://markbeachill.github.io/ai-chat-to-html/
EOF

( cd "$WORK" && zip -rq "ai-chat-to-html-full.zip" "ai-chat-to-html-full" )
mv "$WORK/ai-chat-to-html-full.zip" "$OUT/"

echo "Built:"
ls -la "$OUT"/*.zip
