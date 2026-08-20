#!/usr/bin/env python3
"""Build the Starline Content Studio static catalog and output adapters."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

THEMES = {
    "moyu-green": {"name": "摸鱼绿", "accent": "#0c8f73", "soft": "#e7f7f1", "ink": "#12352f"},
    "tech-cobalt": {"name": "科技钴蓝", "accent": "#2454d8", "soft": "#edf2ff", "ink": "#172554"},
    "red-white": {"name": "红白色系", "accent": "#cf3e3e", "soft": "#fff0f0", "ink": "#3b1515"},
    "graphite-minimal": {"name": "石墨极简风", "accent": "#555a66", "soft": "#f1f2f4", "ink": "#22252c"},
    "apple-open-course": {"name": "公开课风", "accent": "#1769d2", "soft": "#eef5ff", "ink": "#10213a"},
    "zen-whitespace": {"name": "留白禅意风", "accent": "#567064", "soft": "#edf4ef", "ink": "#263b2c"},
    "moyu-ticket": {"name": "摸鱼票据风", "accent": "#147d65", "soft": "#e9f7f1", "ink": "#163c34"},
    "olive-journal": {"name": "橄榄手记", "accent": "#c56b2e", "soft": "#fff3e6", "ink": "#452718"},
    "klein-blue": {"name": "克莱因蓝册", "accent": "#123ab8", "soft": "#edf0ff", "ink": "#111b4a"},
}

CONTENT_TYPES = {
    "article": "文章",
    "study-note": "学习笔记",
    "resume": "简历草稿",
    "project": "项目记录",
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


def list_value(value: str | None):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def first_title(body: str):
    return next((m.group(1).strip() for m in re.finditer(r"^#\s+(.+)$", body, re.M)), "未命名内容")


def inline(text: str, accent: str) -> str:
    safe = html.escape(text, quote=False)
    safe = re.sub(r"\*\*(.+?)\*\*", rf'<strong style="color:{accent};">\1</strong>', safe)
    safe = re.sub(r"`(.+?)`", r"<code>\1</code>", safe)
    return safe


def render_wechat(meta, body, theme):
    title = meta.get("title") or first_title(body)
    sections = [
        '<section style="font-family:Arial,sans-serif;color:#1F2937;line-height:1.8;">',
        f'<section style="background:{theme["soft"]};padding:28px 20px;margin:0 0 20px;border-radius:16px;"><h1 style="color:{theme["accent"]};font-size:28px;margin:0;"><span leaf="">{html.escape(title)}</span></h1></section>',
    ]
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
                sections.append(f'<img src="{html.escape(match.group(1), quote=True)}" alt="文章插图" style="max-width:100%;height:auto;display:block;margin:16px auto;border-radius:8px;" />')
        else:
            sections.append(f'<p style="margin:0 0 16px;"><span leaf="">{inline(line, theme["accent"])}</span></p>')
    sections.append("</section>")
    return "\n".join(sections), title


def render_reading(meta, body, theme):
    title = meta.get("title") or first_title(body)
    blocks = []
    for line in body.splitlines():
        if not line.strip():
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            blocks.append(f'<h2>{html.escape(line[3:])}</h2>')
        elif line.startswith("> "):
            blocks.append(f'<blockquote>{inline(line[2:], theme["accent"])}</blockquote>')
        elif line.startswith("- "):
            blocks.append(f'<li>{inline(line[2:], theme["accent"])}</li>')
        else:
            blocks.append(f'<p>{inline(line, theme["accent"])}</p>')
    return f'<header class="reading-head"><p class="kicker">{html.escape(CONTENT_TYPES.get(meta.get("type", "article"), "内容"))}</p><h1>{html.escape(title)}</h1><p class="lede">{html.escape(meta.get("summary", "从 Markdown 源文件构建的可读内容。"))}</p></header><div class="reading-body">{"".join(blocks)}</div>'


def record_for(source: Path, meta, body, slug, theme_id, updated_at):
    title = meta.get("title") or first_title(body)
    tags = list_value(meta.get("tags"))
    return {
        "slug": slug,
        "title": title,
        "summary": meta.get("summary", ""),
        "type": meta.get("type", "article"),
        "type_name": CONTENT_TYPES.get(meta.get("type", "article"), "文章"),
        "category": meta.get("category", "未分类"),
        "tags": tags,
        "status": meta.get("status", "published"),
        "theme": theme_id,
        "theme_name": THEMES[theme_id]["name"],
        "source": str(source).replace("\\", "/"),
        "updated_at": updated_at,
    }


def build(args):
    out = Path(args.output)
    if out.exists():
        shutil.rmtree(out)
    (out / "articles").mkdir(parents=True)
    records = []
    updated_at = datetime.now(timezone.utc).isoformat()
    for source in sorted(Path(args.content).rglob("*.md")):
        meta, body = frontmatter(source.read_text(encoding="utf-8"))
        slug = meta.get("slug") or re.sub(r"[^a-z0-9-]+", "-", source.stem.lower()).strip("-") or source.stem
        theme_id = meta.get("theme", "moyu-green")
        if theme_id not in THEMES:
            theme_id = "moyu-green"
        theme = THEMES[theme_id]
        rendered, title = render_wechat(meta, body, theme)
        reading = render_reading(meta, body, theme)
        article_dir = out / "articles" / slug
        article_dir.mkdir(parents=True, exist_ok=True)
        record = record_for(source, meta, body, slug, theme_id, updated_at)
        (article_dir / "index.html").write_text(article_page(record, rendered, reading, theme), encoding="utf-8")
        (article_dir / "wechat.html").write_text(rendered, encoding="utf-8")
        records.append(record)
    (out / "index.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "index.html").write_text(index_page(records), encoding="utf-8")


def shell_style():
    return """<style>
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f5f7fa;color:#172033;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI","PingFang SC",sans-serif}a{color:inherit}button,input,select{font:inherit}button{cursor:pointer}.shell{max-width:1180px;margin:auto;padding:32px 22px 64px}.topbar{display:flex;align-items:center;justify-content:space-between;gap:18px}.brand{display:flex;gap:12px;align-items:center;text-decoration:none}.mark{display:grid;place-items:center;width:36px;height:36px;border-radius:12px;background:#172033;color:#fff;font-weight:800}.brand strong{display:block;font-size:15px}.brand small{display:block;color:#758096;margin-top:2px}.eyebrow,.kicker{font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:#637088;font-weight:750}.hero{padding:64px 0 32px;max-width:740px}.hero h1{font-size:clamp(34px,6vw,68px);line-height:1.04;letter-spacing:-.055em;margin:12px 0 16px}.hero p{font-size:17px;line-height:1.7;color:#607087;margin:0}.workspace{display:grid;grid-template-columns:220px minmax(0,1fr);gap:22px;align-items:start}.rail{position:sticky;top:18px}.rail h2{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:#7c8799;margin:0 0 12px}.nav-list{display:grid;gap:4px}.nav-list button{border:0;background:transparent;text-align:left;padding:10px 12px;border-radius:10px;color:#647089}.nav-list button.active,.nav-list button:hover{background:#e9edf3;color:#172033}.content-panel{min-width:0}.toolbar{display:flex;gap:10px;align-items:center;margin-bottom:14px}.toolbar input,.toolbar select{border:1px solid #dce2ea;background:#fff;border-radius:12px;padding:12px 14px;color:#172033}.toolbar input{flex:1;min-width:0}.count{color:#738098;font-size:13px;white-space:nowrap}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.card{background:#fff;border:1px solid #e5e9ef;border-radius:16px;padding:18px;min-width:0;transition:transform .18s ease,box-shadow .18s ease}.card:hover{transform:translateY(-2px);box-shadow:0 12px 30px #17203312}.card h2{font-size:20px;line-height:1.3;margin:10px 0}.card h2 a{text-decoration:none}.card p{color:#69758a;line-height:1.6;margin:8px 0}.meta-row{display:flex;gap:8px;flex-wrap:wrap;color:#7b8798;font-size:12px}.tag{background:#f0f3f7;border-radius:999px;padding:4px 8px}.status{color:#19705b}.empty{padding:38px 12px;color:#758096;text-align:center;background:#fff;border:1px dashed #d7dde6;border-radius:16px}.footer{border-top:1px solid #e3e7ed;margin-top:60px;padding-top:18px;color:#7b8798;font-size:12px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}.footer a{color:#52627b}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
@media(max-width:760px){.shell{padding:20px 15px 40px}.hero{padding:38px 0 22px}.hero h1{font-size:42px}.workspace{display:block}.rail{position:static;margin-bottom:16px}.nav-list{display:flex;overflow:auto}.nav-list button{white-space:nowrap}.cards{grid-template-columns:1fr}.toolbar{flex-wrap:wrap}.toolbar input{flex-basis:100%}.count{width:100%}}
@media(prefers-reduced-motion:reduce){.card{transition:none}.card:hover{transform:none}}
</style>"""


def index_page(records):
    data = html.escape(json.dumps(records, ensure_ascii=False), quote=True)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Starline Content Studio</title>{shell_style()}</head><body><main class="shell"><nav class="topbar"><a class="brand" href="./"><span class="mark">S</span><span><strong>Starline Content Studio</strong><small>内容资产 · 多端输出</small></span></a><span class="eyebrow">静态工作台</span></nav><header class="hero"><div class="eyebrow">CONTENT WORKSPACE</div><h1>把内容，放回它该在的地方。</h1><p>Markdown 是源资产，公众号只是第一个出口。先管理内容，再选择阅读、排版或未来的简历与学习模块。</p></header><section class="workspace"><aside class="rail"><h2>工作区</h2><div class="nav-list"><button class="active" data-filter="all">全部内容</button><button data-filter="article">文章</button><button data-filter="study-note">学习笔记</button><button data-filter="resume">简历草稿</button><button data-filter="project">项目记录</button></div></aside><section class="content-panel"><div class="toolbar"><label class="sr-only" for="search">搜索内容</label><input id="search" placeholder="搜索标题、标签、分类或来源" autocomplete="off"><label class="sr-only" for="sort">排序</label><select id="sort"><option value="updated">最近更新</option><option value="title">标题 A-Z</option><option value="type">内容类型</option></select><span id="count" class="count"></span></div><div id="list" class="cards"></div><div id="empty" class="empty" hidden>没有匹配内容。试试清除搜索或切换工作区。</div></section></section><footer class="footer"><span>Code by starline · 仅许可原创代码</span><a href="https://github.com/FreeCodeCampXYG/starline-gzh-publisher">查看源项目</a></footer></main><script type="application/json" id="records">{data}</script><script>const records=JSON.parse(document.getElementById('records').textContent);let active='all';const list=document.getElementById('list'),empty=document.getElementById('empty'),count=document.getElementById('count');function esc(s){{return String(s||'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]))}}function draw(){{const q=document.getElementById('search').value.toLowerCase().trim();const sort=document.getElementById('sort').value;let rows=records.filter(r=>(active==='all'||r.type===active)&&(!q||JSON.stringify(r).toLowerCase().includes(q)));rows.sort((a,b)=>sort==='title'?a.title.localeCompare(b.title):sort==='type'?a.type_name.localeCompare(b.type_name):b.updated_at.localeCompare(a.updated_at));list.innerHTML=rows.map(r=>`<article class="card"><div class="meta-row"><span>${{esc(r.type_name)}}</span><span>·</span><span>${{esc(r.category)}}</span><span>·</span><span class="status">${{esc(r.status)}}</span></div><h2><a href="articles/${{encodeURIComponent(r.slug)}}/">${{esc(r.title)}}</a></h2><p>${{esc(r.summary||'打开内容详情，选择阅读或公众号预览。')}}</p><div class="meta-row">${{r.tags.map(t=>`<span class="tag">#${{esc(t)}}</span>`).join('')}}<span>${{esc(r.theme_name)}}</span></div></article>`).join('');count.textContent=`${{rows.length}} / ${{records.length}}`;empty.hidden=rows.length>0}}document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{{active=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));draw()}}));document.getElementById('search').addEventListener('input',draw);document.getElementById('sort').addEventListener('change',draw);draw();</script></body></html>'''


def article_page(record, rendered, reading, theme):
    tags = " ".join(f'<span class="tag">#{html.escape(t)}</span>' for t in record["tags"])
    css = '''<style>.article-shell{max-width:920px}.article-tools{display:flex;justify-content:space-between;gap:12px;align-items:center;margin:30px 0 18px;flex-wrap:wrap}.back{color:#647089;text-decoration:none}.tool-btn{border:1px solid #dce2ea;background:#fff;border-radius:10px;padding:10px 13px;color:#172033}.article-meta{background:#fff;border:1px solid #e5e9ef;border-radius:16px;padding:20px;margin-bottom:14px}.article-meta h1{font-size:clamp(30px,5vw,54px);letter-spacing:-.045em;line-height:1.08;margin:10px 0}.article-meta p{color:#647089;line-height:1.7}.view-tabs{display:flex;gap:6px;border-bottom:1px solid #e0e5eb;margin-bottom:14px}.view-tabs button{border:0;background:transparent;padding:12px 14px;color:#758096;border-bottom:2px solid transparent}.view-tabs button.active{color:__ACCENT__;border-color:__ACCENT__}.view{background:#fff;border:1px solid #e5e9ef;border-radius:16px;padding:18px;overflow:hidden}.reading-head{padding:16px 8px 25px;border-bottom:1px solid #edf0f4}.reading-head h1{font-size:clamp(30px,5vw,52px);line-height:1.1;letter-spacing:-.045em;margin:8px 0 12px}.lede{color:#6c788b;line-height:1.7}.reading-body{max-width:700px;margin:28px auto;font-family:Georgia,"Songti SC",serif;font-size:18px;line-height:1.9}.reading-body h2{font-family:inherit;font-size:26px;line-height:1.3;margin-top:34px;color:__INK__}.reading-body p{margin:0 0 18px}.reading-body blockquote{border-left:3px solid __ACCENT__;background:__SOFT__;padding:12px 16px;margin:20px 0}.wechat-frame{max-width:740px;margin:auto}.notice{padding:12px 14px;background:#fff8e8;border:1px solid #f0dfb5;border-radius:10px;color:#715b2a;font-size:13px;line-height:1.6;margin-bottom:14px}.hidden{display:none}@media(max-width:600px){.article-tools{margin-top:20px}.view{padding:12px}}</style>'''.replace('__ACCENT__', theme['accent']).replace('__INK__', theme['ink']).replace('__SOFT__', theme['soft'])
    script = '''<script>const tabs=document.querySelectorAll('[data-view]');tabs.forEach(tab=>tab.addEventListener('click',()=>{tabs.forEach(x=>x.classList.toggle('active',x===tab));document.querySelectorAll('.view').forEach(x=>x.classList.toggle('hidden',x.id!==tab.dataset.view))}));document.getElementById('copy').addEventListener('click',async()=>{const value=document.getElementById('wechat').querySelector('.wechat-frame').innerHTML;try{await navigator.clipboard.writeText(value);document.getElementById('copy').textContent='已复制 HTML';setTimeout(()=>document.getElementById('copy').textContent='复制公众号 HTML',1800)}catch(e){document.getElementById('copy').textContent='请手动打开 wechat.html'}});</script>'''
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(record["title"])} · Starline</title>{shell_style()}{css}</head><body><main class="shell article-shell"><div class="article-tools"><a class="back" href="../../">← 返回内容目录</a><div><button class="tool-btn" id="copy">复制公众号 HTML</button></div></div><section class="article-meta"><div class="eyebrow">{html.escape(record["type_name"])} · {html.escape(record["status"])}</div><h1>{html.escape(record["title"])}</h1><p>{html.escape(record["summary"] or "Markdown 源内容的多视图预览。")}</p><div class="meta-row"><span>{html.escape(record["category"])}</span><span>·</span><span>{html.escape(record["theme_name"])}</span><span>·</span><span>{html.escape(record["updated_at"][:10])}</span>{tags}</div></section><div class="view-tabs"><button class="active" data-view="reading">阅读视图</button><button data-view="wechat">公众号预览</button><button data-view="contract">内容契约</button></div><section id="reading" class="view">{reading}</section><section id="wechat" class="view hidden"><div class="notice">公众号 HTML 是输出适配器，不是源内容。复制后请在微信编辑器中人工检查图片、链接与粘贴效果。</div><div class="wechat-frame">{rendered}</div></section><section id="contract" class="view hidden"><div class="reading-body"><h2>当前内容契约</h2><p><strong>源文件：</strong>{html.escape(record["source"])}</p><p><strong>内容类型：</strong>{html.escape(record["type_name"])}。未来可在同一内容模型上接入学习笔记定位、简历事实块与其他输出适配器。</p><p><strong>安全边界：</strong>Pages 只读构建，不暴露 Token，不从浏览器直接写远程仓库。</p><p><strong>未来 AI：</strong>选区级操作应保留 before/after、版本锚点、接受/拒绝/回退，不直接覆盖源 Markdown。</p></div></section><footer class="footer"><span>Code by starline</span><a href="wechat.html">打开纯公众号 HTML</a></footer></main>{script}</body></html>'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", default="content")
    parser.add_argument("--output", default="_site")
    args = parser.parse_args()
    build(args)
