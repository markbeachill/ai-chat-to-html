#!/usr/bin/env python3
"""
aichatprocess.py — Convert a marked-up AI chat transcript (Markdown) into a complete,
self-contained HTML page plus a separate CSS file.

The transcript is plain Markdown where each turn begins with a line that
identifies the speaker, e.g.:

    # **[USER]**
    Tell me about gravity?
    # **[CHATBOT]**
    Gravity is the force that ...

Role-line matching is deliberately flexible: any line whose text contains
the token [USER] or [CHATBOT] (case-insensitive) starts a new turn. The rest
of the line is ignored, so '# **[USER]**', '[user]', and '## [Chatbot]:' all work.

The Markdown inside each turn is converted to HTML with Python-Markdown.
Fenced code blocks are rendered as visible, escaped code — never interpreted
as page markup — so transcripts that contain HTML examples stay safe.

No LaTeX/math handling: math written as plain text is left as plain text.

If no --source is given, the tool reads aichat.txt, falling back to aichat.md
when aichat.txt is absent. A user who prefers a Markdown editor can keep the
transcript as aichat.md with no extra flags.

CSS behaviour (--write-css):
    never       Leave the CSS file untouched; only link to it. Template ignored.
    if-missing  Write the CSS file only if it does not already exist (default).
    overwrite   Always (re)write the CSS file.
When writing, the external template (default: aichat-template.css) is used if
present; otherwise an internal default stylesheet is written.

The generated CSS is scoped under '.ai-chat-page' so the snippet can be pasted
into pages that have their own, differing CSS without the two interfering.
(Full isolation would require an iframe or Shadow DOM, which would defeat the
copy-a-snippet goal; scoping is the deliberate trade-off.)
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "Error: the 'markdown' package is required. Install it with:\n"
        "    pip install -r requirements.txt\n"
        "or\n"
        "    pip install markdown\n"
    )
    raise SystemExit(1)


# --------------------------------------------------------------------------- #
# Defaults
# --------------------------------------------------------------------------- #

DEFAULT_SOURCE = "aichat.txt"
DEFAULT_SOURCE_FALLBACK = "aichat.md"
DEFAULT_OUTPUT = "aichat.html"
DEFAULT_CSS = "aichat.css"
DEFAULT_CSS_TEMPLATE = "aichat-template.css"

# Any line containing one of these tokens (case-insensitive) starts a new turn.
ROLE_TOKENS = {
    "USER": "user",
    "CHATBOT": "chatbot",
}
ROLE_LINE_RE = re.compile(r"\[\s*(USER|CHATBOT)\s*\]", re.IGNORECASE)

ROLE_LABELS = {
    "user": "User",
    "chatbot": "Chatbot",
}


# --------------------------------------------------------------------------- #
# Transcript parsing
# --------------------------------------------------------------------------- #

def parse_transcript(text: str):
    """Split a transcript into a list of (role, body_markdown) turns.

    A new turn begins at any line containing [USER] or [CHATBOT]. Content
    before the first role line is ignored (with a warning).
    """
    turns = []
    current_role = None
    current_lines: list[str] = []
    preamble: list[str] = []

    def flush():
        if current_role is not None:
            body = "\n".join(current_lines).strip("\n")
            turns.append((current_role, body))

    for line in text.splitlines():
        match = ROLE_LINE_RE.search(line)
        if match:
            flush()
            current_role = ROLE_TOKENS[match.group(1).upper()]
            current_lines = []
        elif current_role is None:
            if line.strip():
                preamble.append(line)
        else:
            current_lines.append(line)

    flush()

    if preamble:
        sys.stderr.write(
            "Warning: text before the first role marker was ignored:\n"
            f"  {preamble[0][:60]!r}...\n"
        )
    return turns


# --------------------------------------------------------------------------- #
# Markdown -> HTML
# --------------------------------------------------------------------------- #

def make_markdown_converter() -> "markdown.Markdown":
    # fenced_code: ``` blocks. codehilite is intentionally NOT used (no
    # highlighter dependency); the language is preserved as a class so a
    # highlighter can be added later. Python-Markdown escapes the contents of
    # fenced code blocks by default, which is exactly the safety we need.
    return markdown.Markdown(
        extensions=["fenced_code", "tables", "sane_lists", "nl2br"],
        output_format="html5",
    )


def turn_to_html(md: "markdown.Markdown", role: str, body: str) -> str:
    md.reset()
    inner = md.convert(body) if body.strip() else ""
    label = ROLE_LABELS.get(role, role.title())
    return (
        f'      <div class="ai-chat-turn ai-chat-turn--{role}">\n'
        f'        <div class="ai-chat-role" aria-hidden="true">{html.escape(label)}</div>\n'
        f'        <div class="ai-chat-bubble">\n'
        f"{_indent(inner, 10)}\n"
        f"        </div>\n"
        f"      </div>"
    )


def _indent(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + ln if ln else ln for ln in text.splitlines())


# --------------------------------------------------------------------------- #
# Page assembly
# --------------------------------------------------------------------------- #

MARKER_STAR = "<!-- ******************************************** -->"


def _marker_block(label: str) -> str:
    stars = "\n".join([MARKER_STAR] * 5)
    label_line = f"<!-- {label:<44} -->"
    return f"{stars}\n{label_line}\n{stars}"


def build_html(turns, css_href: str, title: str) -> str:
    md = make_markdown_converter()
    turn_html = "\n".join(turn_to_html(md, role, body) for role, body in turns)

    start_marker = _marker_block("COPY CHAT HTML START")
    end_marker = _marker_block("COPY CHAT HTML END")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{html.escape(css_href, quote=True)}">
</head>
<body>

{start_marker}

<main class="ai-chat-page">
  <div class="ai-chat-window">
    <div class="ai-chat-log">
{turn_html}
    </div>
  </div>
</main>

{end_marker}

</body>
</html>
"""


