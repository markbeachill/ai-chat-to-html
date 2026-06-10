#!/usr/bin/env python3
"""
AI Chat to HTML processor

Default behaviour:
  Reads:  aichat.md
  Writes: aichat.html
  CSS:    aichat.css

Input markers:
  # **[USER]**
  # **[CHATBOT]**
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

USER_MARKER = "# **[USER]**"
CHATBOT_MARKER = "# **[CHATBOT]**"

INTERNAL_DEFAULT_CSS = """
:root {
  --chat-page-bg: #f4f4f5;
  --chat-window-bg: #ffffff;
  --chat-border: #d4d4d8;
  --chat-text: #18181b;
  --chat-muted: #52525b;
  --user-bg: #e0f2fe;
  --chatbot-bg: #f1f5f9;
  --code-bg: #111827;
  --code-text: #f9fafb;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  padding: 2rem;
  background: var(--chat-page-bg);
  color: var(--chat-text);
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.55;
}

.page-shell { max-width: 900px; margin: 0 auto; }
.page-title { margin: 0 0 1rem; font-size: 1.75rem; }
.copy-note { margin: 0 0 1rem; color: var(--chat-muted); font-size: 0.95rem; }

.ai-chat-window {
  background: var(--chat-window-bg);
  border: 1px solid var(--chat-border);
  border-radius: 1rem;
  padding: 1.25rem;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.chat-turn {
  margin: 1rem 0;
  padding: 1rem;
  border-radius: 0.85rem;
  border: 1px solid var(--chat-border);
}
.chat-turn:first-child { margin-top: 0; }
.chat-turn:last-child { margin-bottom: 0; }
.chat-turn-user { background: var(--user-bg); }
.chat-turn-chatbot { background: var(--chatbot-bg); }

.chat-role {
  margin: 0 0 0.5rem;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--chat-muted);
}

.chat-body > :first-child { margin-top: 0; }
.chat-body > :last-child { margin-bottom: 0; }
.chat-body img { max-width: 100%; height: auto; border-radius: 0.5rem; }

