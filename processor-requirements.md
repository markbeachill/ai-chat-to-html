# Processor requirements

The processor converts a manually marked AI chat transcript into a complete HTML page and optional CSS file.

The default source file is `aichat.md`, with `aichat.txt` accepted as a fallback for older workflows. The default output file is `aichat.html`. The default CSS file is `aichat.css`. The optional CSS template file is `aichat-template.css`.

The processor recognises only two turn markers: `# **[USER]**` and `# **[CHATBOT]**`. Everything after a marker belongs to that turn until the next marker.

The processor supports `--source`, `--output`, `--css`, `--css-template`, `--write-css`, and `--title`.

The `--write-css` setting supports `never`, `if-missing`, and `overwrite`. When writing CSS, the processor first looks for the external CSS template. If the template is not available, it writes an internal default CSS backup.

The generated HTML must be a complete page. The reusable chat section must be clearly marked with large repeated HTML comment blocks labelled `COPY CHAT HTML START` and `COPY CHAT HTML END`.

External Markdown image links are preserved. Local, pasted, uploaded, internal, or non-portable image references are replaced with a placeholder.

The processor does not handle native LLM exports, automatic role detection, or embedded media capture.