# --------------------------------------------------------------------------- #
# Word-friendly output
# --------------------------------------------------------------------------- #
#
# Word's HTML import ignores flexbox, alignment, border-radius and box-shadow,
# and handles linked CSS poorly. So the Word variant is a different build: a
# clean transcript (speaker label, then text), using only constructs Word keeps
# and INLINE styles on each element (these survive copy-paste). A linked
# stylesheet is also included so the page looks right in the browser before you
# copy from it.

# Inline style fragments per Word look. Each entry is the copy-paste-safe layer
# (inline styles survive the paste into Word). All three avoid flexbox, bubbles,
# alignment and dark backgrounds — the things Word strips or mishandles.
WORD_STYLES = {
    "default": {
        "turn":  "margin:0 0 18px 0; padding:0 0 14px 0; "
                 "border-bottom:1px solid #dddddd;",
        "role_user": "margin:0 0 6px 0; font-family:Arial,sans-serif; "
                     "font-size:11pt; font-weight:bold; color:#1a4f8b;",
        "role_bot":  "margin:0 0 6px 0; font-family:Arial,sans-serif; "
                     "font-size:11pt; font-weight:bold; color:#444444;",
        "body":  "margin:0; font-family:Calibri,Arial,sans-serif; "
                 "font-size:11pt; color:#1a1a1a; line-height:1.5;",
        "p":     "margin:0 0 8px 0;",
        "list":  "margin:0 0 8px 0; padding-left:22px;",
        "li":    "margin:0 0 3px 0;",
        "pre":   "margin:0 0 10px 0; padding:10px 12px; background:#f3f3f3; "
                 "border:1px solid #cccccc; font-family:Consolas,monospace; "
                 "font-size:10pt; white-space:pre-wrap;",
        "code":  "font-family:Consolas,monospace; font-size:10pt; background:#f3f3f3;",
    },
    # Tighter spacing and smaller type — fits a long transcript on fewer pages.
    "compact": {
        "turn":  "margin:0 0 9px 0; padding:0;",
        "role_user": "margin:0 0 2px 0; font-family:Arial,sans-serif; "
                     "font-size:10pt; font-weight:bold; color:#1a4f8b;",
        "role_bot":  "margin:0 0 2px 0; font-family:Arial,sans-serif; "
                     "font-size:10pt; font-weight:bold; color:#444444;",
        "body":  "margin:0; font-family:Calibri,Arial,sans-serif; "
                 "font-size:10pt; color:#1a1a1a; line-height:1.35;",
        "p":     "margin:0 0 5px 0;",
        "list":  "margin:0 0 5px 0; padding-left:20px;",
        "li":    "margin:0 0 1px 0;",
        "pre":   "margin:0 0 6px 0; padding:7px 9px; background:#f3f3f3; "
                 "border:1px solid #cccccc; font-family:Consolas,monospace; "
                 "font-size:9pt; white-space:pre-wrap;",
        "code":  "font-family:Consolas,monospace; font-size:9pt; background:#f3f3f3;",
    },
    # No rules, no colour — just bold black labels. Most neutral; reformats
    # cleanly into someone else's document template.
    "plain": {
        "turn":  "margin:0 0 14px 0; padding:0;",
        "role_user": "margin:0 0 4px 0; font-family:Calibri,Arial,sans-serif; "
                     "font-size:11pt; font-weight:bold; color:#000000;",
        "role_bot":  "margin:0 0 4px 0; font-family:Calibri,Arial,sans-serif; "
                     "font-size:11pt; font-weight:bold; color:#000000;",
        "body":  "margin:0; font-family:Calibri,Arial,sans-serif; "
                 "font-size:11pt; color:#000000; line-height:1.5;",
        "p":     "margin:0 0 8px 0;",
        "list":  "margin:0 0 8px 0; padding-left:22px;",
        "li":    "margin:0 0 3px 0;",
        "pre":   "margin:0 0 10px 0; padding:8px 10px; "
                 "border:1px solid #cccccc; font-family:Consolas,monospace; "
                 "font-size:10pt; white-space:pre-wrap;",
        "code":  "font-family:Consolas,monospace; font-size:10pt;",
    },
}