.chat-body pre {
  overflow-x: auto;
  padding: 1rem;
  border-radius: 0.65rem;
  background: var(--code-bg);
  color: var(--code-text);
}
.chat-body code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }
.chat-body :not(pre) > code { padding: 0.15rem 0.3rem; border-radius: 0.25rem; background: rgba(15, 23, 42, 0.08); }
.chat-body blockquote { margin-left: 0; padding-left: 1rem; border-left: 4px solid var(--chat-border); color: var(--chat-muted); }
""".lstrip()


@dataclass
class Turn:
    role: str
    content: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a marked AI chat transcript into an HTML page and optional CSS file.")
    parser.add_argument("--source", default="aichat.md", help="Source transcript file. Default: aichat.md")
    parser.add_argument("--output", default="aichat.html", help="Output HTML file. Default: aichat.html")
    parser.add_argument("--css", default="aichat.css", help="CSS file linked by the HTML. Default: aichat.css")
    parser.add_argument("--css-template", default="aichat-template.css", help="Optional CSS template file. Default: aichat-template.css")
    parser.add_argument("--write-css", choices=["never", "if-missing", "overwrite"], default="if-missing", help="CSS writing behaviour. Default: if-missing")
    parser.add_argument("--title", default="AI Chat Example", help="HTML page title. Default: AI Chat Example")
    return parser.parse_args()


def parse_transcript(text: str) -> List[Turn]:
    turns: List[Turn] = []
    current_role: str | None = None
    current_lines: List[str] = []

    def close_current_turn() -> None:
        nonlocal current_role, current_lines
        if current_role is None:
            return
        content = "\n".join(current_lines).strip()
        if content:
            turns.append(Turn(role=current_role, content=content))
        current_role = None
        current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == USER_MARKER:
            close_current_turn()
            current_role = "user"
            current_lines = []
            continue
        if line == CHATBOT_MARKER:
            close_current_turn()
            current_role = "chatbot"
            current_lines = []
            continue
        if current_role is not None:
            current_lines.append(raw_line)

    close_current_turn()
    return turns


def normalise_images(markdown_text: str) -> str:
    """Keep external Markdown images; replace non-portable image references with a placeholder."""
    def replace_image(match: re.Match[str]) -> str:
        alt_text = match.group(1).strip()
        target = match.group(2).strip()
        if target.startswith(("http://", "https://")):
            return match.group(0)
        label = alt_text or "image"
        return f"[Image present in original chat — not included: {label}]"
    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace_image, markdown_text)


def markdown_to_html(markdown_text: str) -> str:
    markdown_text = normalise_images(markdown_text)
    try:
        import markdown  # type: ignore
        return markdown.markdown(markdown_text, extensions=["extra", "fenced_code", "tables", "sane_lists"], output_format="html5")
    except Exception:
        return basic_markdown_to_html(markdown_text)


def basic_markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    output: List[str] = []
    paragraph: List[str] = []
    in_code = False
    code_lines: List[str] = []
    list_type: str | None = None
    quote_lines: List[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(line.strip() for line in paragraph)
            output.append(f"<p>{inline_markdown(text)}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_type
        if list_type:
            output.append(f"</{list_type}>")
            list_type = None

    def flush_quote() -> None:
        nonlocal quote_lines
        if quote_lines:
            output.append(f"<blockquote><p>{inline_markdown(' '.join(quote_lines))}</p></blockquote>")
            quote_lines = []

    def flush_code() -> None:
        nonlocal code_lines
        output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
        code_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph(); flush_list(); flush_quote()
            if in_code:
                flush_code(); in_code = False
            else:
                in_code = True; code_lines = []
            continue
        if in_code:
            code_lines.append(line); continue
        if not stripped:
            flush_paragraph(); flush_list(); flush_quote(); continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph(); flush_list(); flush_quote()
            level = len(heading.group(1))
            output.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>")
            continue
        if stripped.startswith(">"):
            flush_paragraph(); flush_list(); quote_lines.append(stripped.lstrip(">").strip()); continue
        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        if bullet:
            flush_paragraph(); flush_quote()
            if list_type != "ul": flush_list(); output.append("<ul>"); list_type = "ul"
            output.append(f"<li>{inline_markdown(bullet.group(1))}</li>"); continue
        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered:
            flush_paragraph(); flush_quote()
            if list_type != "ol": flush_list(); output.append("<ol>"); list_type = "ol"
            output.append(f"<li>{inline_markdown(ordered.group(1))}</li>"); continue
        flush_list(); flush_quote(); paragraph.append(line)

    if in_code: flush_code()
    flush_paragraph(); flush_list(); flush_quote()
    return "\n".join(output)


def inline_markdown(text: str) -> str:
    # Convert external images before ordinary links.
    text = re.sub(
        r"!\[([^\]]*)\]\((https?://[^)]+)\)",
        lambda m: f'<img src="{html.escape(m.group(2), quote=True)}" alt="{html.escape(m.group(1), quote=True)}">',
        text,
    )
    escaped = html.escape(text, quote=False)
    # Undo escaped image tags created above.
    escaped = escaped.replace("&lt;img ", "<img ").replace("&gt;", ">")
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', escaped)
    return escaped


def render_turn(turn: Turn) -> str:
    role_label = "User" if turn.role == "user" else "Chatbot"
    role_class = "chat-turn-user" if turn.role == "user" else "chat-turn-chatbot"
    body_html = markdown_to_html(turn.content)
    return f'''    <section class="chat-turn {role_class}">
      <p class="chat-role">{role_label}</p>
      <div class="chat-body">
{indent_html(body_html, 8)}
      </div>
    </section>'''


def indent_html(fragment: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line.strip() else line for line in fragment.splitlines())


def copy_marker(label: str) -> str:
    block = "\n".join(["<!-- ******************************************** -->"] * 5)
    return f"""{block}
<!-- {label:<42} -->
{block}"""


def render_html_page(turns: Iterable[Turn], title: str, css_path: str) -> str:
    chat_html = "\n\n".join(render_turn(turn) for turn in turns)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{html.escape(css_path, quote=True)}">
</head>
<body>
  <div class="page-shell">
    <h1 class="page-title">{html.escape(title)}</h1>
    <p class="copy-note">The reusable chat section is clearly marked in the HTML source.</p>

{copy_marker("COPY CHAT HTML START")}
    <main class="ai-chat-window" aria-label="AI chat example">
{chat_html}
    </main>
{copy_marker("COPY CHAT HTML END")}

  </div>
</body>
</html>
'''


def write_css(css_file: Path, css_template: Path, mode: str) -> None:
    if mode == "never":
        return
    if mode == "if-missing" and css_file.exists():
        return
    if css_template.exists():
        shutil.copyfile(css_template, css_file)
    else:
        css_file.write_text(INTERNAL_DEFAULT_CSS, encoding="utf-8")


def main() -> int:
    args = parse_args()
    source = Path(args.source)
    output = Path(args.output)
    css_file = Path(args.css)
    css_template = Path(args.css_template)

    if not source.exists():
        fallback = Path("aichat.txt")
        if args.source == "aichat.md" and fallback.exists():
            source = fallback
        else:
            raise SystemExit(f"Source file not found: {source}")

    turns = parse_transcript(source.read_text(encoding="utf-8"))
    if not turns:
        raise SystemExit(f"No chat turns found. Expected markers: {USER_MARKER!r} and {CHATBOT_MARKER!r}")

    output.write_text(render_html_page(turns, args.title, css_file.name), encoding="utf-8")
    write_css(css_file, css_template, args.write_css)

    print(f"Read:     {source}")
    print(f"Wrote:    {output}")
    print(f"Linked:   {css_file}")
    print(f"Turns:    {len(turns)}")
    print(f"CSS mode: {args.write_css}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
