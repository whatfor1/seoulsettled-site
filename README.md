# Seoul Settled

Practical, step-by-step guides to living in Korea — visas, banking, housing, healthcare
and everyday life, checked against official government sources.

Static site built with [Astro](https://astro.build), deployed to GitHub Pages.

## Local

```bash
npm install
npm run dev      # http://localhost:4321/seoulsettled-site/
npm run build
```

## Content

Posts are Markdown in `src/content/posts/`, one file per guide. Frontmatter schema lives
in `src/content.config.ts`.

`tools/export_from_blogger.py` pulled the original 14 posts out of the Blogger blog this
replaced; it is kept for reference, not part of the build.
