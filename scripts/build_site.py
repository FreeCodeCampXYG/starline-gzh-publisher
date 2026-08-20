#!/usr/bin/env python3
"""Build a static Markdown catalog and WeChat HTML previews."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

THEMES = {
    "moyu-green": {"name": "摸鱼绿", "accent": "#059669", "soft": "#ECFDF5"},
    "tech-cobalt": {"name": "科技钴蓝", "accent": "#1D4ED8", "soft": "#EFF6FF"},
    "red-white": {"name": "红白色系", "accent": "#DC2626", "soft": "#FEF2F2"},
    "graphite-minimal": {"name": "石墨极简风", "accent": "#52525B", "soft": "#F4F4F5"},
    "apple-open-course": {"name": "苹果公开课风", "accent": "#0066CC", "soft": "#EFF6FF"},
    "zen-whitespace": {"name": "留白禅意风", "accent": "#4A5D52", "soft": "#F1F5F2"},
    "moyu-ticket": {"name": "摸鱼票据风", "accent": "#059669", "soft": "#ECFDF5"},
    "olive-journal": {"name": "橄榄手记", "accent": "#ED7B2F", "soft": "#FFF7ED"},
    "klein-blue": {"name": "克莱因蓝艺术展册", "accent": "#002FA7", "soft": "#EFF6FF"},
}


def frontmatter(text: str):
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    meta[key.strip()] = value.strip().strip('"')
            body = parts[2].lstrip()
    return meta, body


def inline(text: str, accent: str) -> str:
    safe = html.escape(text, quote=False)
    safe = re.sub(r"\*\*(.+?)\*\*", rf'<strong style="color:{accent};">\1</strong>', safe)
    safe = re.sub(r"`(.+?)`", r'<code>\1</code>', safe)
    return safe


def render_wechat(meta, body, theme):
    title = meta.get("title") or next((m.group(1) for m in re.finditer(r"^#\s+(.+)$", body, re.M)), "未命名文章")
    sections = [f'<section style="font-family:Arial,sans-serif;color:#1F2937;line-height:1.8;">', f'<section style="background:{theme["soft"]};padding:28px 20px;margin:0 0 20px;border-radius:16px;"><h1 style="color:{theme["accent"]};font-size:28px;margin:0;"><span leaf="">{html.escape(title)}</span></h1></section>']
    for line in body.splitlines():
        if not line.strip() or line.startswith("# "):
            continue
        if line.startswith("## "):
            sections.append(f'<section style="background:{theme["soft"]};padding:14px 16px;margin:24px 0 12px;border-left:4px solid {theme["accent"]};"><p style="margin:0;font-weight:bold;color:{theme["accent"]};"><span leaf="">{html.escape(line[3:])}</span></p></section>')
        elif line.startswith("> "):
            sections.append(f'<section style="background:{theme["soft"]};padding:16px;margin:16px 0;border-radius:10px;"><p style="margin:0;"><span leaf="">{inline(line[2:], theme["accent"])}</span></p></section>')
        elif line.startswith("- "):
            sections.append(f'<p style="margin:8px 0 8px 16px;"><span leaf="">• {inline(line[2:], theme["accent"])}</span></p>')
        elif line.startswith("!"):
            match = re.match(r"!\[[^\]]*\]\((https?://[^)]+)\)", line)
            if match:
                sections.append(f'<img src="{html.escape(match.group(1), quote=True)}" style="max-width:100%;height:auto;display:block;margin:16px auto;border-radius:8px;" />')
        else:
            sections.append(f'<p style="margin:0 0 16px;"><span leaf="">{inline(line, theme["accent"])}</span></p>')
    sections.append('</section>')
    return "\n".join(sections), title


def build(args):
    out = Path(args.output)
    if out.exists():
        shutil.rmtree(out)
    (out / "articles").mkdir(parents=True)
    records = []
    for source in sorted(Path(args.content).rglob("*.md")):
        meta, body = frontmatter(source.read_text(encoding="utf-8"))
        slug = meta.get("slug") or source.stem.lower().replace(" ", "-")
        theme_id = meta.get("theme", "moyu-green")
        theme = THEMES.get(theme_id, THEMES["moyu-green"])
        rendered, title = render_wechat(meta, body, theme)
        article_dir = out / "articles" / slug
        article_dir.mkdir(parents=True, exist_ok=True)
        (article_dir / "index.html").write_text(page(title, rendered, theme, slug), encoding="utf-8")
        (article_dir / "wechat.html").write_text(rendered, encoding="utf-8")
        records.append({"slug": slug, "title": title, "theme": theme_id, "theme_name": theme["name"], "source": str(source).replace('\\', '/'), "updated_at": datetime.now(timezone.utc).isoformat()})
    (out / "index.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "index.html").write_text(index_page(records), encoding="utf-8")


def page(title, rendered, theme, slug):
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>body{{margin:0;background:#f6f7f9;font-family:system-ui,-apple-system,sans-serif;color:#1f2937}}main{{max-width:820px;margin:0 auto;padding:28px 16px}}nav{{display:flex;justify-content:space-between;margin-bottom:20px}}button{{border:0;border-radius:999px;padding:10px 14px;background:{theme["accent"]};color:#fff;cursor:pointer}}article{{background:#fff;border-radius:18px;padding:18px;box-shadow:0 12px 30px #0000000d}}.meta{{color:#64748b;font-size:13px}}</style><main><nav><a href="../../">← 内容目录</a><button onclick="navigator.clipboard.writeText(document.querySelector('[data-wechat]').innerHTML)">复制公众号 HTML</button></nav><article><div class="meta">{html.escape(theme["name"])} · {html.escape(slug)}</div><div data-wechat>{rendered}</div></article></main></html>'''


def index_page(records):
    cards = "".join(f'<article><div class="eyebrow">{html.escape(r["theme_name"])} · {html.escape(r["updated_at"][:10])}</div><h2><a href="articles/{html.escape(r["slug"])}/">{html.escape(r["title"])}</a></h2><p>{html.escape(r["source"])}</p></article>' for r in records)
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Starline GZH Publisher</title><style>body{{margin:0;background:#f6f7f9;color:#172033;font-family:system-ui,-apple-system,sans-serif}}main{{max-width:1100px;margin:auto;padding:48px 20px}}header{{padding:28px 0 34px}}h1{{font-size:clamp(32px,6vw,64px);margin:0 0 12px}}.sub{{color:#64748b}}.toolbar{{display:flex;gap:12px;margin:20px 0}}input{{flex:1;padding:13px 16px;border:1px solid #dbe2ea;border-radius:999px;font:inherit}}section{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}article{{background:#fff;border:1px solid #e5e7eb;border-radius:18px;padding:20px;box-shadow:0 10px 24px #0000000a}}a{{color:#172033;text-decoration:none}}a:hover{{text-decoration:underline}}.eyebrow{{font-size:12px;color:#2563eb;text-transform:uppercase}}</style><main><header><div class="sub">STARLINE GZH PUBLISHER</div><h1>你的 Markdown，<br>自动变成公众号内容。</h1><div class="sub">GitHub 内容管理 · 多主题预览 · 可复制公众号 HTML</div></header><div class="toolbar"><input id="search" placeholder="搜索文章、主题或路径" oninput="filter()"></div><section id="list">{cards}</section></main><script>function filter(){{const q=document.getElementById('search').value.toLowerCase();document.querySelectorAll('#list article').forEach(x=>x.style.display=x.innerText.toLowerCase().includes(q)?'':'none')}} </script></html>'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", default="content")
    parser.add_argument("--output", default="_site")
    args = parser.parse_args()
    build(args)
