#!/usr/bin/env python3
"""Build the Starline multi-platform content workbench."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

THEMES = {
    "moyu-green": {"name": "摸鱼绿", "accent": "#059669", "secondary": "#10B981", "rgb": "5,150,105", "soft": "#ECFDF5", "ink": "#12352f", "paper": "#fffdf9"},
    "tech-cobalt": {"name": "科技钴蓝", "accent": "#1D4ED8", "secondary": "#2563EB", "rgb": "29,78,216", "soft": "#EFF6FF", "ink": "#172554", "paper": "#ffffff"},
    "red-white": {"name": "红白色系", "accent": "#DC2626", "secondary": "#EF4444", "rgb": "220,38,38", "soft": "#FEF2F2", "ink": "#3b1515", "paper": "#fffdfc"},
    "graphite-minimal": {"name": "石墨极简", "accent": "#52525B", "secondary": "#71717A", "rgb": "82,82,91", "soft": "#F4F4F5", "ink": "#22252c", "paper": "#ffffff"},
    "apple-open-course": {"name": "公开课风", "accent": "#0066CC", "secondary": "#2563EB", "rgb": "0,102,204", "soft": "#F5F5F7", "ink": "#1D1D1F", "paper": "#ffffff"},
    "zen-whitespace": {"name": "留白禅意", "accent": "#4A5D52", "secondary": "#6B806F", "rgb": "74,93,82", "soft": "#F1F5F2", "ink": "#263b2c", "paper": "#fffefa"},
    "moyu-ticket": {"name": "摸鱼票据", "accent": "#059669", "secondary": "#10B981", "rgb": "5,150,105", "soft": "#ECFDF5", "ink": "#163c34", "paper": "#fffdf8"},
    "olive-journal": {"name": "橄榄手记", "accent": "#ED7B2F", "secondary": "#F59E0B", "rgb": "237,123,47", "soft": "#FFF7ED", "ink": "#452718", "paper": "#fffdf9"},
    "klein-blue": {"name": "克莱因蓝册", "accent": "#002FA7", "secondary": "#2563EB", "rgb": "0,47,167", "soft": "#EFF6FF", "ink": "#111b4a", "paper": "#ffffff"},
}

PLATFORMS = {
    "wechat": {"name": "微信公众号", "sub": "长文排版 · 可复制 HTML"},
    "xiaohongshu": {"name": "小红书图文", "sub": "爆款文案 · 竖版图片"},
    "visual": {"name": "视觉卡片", "sub": "SVG 图示 · PNG 导出"},
}

DEFAULT_MARKDOWN = """# 欢迎使用 Starline Content Studio

> 左侧写内容，右侧看效果；同一份源文案，可以输出到不同平台。

## 公众号只是第一个出口

把 Markdown 或普通文字粘贴到左侧。你可以先在右侧检查公众号长文排版，再切换到小红书图文或视觉卡片。

## 内容和视觉分开管理

源内容保持可编辑，公众号 HTML、小红书文案和 SVG 图片都是可重新生成的输出，不会覆盖原文。

