# AI Chat to HTML

AI Chat to HTML converts a manually marked AI conversation into a complete HTML page and a separate CSS file.

The main workflow is simple: create `aichat.md`, mark each turn with `# **[USER]**` or `# **[CHATBOT]**`, run the processor, then open `aichat.html`.

## Quick start

```bash
python3 aichatprocess.py
```

By default the processor reads `aichat.md`, writes `aichat.html`, and links to `aichat.css`. If `aichat.md` is not found, the processor will also look for `aichat.txt` for backwards compatibility.

## Conversation Collector Prompt

You can create the source transcript manually, or use the Conversation Collector Prompt at the end of a chatbot conversation. The collector asks the chatbot to produce a draft transcript using the correct markers.

The generated transcript should still be checked before processing.

## CSS

CSS is written from `aichat-template.css` when that file exists. If the template is missing, the processor uses an internal default CSS backup.

## Image handling

External Markdown image links are preserved. Local, pasted, uploaded, internal, or non-portable image references are replaced with a placeholder.
