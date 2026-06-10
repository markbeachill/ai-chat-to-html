# **[USER]**

Can you explain what this tool does?

# **[CHATBOT]**

It converts a manually marked AI chat transcript into a simple HTML page.

The transcript uses two markers:

- `# **[USER]**`
- `# **[CHATBOT]**`

The output looks like a generic chat window.

# **[USER]**

Can it preserve code blocks?

# **[CHATBOT]**

Yes. For example:

```python
print("Hello from an example chat")
```

It also preserves ordinary Markdown such as lists, links, and headings.

# **[USER]**

What about images?

# **[CHATBOT]**

External Markdown image links can be reproduced, such as:

![Example external image](https://via.placeholder.com/640x240.png?text=External+image+link)

Local, pasted, uploaded, or internal images are not included as reusable image files.