- 左侧：源内容编辑
- 右侧：平台实时预览
- 顶部：平台、主题和导出操作
"""


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


def first_title(body: str):
    return next((m.group(1).strip() for m in re.finditer(r"^#\s+(.+)$", body, re.M)), "未命名内容")


def inline(text: str, accent: str) -> str:
    safe = html.escape(text, quote=False)
    safe = re.sub(r"\*\*(.+?)\*\*", rf'<strong style="color:{accent};">\1</strong>', safe)
    safe = re.sub(r"`(.+?)`", r"<code>\1</code>", safe)
    return safe


def render_wechat(meta, body, theme):
    title = meta.get("title") or first_title(body)
    chapters = [line[3:].strip() for line in body.splitlines() if line.startswith("## ")]
    sections = [f'<section data-wechat-root="true" style="max-width:677px;margin:0 auto;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,\'PingFang SC\',\'Microsoft YaHei\',sans-serif;color:#374151;line-height:1.75;letter-spacing:0.5px;overflow-x:hidden;">']
    # Use the registered Starline theme recipes: cover, task card, selected three-part guide, then block-level chapters.
    sections.append(f'<section style="margin:0 0 32px;background:#fff;border:1.5px solid rgba({theme["rgb"]},0.15);border-radius:20px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06);width:100%;"><section style="padding:32px 28px 28px;"><section style="display:flex;align-items:center;gap:8px;margin-bottom:28px;"><span style="width:6px;height:6px;background:{theme["accent"]};border-radius:50%;"><span leaf=""><br></span></span><span style="font-size:11px;font-weight:700;letter-spacing:3px;color:{theme["accent"]};"><span leaf="">{html.escape(meta.get("label", "PRACTICAL GUIDE"))}</span></span><section style="flex:1;height:1px;overflow:hidden;background:linear-gradient(to right,rgba({theme["rgb"]},0.12),transparent);"><span leaf=""><br></span></section><span style="font-size:10px;color:#D1D5DB;font-weight:600;"><span leaf="">{html.escape(meta.get("date", datetime.now().strftime("%Y.%m")))}</span></span></section><section><p style="font-size:15px;color:#D1D5DB;margin:0 0 6px;text-decoration:line-through;letter-spacing:0.5px;"><span leaf="">{html.escape(meta.get("old_belief", "写完文章就算完成？"))}</span></p><p style="font-size:24px;font-weight:900;color:#111827;margin:0;line-height:1.05;letter-spacing:-2px;"><span leaf="">{html.escape(title[:16])}</span></p><p style="font-size:24px;font-weight:900;color:{theme["accent"]};margin:0 0 16px;line-height:1.05;letter-spacing:-2px;"><span leaf="">先把内容排对，再谈发布。</span></p><section style="width:48px;height:3px;background:linear-gradient(to right,{theme["accent"]},{theme["secondary"]});border-radius:2px;margin-bottom:12px;"><span leaf=""><br></span></section><p style="font-size:13px;color:#9CA3AF;margin:0;line-height:1.7;letter-spacing:0.5px;"><span leaf="">{html.escape(meta.get("subtitle", "编辑、预览、复制，一次完成"))}</span></p></section></section><section style="background:linear-gradient(135deg,{theme["accent"]},{theme["secondary"]});padding:12px 28px;"><p style="font-size:12px;color:rgba(255,255,255,0.9);margin:0;font-weight:600;letter-spacing:0.5px;"><span leaf="">STARLINE CONTENT STUDIO</span></p></section></section>')
    if chapters:
        selected = chapters[:3]
        toc = [f'<section style="margin:0 10px 34px;padding:18px 16px;background:{theme["soft"]};border-radius:12px;"><p style="margin:0 0 12px;font-size:12px;line-height:1.4;color:{theme["accent"]};font-weight:700;letter-spacing:1px;"><span leaf="">YOU WILL LEARN</span></p>']
        for idx, chapter in enumerate(selected, 1):
            toc.append(f'<p style="margin:0 0 8px;font-size:14px;line-height:1.7;color:#111827;"><span style="color:{theme["accent"]};font-weight:800;"><span leaf="">0{idx}</span></span><span leaf="">　{html.escape(chapter)}</span></p>')
        toc.append('</section>')
        sections.append("".join(toc))
    chapter_no = 0
    for line in body.splitlines():
        if not line.strip() or line.startswith("# "):
            continue
        if line.startswith("## "):
            chapter_no += 1
            sections.append(f'<section style="margin:42px 10px 34px;height:1px;line-height:1px;background:#D2D2D7;font-size:0;"><span leaf="">.</span></section><section style="margin:0 10px 22px;background:#FFFFFF;"><p style="margin:0 0 7px;font-size:12px;line-height:1.4;color:{theme["accent"]};font-weight:750;letter-spacing:1px;"><span leaf="">STEP {chapter_no:02d} · CONTENT EDITION</span></p><p style="margin:0;font-size:25px;line-height:1.38;color:#1D1D1F;font-weight:800;"><span leaf="">{html.escape(line[3:])}</span></p></section>')
        elif line.startswith("### "):
            sections.append(f'<p style="margin:26px 10px 12px;padding-left:12px;border-left:3px solid {theme["accent"]};font-size:17px;line-height:1.55;color:#1D1D1F;font-weight:800;"><span leaf="">{html.escape(line[4:])}</span></p>')
        elif line.startswith("> "):
            sections.append(f'<section style="margin:24px 10px;padding:17px 0 17px 18px;background:#FFFFFF;border-left:3px solid {theme["accent"]};"><p style="margin:0;font-size:18px;line-height:1.75;color:{theme["ink"]};font-weight:750;"><span leaf="">{inline(line[2:], theme["accent"])}</span></p></section>')
        elif line.startswith("- "):
            sections.append(f'<p style="margin:0 10px 11px;font-size:14px;line-height:1.8;color:#424245;"><span style="display:inline-block;width:24px;height:24px;line-height:24px;text-align:center;border-radius:50%;background:{theme["accent"]};color:#FFFFFF;font-size:12px;font-weight:800;margin-right:9px;"><span leaf="">•</span></span><span leaf="">{inline(line[2:], theme["accent"])}</span></p>')
        else:
            sections.append(f'<p style="margin:0 10px 16px;font-size:15px;line-height:1.9;color:#424245;text-align:justify;"><span leaf="">{inline(line, theme["accent"])}</span></p>')
    sections.append(f'<section style="margin:42px 10px 24px;background:#FFFFFF;text-align:center;"><p style="margin:0 0 18px;font-size:11px;line-height:1;color:#A1A1A6;letter-spacing:3px;"><span leaf="">END</span></p><section style="height:1px;line-height:1px;background:#D2D2D7;font-size:0;"><span leaf="">.</span></section></section><section style="margin:0 10px 24px;padding:20px 0;background:#FFFFFF;text-align:center;"><p style="margin:0 0 8px;font-size:14px;line-height:1.75;color:#1D1D1F;font-weight:700;"><span leaf="">{html.escape(meta.get("author_line", "Starline Content Studio，持续把内容做得更清楚。"))}</span></p><p style="margin:0;font-size:13px;line-height:1.75;color:#6E6E73;"><span leaf="">如果你觉得今天这篇有收获，欢迎点赞、在看、转发，我们下篇见。</span></p></section></section>')
    return "\n".join(sections), title


def render_xiaohongshu(meta, body, theme):
    title = meta.get("title") or first_title(body)
    clean = []
    for line in body.splitlines():
        if line.startswith("# ") or not line.strip():
            continue
        if line.startswith("## "):
            clean.append(f'【{line[3:].strip()}】')
        elif line.startswith("> "):
            clean.append(f'💡 {line[2:].strip()}')
        elif line.startswith("- "):
            clean.append(f'• {line[2:].strip()}')
        else:
            clean.append(line.strip())
    short = "\n\n".join(clean)
    if len(short) > 800:
        short = short[:797].rstrip() + "..."
    tags = [x.strip().lstrip("#") for x in meta.get("tags", "干货分享,效率提升,内容创作").split(",") if x.strip()][:5]
    xhs_title = meta.get("xhs_title") or f"{title}｜这份方法真的值得收藏 📌"
    xhs_html = f'<article data-xhs-root="true"><div class="xhs-cover" style="background:{theme["accent"]};"><span>STARLINE NOTE</span><h1>{html.escape(xhs_title)}</h1><small>把复杂内容，讲得更清楚</small></div><div class="xhs-copy"><p class="xhs-lead">今天来聊聊：{html.escape(title)}。如果你也正在处理类似问题，这份整理可以先收藏起来。</p><div class="xhs-body">{html.escape(short).replace(chr(10), "<br><br>")}</div><p class="xhs-end">收藏起来，下次需要时直接翻出来 📌</p><p class="xhs-tags">{" ".join("#" + html.escape(t) for t in tags)}</p></div></article>'
    return xhs_html, xhs_title


def render_visual_card(meta, body, theme):
    title = meta.get("title") or first_title(body)
    points = []
    for line in body.splitlines():
        if line.startswith("## "):
            points.append(line[3:].strip())
    if not points:
        points = [line.strip() for line in body.splitlines() if line.strip() and not line.startswith("#")][:4]
    points = points[:4] or ["核心观点", "关键方法", "下一步行动"]
    svg_lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1440" role="img" aria-labelledby="title desc"><title id="title">{html.escape(title)}</title><desc id="desc">由源内容生成的视觉卡片</desc><rect width="1080" height="1440" fill="{theme["paper"]}"/><rect x="0" y="0" width="1080" height="430" fill="{theme["accent"]}"/><circle cx="930" cy="100" r="170" fill="#ffffff" opacity=".10"/><text x="86" y="100" fill="#fff" font-family="Arial,sans-serif" font-size="26" letter-spacing="5">STARLINE / VISUAL NOTE</text><text x="86" y="220" fill="#fff" font-family="Arial,sans-serif" font-size="62" font-weight="700">{html.escape(title[:18])}</text><text x="86" y="280" fill="#fff" opacity=".8" font-family="Arial,sans-serif" font-size="25">一张图，先抓住重点</text>']
    for idx, point in enumerate(points):
        y = 620 + idx * 170
        svg_lines.extend([f'<circle cx="118" cy="{y - 8}" r="27" fill="{theme["soft"]}"/><text x="118" y="{y + 2}" text-anchor="middle" fill="{theme["accent"]}" font-family="Arial,sans-serif" font-size="24" font-weight="700">{idx + 1}</text>', f'<text x="180" y="{y}" fill="{theme["ink"]}" font-family="Arial,sans-serif" font-size="34" font-weight="700">{html.escape(point[:24])}</text>', f'<line x1="180" y1="{y + 42}" x2="930" y2="{y + 42}" stroke="{theme["soft"]}" stroke-width="4"/>'])
    svg_lines.append('<text x="86" y="1370" fill="#718096" font-family="Arial,sans-serif" font-size="22">Code by starline · 源内容��编辑 · 视觉输出可重新生成</text></svg>')
    svg = "".join(svg_lines)
    return f'<div data-visual-root="true" class="visual-card"><div class="visual-svg">{svg}</div></div>', svg


def wechat_section_only(raw_html: str) -> str:
    """Return only the validated paste payload, never the workbench shell."""
    start = raw_html.find('<section data-wechat-root="true"')
    end = raw_html.rfind('</section>')
    if start < 0 or end < start:
        return raw_html
    return raw_html[start:end + len('</section>')]


def build(args):
    out = Path(args.output)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "articles").mkdir()
    records = []
    for source in sorted(Path(args.content).rglob("*.md")):
        meta, body = frontmatter(source.read_text(encoding="utf-8"))
        slug = meta.get("slug") or re.sub(r"[^a-z0-9-]+", "-", source.stem.lower()).strip("-") or source.stem
        theme_id = meta.get("theme", "moyu-green")
        if theme_id not in THEMES:
            theme_id = "moyu-green"
        record = {"slug": slug, "title": meta.get("title") or first_title(body), "theme": theme_id, "theme_name": THEMES[theme_id]["name"], "category": meta.get("category", "未分类"), "type": meta.get("type", "article"), "tags": [x.strip() for x in meta.get("tags", "").split(",") if x.strip()], "status": meta.get("status", "published"), "summary": meta.get("summary", meta.get("description", "")), "source": str(source).replace("\\", "/"), "markdown": body, "updated_at": datetime.now(timezone.utc).isoformat()}
        article_dir = out / "articles" / slug
        article_dir.mkdir(parents=True, exist_ok=True)
        (article_dir / "index.html").write_text(article_page(record), encoding="utf-8")
        wechat, _ = render_wechat(record, body, THEMES[theme_id])
        xhs, _ = render_xiaohongshu(meta, body, THEMES[theme_id])
        visual, svg = render_visual_card(meta, body, THEMES[theme_id])
        (article_dir / "wechat.html").write_text(wechat_section_only(wechat), encoding="utf-8")
        (article_dir / "xiaohongshu.html").write_text(xhs_page(xhs, record["title"], THEMES[theme_id]), encoding="utf-8")
        (article_dir / "visual-card.svg").write_text(svg, encoding="utf-8")
        records.append(record)
    (out / "index.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "index.html").write_text(editor_page(records), encoding="utf-8")


def base_css():
    return """<style>:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI","PingFang SC",sans-serif;color:#172033;background:#eef1f5}*{box-sizing:border-box}body{margin:0;min-width:320px}button,input,select,textarea{font:inherit}button{cursor:pointer}.app{min-height:100vh;display:flex;flex-direction:column}.topbar{height:68px;display:flex;align-items:center;justify-content:space-between;padding:0 24px;border-bottom:1px solid #dfe4eb;background:#fbfcfe}.brand{display:flex;align-items:center;gap:11px}.mark{display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:#172033;color:white;font-weight:800}.brand strong{font-size:14px}.brand small{display:block;color:#8a94a5;font-size:11px;margin-top:2px}.top-actions{display:flex;align-items:center;gap:8px}.select,.ghost,.primary{border-radius:9px;border:1px solid #d9e0e8;padding:9px 13px;background:#fff;color:#344158}.select{min-width:130px}.primary{border-color:#172033;background:#172033;color:#fff;font-weight:700}.status{font-size:12px;color:#7a8698}.workspace{flex:1;display:grid;grid-template-columns:minmax(320px,42%) minmax(420px,58%);min-height:calc(100vh - 68px)}.editor-pane{display:flex;flex-direction:column;min-width:0;background:#f5f7fa;border-right:1px solid #dce2ea}.pane-head{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 20px;border-bottom:1px solid #e1e6ed}.pane-title,.preview-label{font-size:12px;letter-spacing:.1em;text-transform:uppercase;font-weight:800;color:#68758a}.pane-hint{font-size:12px;color:#929baa}.editor-wrap{flex:1;display:flex;min-height:0;padding:16px}.editor{width:100%;min-height:560px;resize:none;border:1px solid #dce3eb;border-radius:10px;outline:none;background:#fff;color:#283449;padding:22px;font:15px/1.85 ui-monospace,SFMono-Regular,Consolas,monospace;box-shadow:0 7px 24px #17203308}.editor:focus{border-color:#8ca5d4;box-shadow:0 0 0 3px #2454d815}.editor-footer{display:flex;justify-content:space-between;padding:0 20px 16px;color:#8994a5;font-size:12px}.preview-pane{min-width:0;background:#e9edf2;display:flex;flex-direction:column}.preview-head{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 22px;border-bottom:1px solid #d7dee7;background:#f7f9fb}.preview-label{display:flex;align-items:center;gap:9px}.live-dot{width:7px;height:7px;border-radius:50%;background:#16a175;box-shadow:0 0 0 4px #16a17518}.preview-tools{display:flex;gap:7px;flex-wrap:wrap}.preview-tools button{border:1px solid #d8dfe8;background:white;border-radius:8px;padding:7px 10px;font-size:12px;color:#516078}.preview-tools button.active{background:#172033;color:#fff;border-color:#172033}.preview-area{flex:1;overflow:auto;padding:28px}.phone{max-width:760px;min-height:720px;margin:0 auto;background:#fff;box-shadow:0 16px 42px #1720331c;border-radius:3px;overflow:hidden}.phone-inner{max-width:680px;margin:0 auto}.xhs-cover{padding:50px 36px 42px;color:white;min-height:250px}.xhs-cover span{font-size:11px;letter-spacing:4px;opacity:.75}.xhs-cover h1{font-size:34px;line-height:1.2;margin:35px 0 15px}.xhs-cover small{opacity:.75}.xhs-copy{padding:28px 32px 40px;background:#fff}.xhs-lead{font-size:17px;line-height:1.75;font-weight:700}.xhs-body{font-size:16px;line-height:1.8;color:#39465b}.xhs-end{font-weight:700}.xhs-tags{color:#2454d8}.visual-card{background:#fff;padding:0}.visual-svg svg{display:block;width:100%;height:auto}.toast{position:fixed;right:24px;bottom:24px;z-index:5;padding:12px 16px;border-radius:9px;background:#172033;color:#fff;font-size:13px;box-shadow:0 8px 28px #17203338}.hidden{display:none}@media(max-width:880px){.workspace{grid-template-columns:1fr}.editor-pane{min-height:620px;border-right:0;border-bottom:1px solid #dce2ea}.preview-pane{min-height:760px}.editor{min-height:500px}.preview-area{padding:18px}.topbar{padding:0 14px}.status{display:none}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}</style>"""