def _inline_style_body(inner: str, w: dict) -> str:
    """Add inline styles to the common block tags Word respects."""
    inner = inner.replace("<p>", f'<p style="{w["p"]}">')
    inner = inner.replace("<pre>", f'<pre style="{w["pre"]}">')
    inner = inner.replace("<code>", f'<code style="{w["code"]}">')
    inner = inner.replace("<ul>", f'<ul style="{w["list"]}">')
    inner = inner.replace("<ol>", f'<ol style="{w["list"]}">')
    inner = inner.replace("<li>", f'<li style="{w["li"]}">')
    return inner


def word_turn_to_html(md, role, body, w: dict) -> str:
    md.reset()
    inner = md.convert(body) if body.strip() else ""
    inner = _inline_style_body(inner, w)
    label = ROLE_LABELS.get(role, role.title())
    role_style = w["role_user"] if role == "user" else w["role_bot"]
    return (
        f'  <div class="wt wt--{role}" style="{w["turn"]}">\n'
        f'    <p class="wt-role" style="{role_style}">{html.escape(label)}</p>\n'
        f'    <div class="wt-body" style="{w["body"]}">\n'
        f"{_indent(inner, 6)}\n"
        f"    </div>\n"
        f"  </div>"
    )


def build_word_html(turns, css_href: str, title: str,
                    word_style: str = "default") -> str:
    w = WORD_STYLES.get(word_style, WORD_STYLES["default"])
    md = make_markdown_converter()
    turn_html = "\n".join(word_turn_to_html(md, role, body, w) for role, body in turns)
    start_marker = _marker_block("COPY WORD TRANSCRIPT START")
    end_marker = _marker_block("COPY WORD TRANSCRIPT END")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} (Word version)</title>
  <link rel="stylesheet" href="{html.escape(css_href, quote=True)}">
</head>
<body>

