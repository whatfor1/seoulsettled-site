import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Give every top-level block in a post an entrance hook. Doing it at build time avoids
// the flash you get when a script adds the hidden state after first paint.
function rehypeRise() {
  return (tree) => {
    for (const node of tree.children) {
      if (node.type !== 'element') continue;
      node.properties = node.properties || {};
      node.properties['data-rise'] = '';
    }
  };
}

// Posts link to each other as "/slug/". Under a base path (GitHub Pages project site) that
// would point at the domain root and 404, so prefix the base at build time. With a custom
// domain BASE is "" and this is a no-op — the Markdown never has to change.
function rehypeBaseLinks(base) {
  const prefix = base.replace(/\/$/, '');
  return () => (tree) => {
    const walk = (node) => {
      if (node.type === 'element' && node.tagName === 'a') {
        const h = node.properties?.href;
        if (prefix && typeof h === 'string' && h.startsWith('/') && !h.startsWith('//') && !h.startsWith(prefix + '/')) {
          node.properties.href = prefix + h;
        }
      }
      (node.children || []).forEach(walk);
    };
    walk(tree);
  };
}

// Markdown links carry no rel, and every guide links out to government sites. Outbound
// links get noopener (tab-nabbing) and nofollow (don't vouch for a page we don't control).
function rehypeExternalLinks() {
  return (tree) => {
    const walk = (node) => {
      if (node.type === 'element' && node.tagName === 'a') {
        const h = node.properties?.href;
        if (typeof h === 'string' && /^https?:\/\//i.test(h) && !h.includes('seoulsettled.com')) {
          node.properties.rel = 'nofollow noopener';
        }
      }
      (node.children || []).forEach(walk);
    };
    walk(tree);
  };
}

// Served from its own domain at the root. SITE_URL/BASE_PATH stay overridable for a preview
// build under a sub-path (e.g. BASE_PATH=/seoulsettled-site).
const SITE = process.env.SITE_URL || 'https://seoulsettled.com';
const BASE = process.env.BASE_PATH || '/';

export default defineConfig({
  site: SITE,
  base: BASE,
  trailingSlash: 'always',
  integrations: [sitemap()],
  markdown: {
    shikiConfig: { theme: 'github-light', wrap: true },
    rehypePlugins: [rehypeRise, rehypeBaseLinks(BASE), rehypeExternalLinks],
  },
  build: { format: 'directory' },
});