def editor_page(records):
    payload = json.dumps({"records": records, "themes": THEMES, "default": DEFAULT_MARKDOWN}, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Starline Content Studio · Multi-platform</title>{base_css()}</head><body><div class="app"><header class="topbar"><div class="brand"><span class="mark">S</span><span><strong>Starline Content Studio</strong><small>One source · many outputs</small></span></div><div class="top-actions"><span id="save-status" class="status">本地工作区</span><select id="platform" class="select" aria-label="选择输出平台"></select><select id="theme" class="select" aria-label="选择视觉主题"></select><button id="export" class="primary">导出当前内容</button></div></header><main class="workspace"><section class="editor-pane"><div class="pane-head"><span class="pane-title">Source / 编辑源文</span><span class="pane-hint">Markdown 或直接粘贴文字</span></div><div class="editor-wrap"><textarea id="editor" class="editor" spellcheck="false" aria-label="Markdown 编辑器"></textarea></div><div class="editor-footer"><span id="word-count">0 字符</span><span>草稿只保存在当前浏览器</span></div></section><section class="preview-pane"><div class="preview-head"><span class="preview-label"><i class="live-dot"></i><span id="platform-label">WeChat / 实时预览</span></span><div class="preview-tools"><button id="copy" class="active">复制当前 HTML</button><button id="reset">恢复示例</button></div></div><div class="preview-area"><div id="phone" class="phone"><div id="preview" class="phone-inner"></div></div></div></section></main><div id="toast" class="toast hidden" role="status"></div></div><script type="application/json" id="boot">{payload}</script><script>{editor_script()}</script></body></html>'''


def editor_script():
    return r'''const boot=JSON.parse(document.getElementById('boot').textContent);const editor=document.getElementById('editor'),preview=document.getElementById('preview'),platformSelect=document.getElementById('platform'),themeSelect=document.getElementById('theme'),label=document.getElementById('platform-label'),count=document.getElementById('word-count'),toast=document.getElementById('toast'),saveStatus=document.getElementById('save-status');let platform=localStorage.getItem('starline-platform')||'wechat',themeId=localStorage.getItem('starline-theme')||'apple-open-course';const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));function meta(raw){let body=raw,m={};if(raw.startsWith('---')){const p=raw.split('---');if(p.length>=3){p[1].split('\n').forEach(x=>{const i=x.indexOf(':');if(i>0)m[x.slice(0,i).trim()]=x.slice(i+1).trim().replace(/^"|"$/g,'')});body=p.slice(2).join('---').trim()}}return{m,body}}function render(){const {m,body}=meta(editor.value),t=boot.themes[themeId]||boot.themes['apple-open-course'];let result;if(platform==='wechat'){result=wechat(m,body,t);label.textContent='WeChat / 实时预览'}else if(platform==='xiaohongshu'){result=xhs(m,body,t);label.textContent='XHS / 小红书图文'}else{result=visual(m,body,t);label.textContent='VISUAL / SVG 图卡'}preview.innerHTML=result;count.textContent=`${editor.value.length} 字符`;localStorage.setItem('starline-draft',editor.value);saveStatus.textContent='已保存到本地'}function wechat(m,b,t){const title=m.title||(b.match(/^#\s+(.+)$/m)||[])[1]||'未命名文章';let out=[`<section data-wechat-root="true" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#263238;line-height:1.85;background:${t.paper};padding:28px 22px 34px;"><section style="background:${t.soft};padding:26px 22px;margin:0 0 26px;border-radius:4px;border-left:5px solid ${t.accent};"><h1 style="color:${t.ink};font-size:30px;line-height:1.25;margin:0;"><span leaf="">${esc(title)}</span></h1></section>`];b.split('\n').forEach(x=>{if(!x.trim()||x.startsWith('# '))return;if(x.startsWith('## '))out.push(`<section style="margin:30px 0 14px;padding:0 0 8px;border-bottom:2px solid ${t.accent};"><p style="margin:0;font-size:19px;font-weight:700;color:${t.ink};"><span leaf="">${esc(x.slice(3))}</span></p></section>`);else if(x.startsWith('> '))out.push(`<section style="background:${t.soft};padding:16px 18px;margin:20px 0;border-radius:3px;"><p style="margin:0;color:${t.ink};"><span leaf="">${esc(x.slice(2))}</span></p></section>`);else if(x.startsWith('- '))out.push(`<p style="margin:8px 0 8px 10px;padding-left:12px;border-left:3px solid ${t.accent};"><span leaf="">${esc(x.slice(2))}</span></p>`);else out.push(`<p style="margin:0 0 18px;font-size:16px;"><span leaf="">${esc(x)}</span></p>`)});return out.join('')+'</section>'}function xhs(m,b,t){const title=m.title||(b.match(/^#\s+(.+)$/m)||[])[1]||'未命名内容';const text=b.split('\n').filter(x=>x.trim()&&!x.startsWith('# ')).map(x=>x.startsWith('## ')?`【${x.slice(3)}】`:x.startsWith('- ')?`• ${x.slice(2)}`:x.startsWith('> ')?`💡 ${x.slice(2)}`:x).join('\n\n').slice(0,800);return `<article data-xhs-root="true"><div class="xhs-cover" style="background:${t.accent};"><span>STARLINE NOTE</span><h1>${esc(m.xhs_title||title+'｜这份方法真的值得收藏 📌')}</h1><small>把复杂内容，讲得更清楚</small></div><div class="xhs-copy"><p class="xhs-lead">今天来聊聊：${esc(title)}。如果你也正在处理类似问题，这份整理可以先收藏起来。</p><div class="xhs-body">${esc(text).replace(/\n/g,'<br><br>')}</div><p class="xhs-end">收藏起来，下次需要时直接翻出来 📌</p><p class="xhs-tags">#干货分享 #效率提升 #内容创作</p></div></article>`}function visual(m,b,t){const title=m.title||(b.match(/^#\s+(.+)$/m)||[])[1]||'未命名内容';const points=b.split('\n').filter(x=>x.startsWith('## ')).map(x=>x.slice(3)).slice(0,4);const ps=points.length?points:['核心观点','关键方法','下一步行动'];let rows=ps.map((x,i)=>`<text x="180" y="${620+i*170}" fill="${t.ink}" font-family="Arial" font-size="34" font-weight="700">${esc(x.slice(0,24))}</text>`).join('');return `<div data-visual-root="true" class="visual-card"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1440" role="img" aria-label="${esc(title)}视觉卡片"><rect width="1080" height="1440" fill="${t.paper}"/><rect width="1080" height="430" fill="${t.accent}"/><text x="86" y="100" fill="#fff" font-family="Arial" font-size="26" letter-spacing="5">STARLINE / VISUAL NOTE</text><text x="86" y="220" fill="#fff" font-family="Arial" font-size="62" font-weight="700">${esc(title.slice(0,18))}</text>${rows}<text x="86" y="1370" fill="#718096" font-family="Arial" font-size="22">Code by starline · 可重新生成</text></svg></div>`}Object.entries(boot.platforms||{}).forEach(([id,p])=>{const o=document.createElement('option');o.value=id;o.textContent=p.name;platformSelect.appendChild(o)});Object.entries(boot.themes).forEach(([id,t])=>{const o=document.createElement('option');o.value=id;o.textContent=t.name;themeSelect.appendChild(o)});platformSelect.value=platform;themeSelect.value=themeId;editor.value=localStorage.getItem('starline-draft')||boot.default;platformSelect.addEventListener('change',()=>{platform=platformSelect.value;localStorage.setItem('starline-platform',platform);render()});themeSelect.addEventListener('change',()=>{themeId=themeSelect.value;localStorage.setItem('starline-theme',themeId);render()});editor.addEventListener('input',render);document.getElementById('reset').addEventListener('click',()=>{editor.value=boot.default;render();flash('已恢复示例内容')});function flash(x){toast.textContent=x;toast.classList.remove('hidden');setTimeout(()=>toast.classList.add('hidden'),1800)}async function copyRich(root){const htmlValue=root.outerHTML;const textValue=root.innerText||root.textContent||'';if(navigator.clipboard&&window.ClipboardItem){await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([htmlValue],{type:'text/html'}),'text/plain':new Blob([textValue],{type:'text/plain'})})]);return}const range=document.createRange();range.selectNode(root);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);const ok=document.execCommand('copy');selection.removeAllRanges();if(!ok)throw new Error('copy failed')}document.getElementById('copy').addEventListener('click',async()=>{try{const root=platform==='wechat'?preview.querySelector('[data-wechat-root]'):preview.firstElementChild;await copyRich(root);flash(platform==='wechat'?'已复制公众号富文本，可直接粘贴':'已复制当前平台富文本')}catch(e){flash('复制失败，请使用导出文件')}});document.getElementById('export').addEventListener('click',()=>{const value=platform==='wechat'?preview.querySelector('[data-wechat-root]').outerHTML:preview.innerHTML;const blob=new Blob([value],{type:'text/html;charset=utf-8'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`starline-${platform}.html`;a.click();URL.revokeObjectURL(a.href);flash('已导出当前 HTML')});render();'''


def xhs_page(content, title, theme):
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · 小红书图文</title>{base_css()}</head><body><main class="preview-area"><div class="phone">{content}</div></main></body></html>'''


def article_page(record):
    theme = THEMES[record["theme"]]
    rendered, _ = render_wechat(record, record["markdown"], theme)
    script = "<script>async function copyRich(root){const h=root.outerHTML,t=root.innerText||root.textContent||'';if(navigator.clipboard&&window.ClipboardItem){await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([h],{type:'text/html'}),'text/plain':new Blob([t],{type:'text/plain'})})]);return}const r=document.createRange();r.selectNode(root);const s=window.getSelection();s.removeAllRanges();s.addRange(r);const ok=document.execCommand('copy');s.removeAllRanges();if(!ok)throw new Error('copy failed')}document.getElementById('copy-article').addEventListener('click',async()=>{try{await copyRich(document.querySelector('[data-wechat-root]'));document.getElementById('copy-article').textContent='已复制富文本'}catch(e){document.getElementById('copy-article').textContent='请打开 wechat.html'}});</script>"
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(record["title"])} · Starline</title>{base_css()}</head><body><div class="app"><header class="topbar"><div class="brand"><a href="../../" style="text-decoration:none;color:inherit">← 返回工作台</a></div><div class="top-actions"><a class="ghost" href="wechat.html">打开纯 HTML</a><button id="copy-article" class="primary">复制公众号 HTML</button></div></header><main class="preview-area"><div class="phone"><div class="phone-inner">{rendered}</div></div></main></div>{script}</body></html>'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", default="content")
    parser.add_argument("--output", default="_site")
    args = parser.parse_args()
    build(args)
