# Workflow overview

How a chat becomes a styled HTML page, in five stages. Stages 1–2 are content
editing in Markdown; stages 3–5 are conversion and presentation.

## Stage 1 — Capture the chat in Markdown

Copy the conversation turn by turn into a plain Markdown file. Introduce each
human turn with a line containing `[USER]` and each chatbot turn with a line
containing `[CHATBOT]`. The conventional form is:

```text
# **[USER]**
...your message...
# **[CHATBOT]**
...the reply...
```

Basic Markdown is preserved: paragraphs, lists, links, headings, and code
blocks. Images, attachments, and embedded media are ignored.

## Stage 2 — Edit the Markdown transcript

The Markdown file is the main editing document. Tidy wording, remove unwanted
material, shorten long answers, or adjust the example while still seeing the
conversation structure clearly. The role lines keep the turns easy to scan.

## Stage 3 — Convert to HTML and CSS

Run `aichat.py` to turn the transcript into a complete HTML page and a separate
CSS file. The page shows the chat with distinct treatment for user and chatbot
turns; the CSS makes it look like a generic chat window. See the
[processor requirements](requirements.md) for the exact behaviour and options.

## Stage 4 — Edit the HTML page

Open the generated page in an HTML editor or browser preview to make final
presentation edits with the CSS applied and the layout visible. This stage is
for visual refinement once the Markdown has done the content work.

## Stage 5 — Reuse the HTML snippet

Inside the generated page, the reusable chat section sits between clearly
labelled `COPY CHAT HTML START` / `END` comment blocks, so the exact block to
copy into another page is easy to find. When you copy the snippet, also bring
the CSS: either link `aichat.css` from the target page or paste its rules into
the site's existing stylesheet. The CSS is scoped under `.ai-chat-page`, so it
coexists with a page's own styles.
