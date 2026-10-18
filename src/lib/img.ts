// Unsplash and Wikimedia both resize on request; never ship a 1920px original into a thumbnail.
export function sized(src: string, w: number): string {
  if (src.includes('images.unsplash.com')) return src.replace(/([?&])w=\d+/, `$1w=${w}`);
  if (src.includes('wikimedia.org') && /\/\d+px-/.test(src)) return src.replace(/\/\d+px-/, `/${w}px-`);
  return src;
}
