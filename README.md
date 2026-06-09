# AI Chat to HTML

Turn a marked-up chat transcript into a complete, self-contained HTML page that
looks like a generic chat window — plus a separate, reusable CSS file.

It's built for a simple workflow: paste a conversation into a Markdown file,
edit it as text, then convert it to a finished web page you can publish or copy
into another site.

**[Visit the site](https://markbeachill.github.io/ai-chat-to-html/)** · [Instructions](https://markbeachill.github.io/ai-chat-to-html/instructions.html) · [Example](https://markbeachill.github.io/ai-chat-to-html/example.html)
[Workflow](docs/workflow.md) · [Requirements](docs/requirements.md)

## Quickstart

```bash
# 1. Install the one dependency
pip install -r requirements.txt

# 2. Put your transcript in aichat.txt, then convert
python3 aichatprocess.py

# Outputs: aichat.html (links to) aichat.css
```

A transcript is plain Markdown with a role line before each turn:

```text
# **[USER]**
Tell me about gravity?
# **[CHATBOT]**
Gravity is the force that attracts objects with mass toward each other...
```

> Tip: you can keep the transcript as `aichat.md` and edit it in a Markdown editor — with no `--source`, the tool uses `aichat.txt` if present, otherwise `aichat.md`.

Open `aichat.html` in a browser and you'll see the conversation laid out as a
chat, with user turns on the right and chatbot turns on the left.

## Options

| Setting | Default | Purpose |
| --- | --- | --- |
| `--source` | `aichat.txt` | Input transcript |
| `--output` | `aichat.html` | Output HTML file |
| `--css` | `aichat.css` | CSS file the HTML links to |
| `--css-template` | `aichat-template.css` | Optional template copied when writing CSS |
| `--write-css` | `if-missing` | `never`, `if-missing`, or `overwrite` |
| `--title` | `AI Chat` | HTML page title |

```bash
python3 aichatprocess.py --source mychat.txt --output mychat.html --write-css overwrite
```

### How the CSS gets written

With `--write-css` set to `if-missing` (default) or `overwrite`, the tool writes
the CSS file by copying `aichat-template.css` if that file exists, or falling
back to a stylesheet built into the script. So it works on a clean folder, and
you can customise the design by editing the template and re-running with
`--write-css overwrite`. With `never`, the CSS file is left untouched.

## What it does and doesn't do

It preserves Markdown inside each turn (paragraphs, lists, links, headings,
tables) and renders fenced code blocks as **visible, escaped code** — so a
transcript full of HTML examples displays safely instead of breaking the page.

It does **not** handle images, attachments, native LLM export formats,
automatic role detection, or math/LaTeX. Math written as plain text stays plain
text.

## Reusing the chat in another page

The generated page wraps its chat section in clearly labelled
`COPY CHAT HTML START` / `END` comment blocks. Copy everything between them into
your target page, and either link `aichat.css` or paste its rules into your
stylesheet. The CSS is scoped under `.ai-chat-page`, so it coexists with a
page's existing styles.

## Publishing with GitHub Pages

This repo is Pages-ready with no build step:

1. Push the repo to GitHub.
2. In the repo: **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to *Deploy from a branch*,
   choose branch `main` and folder `/docs`, and save.
4. After a minute your site is live at
   `https://markbeachill.github.io/ai-chat-to-html/` — a five-page site
   (home, instructions, example, styling, reference) aimed at end users, with
   developer reference included.

## Repository layout

```
ai-chat-to-html/
├── README.md              This file
├── LICENSE                MIT
├── requirements.txt       Pins Python-Markdown
├── aichatprocess.py       The processor
├── aichat-template.css    Editable CSS template
├── sync-example.sh        Copies example/ into docs/ for publishing
├── docs/                  The project website (served by GitHub Pages)
│   ├── index.html          Home — intro + live sample output
│   ├── instructions.html   End-user guide (the five stages)
│   ├── example.html        Full worked example, input and output
│   ├── styling.html        Themes and how to restyle
│   ├── reference.html      Developer reference / spec
│   ├── site.css            Site styles
│   ├── workflow.md         Plain-text source: the five stages
│   ├── requirements.md     Plain-text source: the spec
│   └── example/            Published copy of the example (kept in sync)
└── example/               Canonical tool output (the source of truth)
    ├── aichat.txt  aichat.html  aichat.css
    └── themes/             Alternate stylesheets + rendered demos
```

> **Two copies of `example/`?** The root `example/` is the tool's real output.
> GitHub Pages serves the site from `docs/`, so the site needs its own copy at
> `docs/example/`. After regenerating the example, run `./sync-example.sh` and
> commit both. (If you'd rather not duplicate, you can instead serve Pages from
> the repo root — but then the docs links would need adjusting.)

## License

MIT — see [LICENSE](LICENSE). Update the copyright line with your name.
