# Processor requirements

`aichat.py` converts a marked-up chat transcript into a complete HTML page and,
optionally, a CSS file. It preserves the Markdown inside each turn, converts it
to HTML, and wraps the turns so they display like a generic chat window.

## Files

Defaults, all assumed to be in the current folder unless overridden:

| Role | Default | Setting |
| --- | --- | --- |
| Source transcript | `aichat.txt` | `--source` |
| Output HTML | `aichat.html` | `--output` |
| CSS linked by the HTML | `aichat.css` | `--css` |
| Optional CSS template | `aichat-template.css` | `--css-template` |

`--title` sets the HTML `<title>` (default `AI Chat`).

## Transcript format

Each turn begins with a line that contains a role token: `[USER]` or
`[CHATBOT]`. Matching is case-insensitive and flexible — the rest of the line
(the `#`, the `**`, any punctuation) is ignored, so `# **[USER]**`, `[user]`,
and `## [Chatbot]:` all work. Everything until the next role line is that
turn's body and is treated as Markdown.

Text before the first role line is ignored (with a warning).

## Conversion rules

- Turn bodies are converted with [Python-Markdown](https://pypi.org/project/Markdown/)
  (`fenced_code`, `tables`, `sane_lists`, `nl2br`).
- Fenced code blocks are rendered as **visible, escaped code** — never
  interpreted as page markup. A transcript containing HTML examples stays safe.
- The code block's language tag is preserved as a CSS class so a syntax
  highlighter can be added later; none is bundled.
- **No math/LaTeX handling.** Math written as plain text stays plain text.
- Images, attachments, native LLM exports, and automatic role detection are out
  of scope.

## CSS behaviour (`--write-css`)

Safe by default. The default mode is `if-missing`.

| Mode | Behaviour |
| --- | --- |
| `never` | Leave the CSS file untouched; only link to it. Template ignored. |
| `if-missing` | Write the CSS file only if it does not already exist. |
| `overwrite` | Always (re)write the CSS file. |

When writing (either `overwrite`, or `if-missing` with no file present): if the
template file exists it is copied verbatim into the CSS file; otherwise an
internal default stylesheet built into the script is written. This means the
tool works on a clean folder, and the design can be customised later by creating
or editing the template.

The generated CSS is scoped under `.ai-chat-page` so the snippet can be pasted
into pages with their own, differing CSS. This is scoping, not guaranteed
isolation — full isolation would need an iframe or Shadow DOM, which would
defeat the copy-a-snippet goal.

## Output structure

The output is a complete HTML page (not a snippet) that links to the CSS file.
The reusable chat section is wrapped in large repeated comment blocks so it is
easy to find and copy:

```html
<!-- ******************************************** -->
<!-- ******************************************** -->
<!-- ******************************************** -->
<!-- ******************************************** -->
<!-- ******************************************** -->
<!-- COPY CHAT HTML START                         -->
<!-- ******************************************** -->
<!-- ******************************************** -->
<!-- ******************************************** -->
<!-- ******************************************** -->
<!-- ******************************************** -->

<main class="ai-chat-page">
  ...
</main>

<!-- ... matching COPY CHAT HTML END block ... -->
```

## Optional collector prompt

The Conversation Collector Prompt is a documentation/helper feature. It can help a user ask a chatbot to produce a draft marked transcript, but it is not part of the processor and does not change the accepted input format.
