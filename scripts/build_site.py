#!/usr/bin/env python3
"""Build a polished static Markdown-to-WeChat editing workbench."""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

THEMES = {
    "moyu-green": {"name": "摸鱼绿", "accent": "#0c8f73", "soft": "#e7f7f1", "ink": "#12352f", "paper": "#fffdf9"},
    "tech-cobalt": {"name": "科技钴蓝", "accent": "#2454d8", "soft": "#edf2ff", "ink": "#172554", "paper": "#ffffff"},
    "red-white": {"name": "红白色系", "accent": "#cf3e3e", "soft": "#fff0f0", "ink": "#3b1515", "paper": "#fffdfc"},
    "graphite-minimal": {"name": "石墨极简", "accent": "#555a66", "soft": "#f1f2f4", "ink": "#22252c", "paper": "#ffffff"},
    "apple-open-course": {"name": "公开课风", "accent": "#1769d2", "soft": "#eef5ff", "ink": "#10213a", "paper": "#ffffff"},
    "zen-whitespace": {"name": "留白禅意", "accent": "#567064", "soft": "#edf4ef", "ink": "#263b2c", "paper": "#fffefa"},
    "moyu-ticket": {"name": "摸鱼票据", "accent": "#147d65", "soft": "#e9f7f1", "ink": "#163c34", "paper": "#fffdf8"},
    "olive-journal": {"name": "橄榄手记", "accent": "#c56b2e", "soft": "#fff3e6", "ink": "#452718", "paper": "#fffdf9"},
    "klein-blue": {"name": "克莱因蓝册", "accent": "#123ab8", "soft": "#edf0ff", "ink": "#111b4a", "paper": "#ffffff"},
}

