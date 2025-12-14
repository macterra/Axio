# Papers

This directory contains source markdown files for academic-style papers with LaTeX math support.

## Structure

- **Source files**: `papers/*.md` (markdown with embedded LaTeX)
- **Published files**: `docs/papers/*.html` (auto-generated HTML)

## Workflow

1. Write papers in markdown format with LaTeX math notation
2. Run `python3 build-site.py` to convert to HTML
3. Papers are automatically published to `docs/papers/` with:
   - MathJax for LaTeX rendering
   - Site styling and navigation
   - Mobile-responsive layout

## Math Notation

Use standard LaTeX math delimiters:
- Inline math: `$...$` or `\(...\)`
- Display math: `$$...$$` or `\[...\]`

## Example

```markdown
# Paper Title

## Abstract

The equation $E = mc^2$ demonstrates...

## Main Content

The wave function is given by:

$$
\Psi(x,t) = A e^{i(kx - \omega t)}
$$
```

## Dependencies

- Python 3
- pandoc (for markdown to HTML conversion)
