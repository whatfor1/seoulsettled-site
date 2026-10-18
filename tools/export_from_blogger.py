"""Pull every Blogger post down into Markdown + frontmatter.

The source HTML uses a small, known tag set (p h2 ul ol li strong em a img div small br
blockquote), so this converts it directly rather than pulling in a dependency.

Images become a `figure` shortcode line the Astro layout renders, which strips Blogger's
inline styles and keeps the credit as structured data instead of free text.

    python3 tools/export_from_blogger.py          # writes src/content/posts/*.md
"""
import html
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/.blogger-automation"))
import blogger  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "content", "posts")
MEDIA = os.path.join(ROOT, "media-manifest.json")


def text_of(node_html):
    t = re.sub(r"<[^>]+>", "", node_html)
    return html.unescape(t).strip()


def inline(s):
    """Inline HTML -> Markdown."""
    s = re.sub(r"<br\s*/?>", "  \n", s, flags=re.I)
    s = re.sub(r"<(strong|b)>(.*?)</\1>", r"**\2**", s, flags=re.I | re.S)
    s = re.sub(r"<(em|i)>(.*?)</\1>", r"*\2*", s, flags=re.I | re.S)

    def link(m):
        attrs, body = m.group(1), m.group(2)
        href = re.search(r'href="([^"]*)"', attrs)
        label = inline(body).strip()
        if not href:
            return label
        return f"[{label}]({html.unescape(href.group(1))})"

    s = re.sub(r"<a([^>]*)>(.*?)</a>", link, s, flags=re.I | re.S)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


FIGURE_RE = re.compile(
    r'<div[^>]*text-align:\s*center[^>]*>\s*<img[^>]+>.*?</div>', re.I | re.S)


def parse_figure(block):
    src = re.search(r'src="([^"]+)"', block)
    alt = re.search(r'alt="([^"]*)"', block)
    small = re.search(r"<small>(.*?)</small>", block, re.S)
    credit_text, credit_url = "", ""
    if small:
        a = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', small.group(1), re.S)
        if a:
            credit_url = html.unescape(a.group(1))
        credit_text = text_of(small.group(1))
        credit_text = re.sub(r"^Photo(:| by)\s*", "", credit_text).strip()
    return {
        "src": html.unescape(src.group(1)) if src else "",
        "alt": html.unescape(alt.group(1)) if alt else "",
        "credit": credit_text,
        "creditUrl": credit_url,
    }


def convert(content):
    """Blogger post HTML -> (markdown body, [figures]), hero figure first if present."""
    figures = []

    def take_figure(m):
        f = parse_figure(m.group(0))
        figures.append(f)
        return f"\n\n@@FIG{len(figures) - 1}@@\n\n"

    s = FIGURE_RE.sub(take_figure, content)

    out = []
    pos = 0
    block_re = re.compile(r"<(h2|h3|p|ul|ol|blockquote)([^>]*)>(.*?)</\1>", re.I | re.S)
    for m in block_re.finditer(s):
        between = s[pos:m.start()]
        for ph in re.findall(r"@@FIG\d+@@", between):
            out.append(ph)
        pos = m.end()

        tag, attrs, body = m.group(1).lower(), m.group(2), m.group(3)
        if tag == "h2":
            out.append(f"## {inline(body)}")
        elif tag == "h3":
            out.append(f"### {inline(body)}")
        elif tag == "p":
            txt = inline(body)
            if txt:
                out.append(txt)
        elif tag == "blockquote":
            out.append("> " + inline(body).replace("\n", "\n> "))
        elif tag in ("ul", "ol"):
            items = re.findall(r"<li[^>]*>(.*?)</li>", body, re.I | re.S)
            for i, it in enumerate(items, 1):
                bullet = f"{i}." if tag == "ol" else "-"
                out.append(f"{bullet} {inline(it)}")
            out.append("")
    for ph in re.findall(r"@@FIG\d+@@", s[pos:]):
        out.append(ph)

    md = "\n\n".join(x for x in out if x is not None)
    md = re.sub(r"\n{3,}", "\n\n", md).strip()

    # hero = the figure that appeared before any prose
    hero = None
    if figures and md.startswith("@@FIG0@@"):
        hero = figures[0]
        md = md[len("@@FIG0@@"):].lstrip()

    def render(m):
        f = figures[int(m.group(1))]
        cap = ""
        if f["credit"]:
            inner = (f'<a href="{f["creditUrl"]}" rel="nofollow noopener">{f["credit"]}</a>'
                     if f["creditUrl"] else f["credit"])
            cap = f"\n  <figcaption>Photo: {inner}</figcaption>"
        return (f'<figure class="fig">\n'
                f'  <img src="{f["src"]}" alt="{f["alt"]}" loading="lazy" decoding="async" />'
                f"{cap}\n</figure>")

    md = re.sub(r"@@FIG(\d+)@@", render, md)
    return md, hero, figures


def slug_of(url):
    return re.sub(r"\.html$", "", url.rstrip("/").rsplit("/", 1)[-1])


def first_sentences(md, limit=155):
    plain = re.sub(r"<[^>]+>", "", md)
    plain = re.sub(r"[*_`#>]", "", plain)
    plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", plain)
    plain = " ".join(plain.split())
    if len(plain) <= limit:
        return plain
    cut = plain[:limit]
    return cut[:cut.rfind(" ")] + "…"


def yaml_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    os.makedirs(OUT, exist_ok=True)
    posts = blogger.list_posts()

    # cross-links between posts must point at the new site, not back at Blogger
    internal = {p["url"]: "/" + slug_of(p["url"]) + "/" for p in posts}

    manifest = []
    for p in posts:
        md, hero, figures = convert(p["content"])
        for old, new in internal.items():
            md = md.replace(old, new)
        slug = slug_of(p["url"])
        published = p["published"]
        date = datetime.fromisoformat(published).strftime("%Y-%m-%d")

        fm = [
            "---",
            f"title: {yaml_str(p['title'])}",
            f"slug: {yaml_str(slug)}",
            f"date: {date}",
            f"description: {yaml_str(first_sentences(md))}",
            f"bloggerId: {yaml_str(p['id'])}",
            f"bloggerUrl: {yaml_str(p['url'])}",
        ]
        labels = p.get("labels") or []
        if labels:
            fm.append("tags:")
            fm += [f"  - {yaml_str(l)}" for l in labels]
        if hero:
            fm += [
                "hero:",
                f"  src: {yaml_str(hero['src'])}",
                f"  alt: {yaml_str(hero['alt'])}",
                f"  credit: {yaml_str(hero['credit'])}",
                f"  creditUrl: {yaml_str(hero['creditUrl'])}",
            ]
        fm.append("---")

        path = os.path.join(OUT, f"{slug}.md")
        with open(path, "w") as f:
            f.write("\n".join(fm) + "\n\n" + md + "\n")

        manifest.append({"slug": slug, "images": figures})
        print(f"  {len(md):>6}자  {len(figures)}img  {slug}")

    with open(MEDIA, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\n{len(posts)}개 → {OUT}")


if __name__ == "__main__":
    main()