DEFAULT_MARKDOWN = """# 欢迎使用 Starline Content Studio

> 在左侧编辑，右侧实时看到公众号排版效果。

## 先写内容，再检查表达

把 Markdown 或普通文字粘贴到左侧。标题、段落、引用、列表会在右侧自动整理成适合公众号阅读的样式。

## 一次复制，直接发布

确认视觉和内容后，点击右上角的「复制公众号 HTML」。复制的是右侧排版结果，不是编辑器里的 Markdown。

- 左侧：源内容，可随时修改
- 右侧：公众号视觉预览
- 顶部：主题与复制操作
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
    return next((m.group(1).strip() for m in re.finditer(r"^#\s+(.+)$", body, re.M)), "未命名文章")


def inline(text: str, accent: str) -> str:
    safe = html.escape(text, quote=False)
    safe = re.sub(r"\*\*(.+?)\*\*", rf'<strong style="color:{accent};">\1</strong>', safe)
    safe = re.sub(r"`(.+?)`", r"<code>\1</code>", safe)
    safe = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', safe)
    return safe


def render_wechat(meta, body, theme):
    title = meta.get("title") or first_title(body)
    sections = [
        f'<section data-wechat-root="true" style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Arial,sans-serif;color:#263238;line-height:1.85;background:{theme["paper"]};padding:28px 22px 34px;">',
        f'<section style="background:{theme["soft"]};padding:26px 22px;margin:0 0 26px;border-radius:4px;border-left:5px solid {theme["accent"]};"><h1 style="color:{theme["ink"]};font-size:30px;line-height:1.25;letter-spacing:.01em;margin:0;"><span leaf="">{html.escape(title)}</span></h1></section>',
    ]
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith("# "):
            i += 1
            continue
        if line.startswith("## "):
            sections.append(f'<section style="margin:30px 0 14px;padding:0 0 8px;border-bottom:2px solid {theme["accent"]};"><p style="margin:0;font-size:19px;font-weight:700;color:{theme["ink"]};"><span leaf="">{html.escape(line[3:])}</span></p></section>')
        elif line.startswith("### "):
            sections.append(f'<p style="margin:22px 0 8px;font-size:16px;font-weight:700;color:{theme["accent"]};"><span leaf="">{html.escape(line[4:])}</span></p>')
        elif line.startswith("> "):
            sections.append(f'<section style="background:{theme["soft"]};padding:16px 18px;margin:20px 0;border-radius:3px;"><p style="margin:0;color:{theme["ink"]};"><span leaf="">{inline(line[2:], theme["accent"])}</span></p></section>')
        elif line.startswith("- "):
            sections.append(f'<p style="margin:8px 0 8px 10px;padding-left:12px;border-left:3px solid {theme["accent"]};"><span leaf="">{inline(line[2:], theme["accent"])}</span></p>')
        elif line.startswith("!"):
            match = re.match(r"!\[([^\]]*)\]\((https?://[^)]+)\)", line)
            if match:
                sections.append(f'<img src="{html.escape(match.group(2), quote=True)}" alt="{html.escape(match.group(1), quote=True)}" style="max-width:100%;height:auto;display:block;margin:18px auto;border-radius:3px;" />')
        else:
            sections.append(f'<p style="margin:0 0 18px;font-size:16px;"><span leaf="">{inline(line, theme["accent"])}</span></p>')
        i += 1
    sections.append("</section>")
    return "\n".join(sections), title


def preview_document(meta, body, theme_id):
    theme = THEMES[theme_id]
    rendered, title = render_wechat(meta, body, theme)
    return {"title": title, "html": rendered, "theme": theme_id, "theme_name": theme["name"]}


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
        preview = preview_document(meta, body, theme_id)
        record = {
            "slug": slug,
            "title": preview["title"],
            "theme": theme_id,
            "theme_name": preview["theme_name"],
            "category": meta.get("category", "未分类"),
            "type": meta.get("type", "article"),
            "tags": [x.strip() for x in meta.get("tags", "").split(",") if x.strip()],
            "status": meta.get("status", "published"),
            "summary": meta.get("summary", meta.get("description", "")),
            "source": str(source).replace("\\", "/"),
            "markdown": body,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        article_dir = out / "articles" / slug
        article_dir.mkdir(parents=True, exist_ok=True)
        (article_dir / "index.html").write_text(article_page(record), encoding="utf-8")
        (article_dir / "wechat.html").write_text(preview["html"], encoding="utf-8")
        records.append(record)
    (out / "index.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "index.html").write_text(editor_page(records), encoding="utf-8")


def base_css():
    return """<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI","PingFang SC",sans-serif;color:#172033;background:#eef1f5}*{box-sizing:border-box}body{margin:0;min-width:320px}button,input,select,textarea{font:inherit}button{cursor:pointer}.app{min-height:100vh;display:flex;flex-direction:column}.topbar{height:68px;display:flex;align-items:center;justify-content:space-between;padding:0 24px;border-bottom:1px solid #dfe4eb;background:#fbfcfe}.brand{display:flex;align-items:center;gap:11px}.mark{display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:#172033;color:white;font-weight:800}.brand strong{font-size:14px;letter-spacing:.01em}.brand small{display:block;color:#8a94a5;font-size:11px;margin-top:2px}.top-actions{display:flex;align-items:center;gap:9px}.select,.ghost,.primary{border-radius:9px;border:1px solid #d9e0e8;padding:9px 13px;background:#fff;color:#344158}.select{min-width:130px}.primary{border-color:#172033;background:#172033;color:#fff;font-weight:700;box-shadow:0 4px 12px #17203320}.primary:active{transform:translateY(1px)}.status{font-size:12px;color:#7a8698}.workspace{flex:1;display:grid;grid-template-columns:minmax(320px,43%) minmax(420px,57%);min-height:calc(100vh - 68px)}.editor-pane{display:flex;flex-direction:column;min-width:0;background:#f5f7fa;border-right:1px solid #dce2ea}.pane-head{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 20px;border-bottom:1px solid #e1e6ed}.pane-title{font-size:12px;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:#68758a}.pane-hint{font-size:12px;color:#929baa}.editor-wrap{flex:1;display:flex;min-height:0;padding:16px}.editor{width:100%;min-height:560px;resize:none;border:1px solid #dce3eb;border-radius:10px;outline:none;background:#fff;color:#283449;padding:22px;font:15px/1.85 ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace;box-shadow:0 7px 24px #17203308}.editor:focus{border-color:#8ca5d4;box-shadow:0 0 0 3px #2454d815,0 7px 24px #17203308}.editor-footer{display:flex;justify-content:space-between;padding:0 20px 16px;color:#8994a5;font-size:12px}.preview-pane{min-width:0;background:#e9edf2;display:flex;flex-direction:column}.preview-head{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 22px;border-bottom:1px solid #d7dee7;background:#f7f9fb}.preview-label{display:flex;align-items:center;gap:9px;font-size:12px;letter-spacing:.1em;text-transform:uppercase;font-weight:800;color:#68758a}.live-dot{width:7px;height:7px;border-radius:50%;background:#16a175;box-shadow:0 0 0 4px #16a17518}.preview-tools{display:flex;gap:7px}.preview-tools button{border:1px solid #d8dfe8;background:white;border-radius:8px;padding:7px 10px;font-size:12px;color:#516078}.preview-tools button.active{background:#172033;color:#fff;border-color:#172033}.preview-area{flex:1;overflow:auto;padding:28px}.phone{max-width:760px;min-height:720px;margin:0 auto;background:#fff;box-shadow:0 16px 42px #1720331c;border-radius:3px;overflow:hidden}.phone-inner{max-width:680px;margin:0 auto}.toast{position:fixed;right:24px;bottom:24px;z-index:5;padding:12px 16px;border-radius:9px;background:#172033;color:#fff;font-size:13px;box-shadow:0 8px 28px #17203338}.hidden{display:none}@media(max-width:880px){.workspace{grid-template-columns:1fr}.editor-pane{min-height:620px;border-right:0;border-bottom:1px solid #dce2ea}.preview-pane{min-height:760px}.editor{min-height:500px}.preview-area{padding:18px}.topbar{padding:0 14px}.status{display:none}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>"""