<p style="font-family:Arial,sans-serif; font-size:9pt; color:#888888;
   margin:0 0 16px 0;">Select all of the transcript below and copy it into
   Word. (This note won't be part of the useful selection.)</p>

{start_marker}

<div class="word-transcript" style="max-width:680px; font-family:Calibri,Arial,sans-serif;">
{turn_html}
</div>

{end_marker}

</body>
</html>
"""


def build_word_css(word_style: str = "default") -> str:
    """Browser-view stylesheet matching the chosen Word look. The page also
    carries inline styles (the layer that survives copy-paste into Word); these
    rules just make it look tidy in the browser before you copy."""
    w = WORD_STYLES.get(word_style, WORD_STYLES["default"])
    return f"""/* Word-friendly transcript styles ({word_style}) — browser view only.
 * Inline styles on each element are what survive a paste into Word; these
 * rules just tidy the browser view.
 */
body {{ background: #ffffff; margin: 24px; }}
.word-transcript {{ max-width: 680px; font-family: Calibri, Arial, sans-serif; }}
.wt {{ {w["turn"]} }}
.wt:last-child {{ border-bottom: none; }}
.wt-role {{ {w["role_bot"]} }}
.wt--user .wt-role {{ {w["role_user"]} }}
.wt-body {{ {w["body"]} }}
.wt-body p {{ {w["p"]} }}
.wt-body ul, .wt-body ol {{ {w["list"]} }}
.wt-body li {{ {w["li"]} }}
.wt-body pre {{ {w["pre"]} }}
.wt-body code {{ {w["code"]} }}
.wt-body pre code {{ background: none; }}
"""



# --------------------------------------------------------------------------- #
# Internal default CSS (used when no template file is present)
# --------------------------------------------------------------------------- #

INTERNAL_DEFAULT_CSS = """/* aichat.css — generated by aichatprocess.py (internal default)
 *
 * All rules are scoped under .ai-chat-page so this snippet can be pasted into
 * a page that already has its own CSS without the two interfering. This is
 * scoping, not true isolation: for guaranteed isolation use an iframe or
 * Shadow DOM (which would defeat the copy-a-snippet goal).
 *
 * To customise the look, create aichat-template.css next to aichatprocess.py and
 * re-run with --write-css overwrite; the template is copied verbatim.
 */

.ai-chat-page {
  --ai-bg: #f5f6f8;
  --ai-window: #ffffff;
  --ai-border: #e4e7ec;
  --ai-user-bubble: #2563eb;
  --ai-user-text: #ffffff;
  --ai-bot-bubble: #f1f3f5;
  --ai-bot-text: #1a1d21;
  --ai-role: #8a909a;
  --ai-code-bg: #1e2530;
  --ai-code-text: #e7ecf3;
  --ai-radius: 16px;
  --ai-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica,
             Arial, sans-serif;
  --ai-mono: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace;

  box-sizing: border-box;
  display: flex;
  justify-content: center;
  padding: 24px 16px;
  background: var(--ai-bg);
  font-family: var(--ai-font);
  color: var(--ai-bot-text);
  line-height: 1.55;
}

.ai-chat-page *,
.ai-chat-page *::before,
.ai-chat-page *::after { box-sizing: border-box; }

.ai-chat-window {
  width: 100%;
  max-width: 760px;
  background: var(--ai-window);
  border: 1px solid var(--ai-border);
  border-radius: var(--ai-radius);
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06),
              0 8px 24px rgba(16, 24, 40, 0.06);
}

.ai-chat-log {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 24px;
}

.ai-chat-turn { display: flex; flex-direction: column; max-width: 85%; }
.ai-chat-turn--user { align-self: flex-end; align-items: flex-end; }
.ai-chat-turn--chatbot { align-self: flex-start; align-items: flex-start; }

.ai-chat-role {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ai-role);
  margin: 0 4px 4px;
}

.ai-chat-bubble {
  padding: 12px 16px;
  border-radius: var(--ai-radius);
  word-wrap: break-word;
  overflow-wrap: anywhere;
}

.ai-chat-turn--user .ai-chat-bubble {
  background: var(--ai-user-bubble);
  color: var(--ai-user-text);
  border-bottom-right-radius: 4px;
}

.ai-chat-turn--chatbot .ai-chat-bubble {
  background: var(--ai-bot-bubble);
  color: var(--ai-bot-text);
  border-bottom-left-radius: 4px;
}

.ai-chat-bubble > :first-child { margin-top: 0; }
.ai-chat-bubble > :last-child { margin-bottom: 0; }
.ai-chat-bubble p { margin: 0 0 0.7em; }
.ai-chat-bubble h1,
.ai-chat-bubble h2,
.ai-chat-bubble h3,
.ai-chat-bubble h4 { margin: 0.6em 0 0.4em; line-height: 1.3; }
.ai-chat-bubble ul,
.ai-chat-bubble ol { margin: 0 0 0.7em; padding-left: 1.4em; }
.ai-chat-bubble li { margin: 0.2em 0; }
.ai-chat-bubble a { color: inherit; text-decoration: underline; }
.ai-chat-turn--chatbot .ai-chat-bubble a { color: var(--ai-user-bubble); }

/* Inline code */
.ai-chat-bubble code {
  font-family: var(--ai-mono);
  font-size: 0.88em;
  background: rgba(135, 144, 154, 0.18);
  padding: 0.12em 0.36em;
  border-radius: 5px;
}
.ai-chat-turn--user .ai-chat-bubble code {
  background: rgba(255, 255, 255, 0.22);
}

/* Fenced code blocks: visible, escaped, scrollable */
.ai-chat-bubble pre {
  background: var(--ai-code-bg);
  color: var(--ai-code-text);
  padding: 14px 16px;
  border-radius: 10px;
  overflow-x: auto;
  margin: 0 0 0.7em;
}
.ai-chat-bubble pre code {
  background: none;
  padding: 0;
  font-size: 0.85em;
  color: inherit;
  white-space: pre;
}

.ai-chat-bubble table {
  border-collapse: collapse;
  margin: 0 0 0.7em;
  font-size: 0.92em;
}
.ai-chat-bubble th,
.ai-chat-bubble td {
  border: 1px solid var(--ai-border);
  padding: 6px 10px;
  text-align: left;
}

@media (max-width: 520px) {
  .ai-chat-turn { max-width: 100%; }
  .ai-chat-log { padding: 16px; }
}

@media (prefers-reduced-motion: reduce) {
  .ai-chat-page * { animation: none !important; transition: none !important; }
}
"""




_THEME_DARK = r"""/* aichat-template.css — DARK theme
 * A swap-in stylesheet for aichatprocess.py. Copy it to aichat-template.css
 * (or pass --css-template) and run with --write-css overwrite.
 * All rules scoped under .ai-chat-page.
 */

.ai-chat-page {
  --ai-bg: #0f1419;
  --ai-window: #161b22;
  --ai-border: #2a313c;
  --ai-user-bubble: #2f81f7;
  --ai-user-text: #ffffff;
  --ai-bot-bubble: #21262d;
  --ai-bot-text: #e6edf3;
  --ai-role: #7d8590;
  --ai-code-bg: #0a0d12;
  --ai-code-text: #d6e0ea;
  --ai-radius: 14px;
  --ai-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --ai-mono: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace;

  box-sizing: border-box;
  display: flex; justify-content: center;
  padding: 24px 16px;
  background: var(--ai-bg);
  font-family: var(--ai-font);
  color: var(--ai-bot-text);
  line-height: 1.55;
}
.ai-chat-page *, .ai-chat-page *::before, .ai-chat-page *::after { box-sizing: border-box; }

.ai-chat-window {
  width: 100%; max-width: 760px;
  background: var(--ai-window);
  border: 1px solid var(--ai-border);
  border-radius: var(--ai-radius);
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.3), 0 16px 40px rgba(0,0,0,0.45);
}
.ai-chat-log { display: flex; flex-direction: column; gap: 18px; padding: 24px; }
.ai-chat-turn { display: flex; flex-direction: column; max-width: 85%; }
.ai-chat-turn--user { align-self: flex-end; align-items: flex-end; }
.ai-chat-turn--chatbot { align-self: flex-start; align-items: flex-start; }
.ai-chat-role {
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase; color: var(--ai-role); margin: 0 4px 4px;
}
.ai-chat-bubble { padding: 12px 16px; border-radius: var(--ai-radius); overflow-wrap: anywhere; }
.ai-chat-turn--user .ai-chat-bubble { background: var(--ai-user-bubble); color: var(--ai-user-text); border-bottom-right-radius: 4px; }
.ai-chat-turn--chatbot .ai-chat-bubble { background: var(--ai-bot-bubble); color: var(--ai-bot-text); border-bottom-left-radius: 4px; }
.ai-chat-bubble > :first-child { margin-top: 0; }
.ai-chat-bubble > :last-child { margin-bottom: 0; }
.ai-chat-bubble p { margin: 0 0 0.7em; }
.ai-chat-bubble h1, .ai-chat-bubble h2, .ai-chat-bubble h3, .ai-chat-bubble h4 { margin: 0.6em 0 0.4em; line-height: 1.3; }
.ai-chat-bubble ul, .ai-chat-bubble ol { margin: 0 0 0.7em; padding-left: 1.4em; }
.ai-chat-bubble li { margin: 0.2em 0; }
.ai-chat-bubble a { color: inherit; text-decoration: underline; }
.ai-chat-turn--chatbot .ai-chat-bubble a { color: #79c0ff; }
.ai-chat-bubble code { font-family: var(--ai-mono); font-size: 0.88em; background: rgba(125,133,144,0.22); padding: 0.12em 0.36em; border-radius: 5px; }
.ai-chat-turn--user .ai-chat-bubble code { background: rgba(255,255,255,0.2); }
.ai-chat-bubble pre { background: var(--ai-code-bg); color: var(--ai-code-text); padding: 14px 16px; border-radius: 10px; overflow-x: auto; margin: 0 0 0.7em; border: 1px solid var(--ai-border); }
.ai-chat-bubble pre code { background: none; padding: 0; font-size: 0.85em; color: inherit; white-space: pre; }
.ai-chat-bubble table { border-collapse: collapse; margin: 0 0 0.7em; font-size: 0.92em; }
.ai-chat-bubble th, .ai-chat-bubble td { border: 1px solid var(--ai-border); padding: 6px 10px; text-align: left; }
@media (max-width: 520px) { .ai-chat-turn { max-width: 100%; } .ai-chat-log { padding: 16px; } }
@media (prefers-reduced-motion: reduce) { .ai-chat-page * { animation: none !important; transition: none !important; } }
"""

_THEME_MINIMAL = r"""/* aichat-template.css — MINIMAL theme
 * Flat, borderless, typographic. No bubbles — speaker labels carry the
 * structure. Scoped under .ai-chat-page.
 */

.ai-chat-page {
  --ai-bg: #ffffff;
  --ai-ink: #1a1a1a;
  --ai-user-ink: #1a1a1a;
  --ai-role: #999999;
  --ai-rule: #ececec;
  --ai-code-bg: #f5f5f5;
  --ai-code-text: #1a1a1a;
  --ai-font: "Helvetica Neue", Helvetica, Arial, sans-serif;
  --ai-mono: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace;

  box-sizing: border-box;
  display: flex; justify-content: center;
  padding: 32px 16px;
  background: var(--ai-bg);
  font-family: var(--ai-font);
  color: var(--ai-ink);
  line-height: 1.7;
}
.ai-chat-page *, .ai-chat-page *::before, .ai-chat-page *::after { box-sizing: border-box; }

.ai-chat-window { width: 100%; max-width: 680px; background: var(--ai-bg); }
.ai-chat-log { display: flex; flex-direction: column; gap: 0; }

.ai-chat-turn {
  display: block; max-width: 100%;
  padding: 22px 0;
  border-bottom: 1px solid var(--ai-rule);
}
.ai-chat-turn:last-child { border-bottom: none; }

.ai-chat-role {
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.16em;
  text-transform: uppercase; color: var(--ai-role); margin: 0 0 8px;
}
.ai-chat-turn--user .ai-chat-role { color: #1a1a1a; }

.ai-chat-bubble { padding: 0; background: none; }
.ai-chat-turn--user .ai-chat-bubble { font-weight: 500; }
.ai-chat-bubble > :first-child { margin-top: 0; }
.ai-chat-bubble > :last-child { margin-bottom: 0; }
.ai-chat-bubble p { margin: 0 0 0.7em; }
.ai-chat-bubble h1, .ai-chat-bubble h2, .ai-chat-bubble h3, .ai-chat-bubble h4 { margin: 0.6em 0 0.4em; line-height: 1.3; }
.ai-chat-bubble ul, .ai-chat-bubble ol { margin: 0 0 0.7em; padding-left: 1.3em; }
.ai-chat-bubble li { margin: 0.2em 0; }
.ai-chat-bubble a { color: #1a1a1a; text-decoration: underline; text-underline-offset: 2px; }
.ai-chat-bubble code { font-family: var(--ai-mono); font-size: 0.88em; background: var(--ai-code-bg); padding: 0.12em 0.36em; border-radius: 3px; }
.ai-chat-bubble pre { background: var(--ai-code-bg); color: var(--ai-code-text); padding: 14px 16px; border-radius: 4px; overflow-x: auto; margin: 0 0 0.7em; border-left: 2px solid #1a1a1a; }
.ai-chat-bubble pre code { background: none; padding: 0; font-size: 0.85em; color: inherit; white-space: pre; }
.ai-chat-bubble table { border-collapse: collapse; margin: 0 0 0.7em; font-size: 0.92em; }
.ai-chat-bubble th, .ai-chat-bubble td { border: 1px solid var(--ai-rule); padding: 6px 10px; text-align: left; }
@media (prefers-reduced-motion: reduce) { .ai-chat-page * { animation: none !important; transition: none !important; } }
"""

_THEME_WARM = r"""/* aichat-template.css — WARM theme
 * Soft paper background, rounded warm bubbles, friendly. Scoped under .ai-chat-page.
 */

.ai-chat-page {
  --ai-bg: #f7f1e8;
  --ai-window: #fffdf9;
  --ai-border: #ece2d2;
  --ai-user-bubble: #c9622f;
  --ai-user-text: #fffaf4;
  --ai-bot-bubble: #f0e7d8;
  --ai-bot-text: #3b3326;
  --ai-role: #a7937a;
  --ai-code-bg: #2c2519;
  --ai-code-text: #f2e9d8;
  --ai-radius: 20px;
  --ai-font: "Avenir Next", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --ai-mono: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace;

  box-sizing: border-box;
  display: flex; justify-content: center;
  padding: 28px 16px;
  background: var(--ai-bg);
  font-family: var(--ai-font);
  color: var(--ai-bot-text);
  line-height: 1.6;
}
.ai-chat-page *, .ai-chat-page *::before, .ai-chat-page *::after { box-sizing: border-box; }

.ai-chat-window {
  width: 100%; max-width: 720px;
  background: var(--ai-window);
  border: 1px solid var(--ai-border);
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(120,90,50,0.06), 0 14px 36px rgba(120,90,50,0.12);
}
.ai-chat-log { display: flex; flex-direction: column; gap: 20px; padding: 28px; }
.ai-chat-turn { display: flex; flex-direction: column; max-width: 84%; }
.ai-chat-turn--user { align-self: flex-end; align-items: flex-end; }
.ai-chat-turn--chatbot { align-self: flex-start; align-items: flex-start; }
.ai-chat-role {
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--ai-role); margin: 0 6px 5px;
}
.ai-chat-bubble { padding: 13px 18px; border-radius: var(--ai-radius); overflow-wrap: anywhere; }
.ai-chat-turn--user .ai-chat-bubble { background: var(--ai-user-bubble); color: var(--ai-user-text); border-bottom-right-radius: 6px; }
.ai-chat-turn--chatbot .ai-chat-bubble { background: var(--ai-bot-bubble); color: var(--ai-bot-text); border-bottom-left-radius: 6px; }
.ai-chat-bubble > :first-child { margin-top: 0; }
.ai-chat-bubble > :last-child { margin-bottom: 0; }
.ai-chat-bubble p { margin: 0 0 0.7em; }
.ai-chat-bubble h1, .ai-chat-bubble h2, .ai-chat-bubble h3, .ai-chat-bubble h4 { margin: 0.6em 0 0.4em; line-height: 1.3; }
.ai-chat-bubble ul, .ai-chat-bubble ol { margin: 0 0 0.7em; padding-left: 1.4em; }
.ai-chat-bubble li { margin: 0.2em 0; }
.ai-chat-bubble a { color: inherit; text-decoration: underline; }
.ai-chat-turn--chatbot .ai-chat-bubble a { color: var(--ai-user-bubble); }
.ai-chat-bubble code { font-family: var(--ai-mono); font-size: 0.88em; background: rgba(167,147,122,0.22); padding: 0.12em 0.36em; border-radius: 5px; }
.ai-chat-turn--user .ai-chat-bubble code { background: rgba(255,255,255,0.24); }
.ai-chat-bubble pre { background: var(--ai-code-bg); color: var(--ai-code-text); padding: 14px 16px; border-radius: 12px; overflow-x: auto; margin: 0 0 0.7em; }
.ai-chat-bubble pre code { background: none; padding: 0; font-size: 0.85em; color: inherit; white-space: pre; }
.ai-chat-bubble table { border-collapse: collapse; margin: 0 0 0.7em; font-size: 0.92em; }
.ai-chat-bubble th, .ai-chat-bubble td { border: 1px solid var(--ai-border); padding: 6px 10px; text-align: left; }
@media (max-width: 520px) { .ai-chat-turn { max-width: 100%; } .ai-chat-log { padding: 18px; } }
@media (prefers-reduced-motion: reduce) { .ai-chat-page * { animation: none !important; transition: none !important; } }
"""


# Bundled themes, selectable with --theme. The default theme is
# INTERNAL_DEFAULT_CSS above. Precedence at write time:
#   explicit --css-template file  >  --theme name  >  default
THEMES = {
    "default": INTERNAL_DEFAULT_CSS,
    "dark": _THEME_DARK,
    "minimal": _THEME_MINIMAL,
    "warm": _THEME_WARM,
}


# --------------------------------------------------------------------------- #
# CSS writing logic
# --------------------------------------------------------------------------- #

def resolve_css(write_mode: str, css_path: Path, template_path: Path,
                theme: str = "default") -> str:
    """Apply --write-css logic. Returns a short status string for reporting.

    Precedence when writing: an existing --css-template file wins; otherwise the
    named --theme is used; 'default' means the built-in default stylesheet.
    """
    if write_mode == "never":
        return "left CSS untouched (--write-css never)"

    if write_mode == "if-missing" and css_path.exists():
        return f"kept existing {css_path.name} (--write-css if-missing)"

    # We are writing (overwrite, or if-missing with no file present).
    if template_path.exists():
        css_path.write_text(template_path.read_text(encoding="utf-8"),
                            encoding="utf-8")
        return f"wrote {css_path.name} from template {template_path.name}"

    css = THEMES.get(theme, INTERNAL_DEFAULT_CSS)
    css_path.write_text(css, encoding="utf-8")
    if theme != "default":
        return f"wrote {css_path.name} from built-in '{theme}' theme"
    return f"wrote {css_path.name} from internal default"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a marked-up AI chat transcript into a complete "
                    "HTML page plus CSS.",
    )
    parser.add_argument("--source", default=None,
                        help=f"Input transcript (default: {DEFAULT_SOURCE}, "
                             f"falling back to {DEFAULT_SOURCE_FALLBACK})")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help=f"Output HTML file (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--css", default=DEFAULT_CSS,
                        help=f"CSS file linked by the HTML (default: {DEFAULT_CSS})")
    parser.add_argument("--css-template", default=DEFAULT_CSS_TEMPLATE,
                        help="Optional CSS template copied when writing CSS "
                             f"(default: {DEFAULT_CSS_TEMPLATE})")
    parser.add_argument("--theme", choices=["default", "dark", "minimal", "warm"],
                        default="default",
                        help="Built-in look to use when writing CSS. An existing "
                             "--css-template file takes precedence (default: default).")
    parser.add_argument("--write-css", choices=["never", "if-missing", "overwrite"],
                        default="if-missing",
                        help="When to write the CSS file (default: if-missing)")
    parser.add_argument("--word-output", default=None,
                        help="Also write a Word-friendly transcript to this file "
                             "(an .html you can copy-paste into Word). Optional.")
    parser.add_argument("--word-style", choices=["default", "compact", "plain"],
                        default="default",
                        help="Look for the Word transcript (default, compact, "
                             "plain). Only applies with --word-output.")
    parser.add_argument("--title", default="AI Chat",
                        help="HTML <title> (default: 'AI Chat')")
    args = parser.parse_args(argv)

    # Source resolution. If --source is given, use exactly that. If not,
    # default to aichat.txt, falling back to aichat.md when the .txt is absent.
    if args.source is not None:
        source_path = Path(args.source)
        if not source_path.exists():
            sys.stderr.write(f"Error: source file not found: {source_path}\n")
            return 1
    else:
        primary = Path(DEFAULT_SOURCE)
        fallback = Path(DEFAULT_SOURCE_FALLBACK)
        if primary.exists():
            source_path = primary
        elif fallback.exists():
            source_path = fallback
        else:
            sys.stderr.write(
                f"Error: no source file found. Looked for {DEFAULT_SOURCE} "
                f"then {DEFAULT_SOURCE_FALLBACK} in the current folder.\n"
                f"Create one, or pass --source <file>.\n"
            )
            return 1

    output_path = Path(args.output)
    css_path = Path(args.css)
    template_path = Path(args.css_template)

    text = source_path.read_text(encoding="utf-8")
    turns = parse_transcript(text)
    if not turns:
        sys.stderr.write(
            "Error: no turns found. Each turn must start with a line "
            "containing [USER] or [CHATBOT].\n"
        )
        return 1

    # The HTML links to the CSS by its filename relative to the HTML file.
    css_href = os.path.relpath(css_path, output_path.parent) \
        if output_path.parent != Path(".") else css_path.name
    page = build_html(turns, css_href=css_href, title=args.title)
    output_path.write_text(page, encoding="utf-8")

    css_status = resolve_css(args.write_css, css_path, template_path,
                             theme=args.theme)

    print(f"Read {source_path}  ({len(turns)} turns)")
    print(f"Wrote {output_path}")
    print(f"CSS:  {css_status}")

    # Optional Word-friendly transcript alongside the normal page.
    if args.word_output:
        word_path = Path(args.word_output)
        word_css_path = word_path.with_name(word_path.stem + ".css")
        word_css_href = os.path.relpath(word_css_path, word_path.parent) \
            if word_path.parent != Path(".") else word_css_path.name
        word_page = build_word_html(turns, css_href=word_css_href,
                                    title=args.title, word_style=args.word_style)
        word_path.write_text(word_page, encoding="utf-8")
        word_css_path.write_text(build_word_css(args.word_style), encoding="utf-8")
        print(f"Word: wrote {word_path} (+ {word_css_path.name}, "
              f"'{args.word_style}' style)")
        if args.theme != "default":
            print(f"Note: --theme '{args.theme}' styles the chat page; the Word "
                  f"version uses its own '{args.word_style}' style.")
    elif args.word_style != "default":
        print("Note: --word-style was set but --word-output was not, so no Word "
              "file was written.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
