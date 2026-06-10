# Workflow overview for creating HTML pages that show AI chats

## Stage 1: Capture the chat in Markdown

The chat is copied turn by turn from the chatbot and pasted into a Markdown text document. Each human turn is introduced with `# **[USER]**`, and each chatbot turn is introduced with `# **[CHATBOT]**`. The pasted content is assumed to keep basic Markdown formatting, such as paragraphs, lists, links, headings, and code blocks.

## Stage 2: Edit the Markdown transcript

The Markdown file is the first editing document. The user can tidy the wording, remove unwanted material, shorten long answers, or adjust the example chat while still seeing the conversation structure clearly.

## Stage 3: Convert the Markdown to HTML and CSS

The edited Markdown transcript is processed into a complete HTML page and a separate CSS file. This processing is done by a Python script that takes the Markdown file and converts it into an HTML page with a CSS file. The CSS makes it look like a generic chat window.

## Stage 4: Edit the HTML page

The generated HTML page can be opened in an HTML editor or browser-based preview tool. This allows the user to make final presentation edits while seeing the chat in situ, with the CSS applied and the final layout visible.

## Stage 5: Copy the reusable HTML content if needed

Inside the generated HTML page, the reusable chat section is clearly marked with large start and end comments. This makes it easy to identify the exact content block to copy into another HTML page.