def editor_page(records):
    payload = json.dumps({"records": records, "themes": THEMES, "default": DEFAULT_MARKDOWN}, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Starline Content Studio · Markdown to WeChat</title>{base_css()}</head><body><div class="app"><header class="topbar"><div class="brand"><span class="mark">S</span><span><strong>Starline Content Studio</strong><small>Markdown → WeChat editorial workspace</small></span></div><div class="top-actions"><span id="save-status" class="status">本地工作区</span><select id="theme" class="select" aria-label="选择公众号主题"></select><button id="copy" class="primary">复制公众号 HTML</button></div></header><main class="workspace"><section class="editor-pane"><div class="pane-head"><span class="pane-title">Source / 编辑源文</span><span class="pane-hint">Markdown 或直接粘贴文字</span></div><div class="editor-wrap"><textarea id="editor" class="editor" spellcheck="false" aria-label="Markdown 编辑器"></textarea></div><div class="editor-footer"><span id="word-count">0 字符</span><span>内容只保存在当前浏览器</span></div></section><section class="preview-pane"><div class="preview-head"><span class="preview-label"><i class="live-dot"></i>WeChat / 实时预览</span><div class="preview-tools"><button id="desktop" class="active">阅读宽度</button><button id="reset">恢复示例</button></div></div><div class="preview-area"><div id="phone" class="phone"><div id="preview" class="phone-inner"></div></div></div></section></main><div id="toast" class="toast hidden" role="status"></div></div><script type="application/json" id="boot">{payload}</script><script>{editor_script()}</script></body></html>'''


def editor_script():
    return r'''const boot=JSON.parse(document.getElementById('boot').textContent);const editor=document.getElementById('editor');const preview=document.getElementById('preview');const themeSelect=document.getElementById('theme');const count=document.getElementById('word-count');const toast=document.getElementById('toast');const saveStatus=document.getElementById('save-status');let currentTheme=localStorage.getItem('starline-theme')||'apple-open-course';const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));function fm(raw){let body=raw,meta={};if(raw.startsWith('---')){const p=raw.split('---');if(p.length>=3){p[1].split('\n').forEach(line=>{const i=line.indexOf(':');if(i>0)meta[line.slice(0,i).trim()]=line.slice(i+1).trim().replace(/^"|"$/g,'')});body=p.slice(2).join('---').trim()}}return{meta,body}}function inline(s,accent){let x=esc(s);x=x.replace(/\*\*(.+?)\*\*/g,`<strong style="color:${accent};">$1</strong>`);x=x.replace(/`(.+?)`/g,'<code>$1</code>');return x}function render(raw){const {meta,body}=fm(raw);const t=boot.themes[currentTheme]||boot.themes['apple-open-course'];const title=meta.title||(body.match(/^#\s+(.+)$/m)||[])[1]||'未命名文章';let out=[`<section data-wechat-root="true" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#263238;line-height:1.85;background:${t.paper};padding:28px 22px 34px;"><section style="background:${t.soft};padding:26px 22px;margin:0 0 26px;border-radius:4px;border-left:5px solid ${t.accent};"><h1 style="color:${t.ink};font-size:30px;line-height:1.25;letter-spacing:.01em;margin:0;"><span leaf="">${esc(title)}</span></h1></section>`];body.split('\n').forEach(line=>{if(!line.trim()||line.startsWith('# '))return;if(line.startsWith('## '))out.push(`<section style="margin:30px 0 14px;padding:0 0 8px;border-bottom:2px solid ${t.accent};"><p style="margin:0;font-size:19px;font-weight:700;color:${t.ink};"><span leaf="">${esc(line.slice(3))}</span></p></section>`);else if(line.startsWith('### '))out.push(`<p style="margin:22px 0 8px;font-size:16px;font-weight:700;color:${t.accent};"><span leaf="">${esc(line.slice(4))}</span></p>`);else if(line.startsWith('> '))out.push(`<section style="background:${t.soft};padding:16px 18px;margin:20px 0;border-radius:3px;"><p style="margin:0;color:${t.ink};"><span leaf="">${inline(line.slice(2),t.accent)}</span></p></section>`);else if(line.startsWith('- '))out.push(`<p style="margin:8px 0 8px 10px;padding-left:12px;border-left:3px solid ${t.accent};"><span leaf="">${inline(line.slice(2),t.accent)}</span></p>`);else out.push(`<p style="margin:0 0 18px;font-size:16px;"><span leaf="">${inline(line,t.accent)}</span></p>`)});out.push('</section>');preview.innerHTML=out.join('\n');count.textContent=`${raw.length} 字符 · ${body.split(/\s+/).filter(Boolean).length} 词`;localStorage.setItem('starline-draft',raw);saveStatus.textContent='已保存到本地';}function flash(message){toast.textContent=message;toast.classList.remove('hidden');setTimeout(()=>toast.classList.add('hidden'),1800)}function copyWechat(){const value=preview.innerHTML;navigator.clipboard?.writeText(value).then(()=>flash('已复制右侧公众号 HTML')).catch(()=>flash('复制失败，请打开文章页手动复制'))}Object.entries(boot.themes).forEach(([id,t])=>{const o=document.createElement('option');o.value=id;o.textContent=t.name;themeSelect.appendChild(o)});themeSelect.value=currentTheme;editor.value=localStorage.getItem('starline-draft')||boot.default;editor.addEventListener('input',()=>render(editor.value));themeSelect.addEventListener('change',()=>{currentTheme=themeSelect.value;localStorage.setItem('starline-theme',currentTheme);render(editor.value)});document.getElementById('copy').addEventListener('click',copyWechat);document.getElementById('reset').addEventListener('click',()=>{editor.value=boot.default;render(editor.value);flash('已恢复示例内容')});render(editor.value);'''


def article_page(record):
    theme = THEMES[record["theme"]]
    meta = {"title": record["title"]}
    rendered, _ = render_wechat(meta, record["markdown"], theme)
    script = "<script>document.getElementById('copy-article').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(document.querySelector('[data-wechat-root]').outerHTML);document.getElementById('copy-article').textContent='已复制 HTML'}catch(e){document.getElementById('copy-article').textContent='请打开 wechat.html'}});</script>"
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(record["title"])} · Starline</title>{base_css()}</head><body><div class="app"><header class="topbar"><div class="brand"><a href="../../" style="text-decoration:none;color:inherit">← 返回工作台</a></div><div class="top-actions"><a class="ghost" href="wechat.html">打开纯 HTML</a><button id="copy-article" class="primary">复制公众号 HTML</button></div></header><main class="preview-area"><div class="phone"><div class="phone-inner">{rendered}</div></div></main></div>{script}</body></html>'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", default="content")
    parser.add_argument("--output", default="_site")
    args = parser.parse_args()
    build(args)
