import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// SITE/BASE are overridden by the deploy workflow. The defaults are the GitHub Pages
// preview; moving to a custom domain later is a one-line change here plus a CNAME file.
const SITE = process.env.SITE_URL || 'https://whatfor1.github.io';
const BASE = process.env.BASE_PATH ?? '/seoulsettled-site';

export default defineConfig({
  site: SITE,
  base: BASE,
  trailingSlash: 'always',
  integrations: [sitemap()],
  markdown: {
    shikiConfig: { theme: 'github-light', wrap: true },
  },
  build: { format: 'directory' },
});
