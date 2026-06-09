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


# --------------------------------------------------------------------------- #
# CSS writing logic
# --------------------------------------------------------------------------- #

def resolve_css(write_mode: str, css_path: Path, template_path: Path) -> str:
    """Apply --write-css logic. Returns a short status string for reporting."""
    if write_mode == "never":
        return "left CSS untouched (--write-css never)"

    if write_mode == "if-missing" and css_path.exists():
        return f"kept existing {css_path.name} (--write-css if-missing)"

    # We are writing (overwrite, or if-missing with no file present).
    if template_path.exists():
        css_path.write_text(template_path.read_text(encoding="utf-8"),
                            encoding="utf-8")
        return f"wrote {css_path.name} from template {template_path.name}"

    css_path.write_text(INTERNAL_DEFAULT_CSS, encoding="utf-8")
    return f"wrote {css_path.name} from internal default (no template found)"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a marked-up AI chat transcript into a complete "
                    "HTML page plus CSS.",
    )
    parser.add_argument("--source", default=DEFAULT_SOURCE,
                        help=f"Input transcript (default: {DEFAULT_SOURCE})")
    parser.add_argument("--output", default=DEFAULT_OUTPUT,
                        help=f"Output HTML file (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--css", default=DEFAULT_CSS,
                        help=f"CSS file linked by the HTML (default: {DEFAULT_CSS})")
    parser.add_argument("--css-template", default=DEFAULT_CSS_TEMPLATE,
                        help="Optional CSS template copied when writing CSS "
                             f"(default: {DEFAULT_CSS_TEMPLATE})")
    parser.add_argument("--write-css", choices=["never", "if-missing", "overwrite"],
                        default="if-missing",
                        help="When to write the CSS file (default: if-missing)")
    parser.add_argument("--title", default="AI Chat",
                        help="HTML <title> (default: 'AI Chat')")
    args = parser.parse_args(argv)

    source_path = Path(args.source)
    output_path = Path(args.output)
    css_path = Path(args.css)
    template_path = Path(args.css_template)

    if not source_path.exists():
        sys.stderr.write(f"Error: source file not found: {source_path}\n")
        return 1

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

    css_status = resolve_css(args.write_css, css_path, template_path)

    print(f"Read {source_path}  ({len(turns)} turns)")
    print(f"Wrote {output_path}")
    print(f"CSS:  {css_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
