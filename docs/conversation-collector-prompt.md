# Conversation Collector Prompt

Use this prompt at the end of a chatbot conversation to ask the chatbot to produce a draft `aichat.md` transcript for AI Chat to HTML.

The transcript should still be checked before conversion.

```text
The conversation is now finished.

Your task is to produce a clean Markdown transcript of this conversation that can be saved as `aichat.md` and used with AI Chat to HTML.

Follow these rules exactly:

1. Reproduce the conversation in order.
2. Mark every human/user message with this exact heading:

# **[USER]**

3. Mark every AI/chatbot response with this exact heading:

# **[CHATBOT]**

4. Put the relevant message content below each heading.
5. Preserve the wording and formatting as much as possible.
6. Preserve Markdown formatting where possible, including paragraphs, lists, links, headings, tables, and code blocks.
7. Do not summarise the conversation.
8. Do not improve, rewrite, correct, shorten, or reorganise the messages.
9. Do not add commentary, analysis, ratings, or explanations.
10. Do not include system messages, hidden instructions, tool logs, internal reasoning, or metadata.
11. Preserve external Markdown image links if they appear in the visible conversation, for example `![alt text](https://example.com/image.png)`.
12. Do not try to include pasted images, uploaded images, screenshots, attachments, local files, or internal chatbot-hosted images.
13. If the visible conversation clearly contains an image but there is no usable external Markdown image link, insert this placeholder: `[Image present in original chat — not included]`.
14. Do not invent image captions, image descriptions, links, or filenames.
15. If the full conversation cannot be reproduced, say so at the top before the transcript and explain what is missing.
16. Output only the transcript itself.

Use this structure:

# **[USER]**

First user message.

# **[CHATBOT]**

First chatbot response.

# **[USER]**

Next user message.

# **[CHATBOT]**

Next chatbot response.

Continue until the conversation has been reproduced.

```

## Important exclusion

- Do not include hidden reasoning, “thinking” sections, analysis, tool output, system messages, developer messages, or internal planning as transcript turns. If the interface shows a separate thinking/reasoning section, ignore it. Only include the final visible chatbot response as `# **[CHATBOT]**`.
