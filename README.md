# AI Chat to HTML

Turn a marked-up chat transcript into a complete, self-contained HTML page that
looks like a generic chat window — plus a separate, reusable CSS file.

It's built for a simple workflow: paste a conversation into a Markdown file,
edit it as text, then convert it to a finished web page you can publish or copy
into another site.

**[Visit the site](https://markbeachill.github.io/ai-chat-to-html/)** · [Instructions](https://markbeachill.github.io/ai-chat-to-html/instructions.html) · [Example](https://markbeachill.github.io/ai-chat-to-html/example.html) · [Collector](https://markbeachill.github.io/ai-chat-to-html/collector.html)
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

## Online converter

The documentation site also includes a browser-only Online Converter. It lets a user paste a marked transcript, choose chat-style or Word-friendly HTML, choose inline or separate CSS, preview the result, and copy the generated HTML. This is a quick-use companion to the Python processor; it does not replace the local workflow.

## Conversation Collector Prompt

You can build the source transcript manually, or use the Conversation Collector Prompt as an assisted shortcut. Paste the prompt at the end of a completed chatbot conversation and ask the AI to return a draft `aichat.md` transcript using `# **[USER]**` and `# **[CHATBOT]**`.

The result should still be checked before conversion, especially for missing turns, code blocks, links and images. See [conversation-collector-prompt.md](conversation-collector-prompt.md) or the [Collector page](https://markbeachill.github.io/ai-chat-to-html/collector.html).

## Options

| Setting | Default | Purpose |
| --- | --- | --- |
| `--source` | `aichat.txt` | Input transcript |
| `--output` | `aichat.html` | Output HTML file |
| `--css` | `aichat.css` | CSS file the HTML links to |
| `--css-template` | `aichat-template.css` | Optional template copied when writing CSS |
| `--theme` | `default` | Built-in look: `default`, `dark`, `minimal`, `warm` |
| `--write-css` | `if-missing` | `never`, `if-missing`, or `overwrite` |
| `--word-output` | — | Also write a Word-friendly transcript to this file |
| `--word-style` | `default` | Word look: `default`, `compact`, `plain` |
| `--math` | off | Render `$…$` / `$$…$$` with KaTeX (web page only) |
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

Markdown images with a web address (`![](https://…)`) are passed through; local
or pasted images become a small "[image not included]" placeholder, since the
tool never loads local files. It does **not** handle attachments, native LLM
export formats, automatic role detection, or math/LaTeX — math written as plain
text stays plain text.

## Themes and a Word version

Pick a built-in look with `--theme`:

```bash
python3 aichatprocess.py --theme dark --write-css overwrite
```

The bundled themes are `default`, `dark`, `minimal` and `warm`. An explicit
`--css-template` file still takes precedence, so you can start from a theme and
customise it.

To get a copy you can paste into Microsoft Word, add `--word-output`:

```bash
python3 aichatprocess.py --word-output --word-style compact
```

Used on its own, `--word-output` names the file from the main output
(`aichat.html` becomes `aichat-word.html`); you can also pass an explicit name.
Word ignores chat bubbles, alignment and linked stylesheets, so this is a
separate, plainer build: a clean transcript with styling written inline on each
element (which is what survives the paste). It's produced by the tool itself —
no external converter or extra dependency. Three looks are available via
`--word-style`: `default`, `compact` and `plain`.

Themes and Word looks are independent: `--theme` styles the chat page,
`--word-style` styles the Word page. The screen themes don't carry into Word
(its dark backgrounds and bubbles wouldn't survive), so the Word output has its
own neutral looks instead.

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
   `https://markbeachill.github.io/ai-chat-to-html/` — a seven-page site
   (home, setup, instructions, example, word, styling, reference) aimed at end users, with
   developer reference included.

## Repository layout

```
ai-chat-to-html/
├── README.md              This file
├── LICENSE                MIT
├── requirements.txt       Pins Python-Markdown
├── aichatprocess.py       The processor
├── aichat-template.css    Editable CSS template
├── conversation-collector-prompt.md  Optional prompt for assisted transcript capture
├── build-demos.sh         Regenerates the site's example pages
├── build-downloads.sh     Builds the download zips
├── docs/                  The project website (served by GitHub Pages)
│   ├── index.html          Home — the two outputs, shown live
│   ├── setup.html          Installing Python (for newcomers)
│   ├── instructions.html   End-user guide (the three steps)
│   ├── collector.html      Copyable Conversation Collector Prompt
│   ├── example.html        Full worked example, input and output
│   ├── word.html           The Word version, explained
│   ├── styling.html        Themes and how to restyle
│   ├── reference.html      Developer reference / spec
│   ├── markdown-guide.html Quick Markdown reference
│   ├── download.html       Download page
│   ├── about.html          About / creator / repository
│   ├── downloads/          Prebuilt zips offered for download
│   ├── site.css            Site styles
│   ├── workflow.md         Plain-text source: the workflow
│   ├── requirements.md     Plain-text source: the spec
│   └── example/            Generated demo output shown by the site
│       ├── aichat.txt  aichat.html  aichat.css  aichat-word.html
│       ├── themes/         Theme demo pages
│       └── word/           Word-style demo pages
    ├── aichat.txt  aichat.html  aichat.css
    └── themes/             Alternate stylesheets + rendered demos
```


## License

MIT — see [LICENSE](LICENSE). Update the copyright line with your name.
