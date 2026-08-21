/**
 * md-components.js — Starline 组件化排版引擎
 * ============================================
 * 借鉴 starline-gzh-design 技能精髓：把 Markdown 渲染为
 * 「杂志级组件排版」（封面卡 / 目录 / 章节卡 / 引言卡 /
 * 正文关键词标记 / 代码卡 / 图片卡 / 签名区 / 参考资料），
 * 而不是平淡的标签→CSS 渲染。
 *
 * 设计原则：
 *   - 高内聚：所有组件函数集中在此文件，输出纯 HTML 字符串
 *   - 低耦合：主题 = 一组色板参数，组件函数与主题解耦
 *   - 零依赖：纯字符串/正则，可被任意工具页 <script> 引入
 *   - 兼容公众号：内联样式 + <span leaf=""> 包裹 + 禁 class/id
 *
 * 使用方式：
 *   <script src="md-components.js"></script>
 *   const html = MdComponents.render(mdText, theme, options);
 *   // theme 为色板对象（见 md-themes.js），options 见 render() 签名
 */

const MdComponents = (() => {
  'use strict';

  // ============================================================
  // 1. 工具函数
  // ============================================================

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // 全角引号/标点处理：正文用全角，代码块内保持原样
  function fullwidth(s) {
    return s
      .replace(/"/g, '“')
      .replace(/"/g, '”')
      .replace(/'/g, '‘')
      .replace(/'/g, '’')
      .replace(/,(?!\d)/g, '，')
      .replace(/\.(?!\d)/g, '。')
      .replace(/;(?!\d)/g, '；')
      .replace(/:(?!\d)/g, '：')
      .replace(/!/g, '！')
      .replace(/\?(?!\d)/g, '？')
      .replace(/\(/g, '（')
      .replace(/\)/g, '）');
  }

  // 内联标记渲染：**加粗** / *斜体* / `代码` / ==高亮== / ++下划线++
  // 整个输出包一层 <span leaf="">，保证粘贴公众号后样式不丢
  function renderInline(text, T) {
    // 先保护行内代码
    const codes = [];
    let t = text.replace(/`([^`]+)`/g, (m, c) => {
      codes.push(c);
      return '\uE000CODE' + (codes.length - 1) + '\uE001';
    });
    // 依次处理 ==高亮==、++下划线++、**加粗**、*斜体*
    t = t
      .replace(/==([^=]+)==/g, (m, c) => `<span style="background:${T.hlBg};padding:0 4px;border-radius:2px;font-weight:600;color:${T.ink};"><span leaf="">${fullwidth(c)}</span></span>`)
      .replace(/\+\+([^+]+)\+\+/g, (m, c) => `<span style="border-bottom:2px solid ${T.underline};font-weight:600;"><span leaf="">${fullwidth(c)}</span></span>`)
      .replace(/\*\*([^*]+)\*\*/g, (m, c) => `<strong style="color:${T.primary};"><span leaf="">${fullwidth(c)}</span></strong>`)
      .replace(/\*([^*]+)\*/g, (m, c) => `<em style="font-style:italic;color:${T.secondary};"><span leaf="">${fullwidth(c)}</span></em>`);
    // 恢复行内代码
    t = t.replace(/\uE000CODE(\d+)\uE001/g, (m, i) =>
      `<span style="background:${T.codeBg};color:${T.codeText};padding:2px 6px;border-radius:4px;font-family:'SF Mono',Consolas,monospace;font-size:13px;font-weight:600;"><span leaf="">${esc(codes[+i])}</span></span>`);
    // 整段包一层 leaf（leaf 内允许嵌套 span leaf）
    return `<span leaf="">${t}</span>`;
  }

  // 段落关键词下划线：启发式挑选 1 个候选短语
  // 优先：含数字的完整短语 → 引号内内容 → 完整英文/数字单词 → 4-14字中文短语
  function pickKeyword(text) {
    const clean = text.replace(/<[^>]+>/g, '');
    if (!clean) return null;
    // 1) 引号/书名号内的完整短语
    let m = clean.match(/[「『“"《]([^」』”"》]{4,18})[」』”"》]/);
    if (m && m[1]) return m[1];
    // 2) 含数字的中英混排片段（"12 个技巧"、"GPT-4-o1"、"收入 3 倍"），取完整 token 边界
    m = clean.match(/[^，。！？；：、\s]{0,6}[0-9]+[^，。！？；：、\s]{0,8}/);
    if (m && m[0].length >= 3 && m[0].length <= 16) return m[0];
    // 3) 完整英文/数字单词（词边界内，不截断），含数字者优先
    m = clean.match(/[A-Za-z0-9][A-Za-z0-9.+\-\/]{3,15}/);
    if (m && m[0].length >= 4 && m[0].length <= 16) return m[0];
    // 4) 句子中第一个完整中文短语（逗号/顿号前）
    m = clean.match(/^[^，。！？；：、]{4,14}/);
    if (m && m[0]) return m[0];
    return null;
  }

  // 正文段落组件：每段渲染 + 自动/手动关键词标记
  function paragraph(pText, T, opt) {
    let content = renderInline(esc(pText), T);
    if (opt.underline !== false) {
      // 尝试从纯文本挑关键词并标记（若该段没有显式标记）
      const hasMark = /<strong|<span style="border-bottom|<span style="background:/.test(content);
      if (!hasMark) {
        const kw = pickKeyword(esc(pText));
        if (kw) {
          const idx = content.indexOf(kw);
          if (idx >= 0 && kw.length <= content.length) {
            const tag = `<span style="border-bottom:2px solid ${T.underline};font-weight:600;"><span leaf="">${kw}</span></span>`;
            content = content.slice(0, idx) + tag + content.slice(idx + kw.length);
          }
        }
      }
    }
    return `<p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;">${content}</p>`;
  }

  // ============================================================
  // 2. 组件：封面卡
  // ============================================================

  // coverType: 'breaking'(杂志快讯) 默认；标题自动断行 + 高亮词
  function cover(title, T, opt) {
    const date = opt.date || '';
    const topLabel = opt.topLabel || 'STARLINE · 原创';
    // 标题断行：按标点/长度切成 2 行，第二行用主色
    const pieces = splitTitle(title);
    const line1 = pieces[0] || title;
    const line2 = pieces[1] || '';
    return `<section style="margin:0 0 32px;background:#fff;border:1.5px solid ${T.softBorder};border-radius:20px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06);width:100%;">
  <section style="padding:32px 28px 28px;">
    <section style="display:flex;align-items:center;gap:8px;margin-bottom:28px;">
      <span style="width:6px;height:6px;background:${T.primary};border-radius:50%;"><span leaf=""><br></span></span>
      <span style="font-size:11px;font-weight:700;letter-spacing:3px;color:${T.primary};"><span leaf="">${esc(topLabel)}</span></span>
      <section style="flex:1;height:1px;overflow:hidden;background:linear-gradient(to right,${T.softBorder},transparent);"><span leaf=""><br></span></section>
      <span style="font-size:10px;color:#D1D5DB;font-weight:600;"><span leaf="">${esc(date)}</span></span>
    </section>
    <p style="font-size:15px;color:#D1D5DB;margin:0 0 6px;text-decoration:line-through;letter-spacing:0.5px;">
      <span leaf="">${esc(opt.strike || '你还在用普通排版？')}</span>
    </p>
    <p style="font-size:24px;font-weight:900;color:${T.ink};margin:0;line-height:1.05;letter-spacing:-2px;">
      <span leaf="">${esc(line1)}</span>
    </p>
    ${line2 ? `<p style="font-size:24px;font-weight:900;color:${T.primary};margin:0 0 16px;line-height:1.05;letter-spacing:-2px;">
      <span leaf="">${esc(line2)}</span>
    </p>` : ''}
    <section style="width:48px;height:3px;background:linear-gradient(to right,${T.primary},${T.secondary});border-radius:2px;margin-bottom:12px;">
      <span leaf=""><br></span>
    </section>
    <p style="font-size:13px;color:#9CA3AF;margin:0;line-height:1.7;letter-spacing:0.5px;">
      <span leaf="">${esc(opt.subtitle || '一份内容，多种输出。')}</span>
    </p>
  </section>
  <section style="background:linear-gradient(135deg,${T.primary},${T.secondary});padding:12px 28px;display:flex;align-items:center;justify-content:space-between;">
    <p style="font-size:12px;color:rgba(255,255,255,0.9);margin:0;font-weight:600;letter-spacing:0.5px;">
      <span leaf="">${esc(opt.brand || 'Starline Writer')}</span>
    </p>
    <section style="display:flex;gap:4px;">
      <span style="background:rgba(255,255,255,0.2);padding:1px 6px;border-radius:3px;font-size:8px;color:#fff;font-weight:600;"><span leaf="">${esc(opt.tag1 || '原创')}</span></span>
      <span style="background:rgba(255,255,255,0.2);padding:1px 6px;border-radius:3px;font-size:8px;color:#fff;font-weight:600;"><span leaf="">${esc(opt.tag2 || '深度')}</span></span>
    </section>
  </section>
</section>`;
  }

  function splitTitle(title) {
    const t = (title || '').trim();
    if (!t) return ['', ''];
    if (t.length <= 12) return [t, ''];
    // 在第二个标点后断行
    let idx = -1;
    const marks = ['：', '，', '——', '·', '—', '!', '！', '?', '？'];
    for (const m of marks) {
      const i = t.indexOf(m);
      if (i > 4 && i < t.length - 4) { idx = i + m.length; break; }
    }
    if (idx < 0) idx = Math.ceil(t.length / 2);
    return [t.slice(0, idx), t.slice(idx)];
  }

  // ============================================================
  // 3. 组件：目录 / 导读（横向滚动，前3章 + 写在最后）
  // ============================================================

  function toc(chapters, T) {
    const parts = chapters.slice(0, 3);
    const items = parts.map((c, i) => {
      const isFirst = i === 0;
      return `<section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;${isFirst ? `background:linear-gradient(135deg,${T.primary},${T.secondary});` : 'background:#fff;border:1px solid #E5E7EB;'}border-radius:12px;padding:12px;margin-right:8px;${isFirst ? '' : 'box-shadow:0 2px 6px rgba(0,0,0,0.04);'}">
        <p style="font-size:9px;font-weight:700;${isFirst ? 'color:rgba(255,255,255,0.7)' : 'color:#9CA3AF'};letter-spacing:1px;margin:0 0 5px;"><span leaf="">PART ${String(i + 1).padStart(2, '0')}</span></p>
        <p style="font-size:13px;font-weight:800;${isFirst ? 'color:#fff' : 'color:#111827'};margin:0 0 3px;"><span leaf="">${esc(c.title)}</span></p>
        <p style="font-size:10px;${isFirst ? 'color:rgba(255,255,255,0.7)' : 'color:#9CA3AF'};margin:0;"><span leaf="">${esc(c.en || '')}</span></p>
      </section>`;
    }).join('');
    const last = `<section style="display:inline-block;white-space:normal;vertical-align:top;width:110px;background:#fff;border:1px solid #E5E7EB;border-radius:12px;padding:12px;box-shadow:0 2px 6px rgba(0,0,0,0.04);">
      <p style="font-size:9px;font-weight:700;color:#9CA3AF;letter-spacing:1px;margin:0 0 5px;"><span leaf="">PART ///</span></p>
      <p style="font-size:13px;font-weight:800;color:#111827;margin:0 0 3px;"><span leaf="">写在最后</span></p>
      <p style="font-size:10px;color:#9CA3AF;margin:0;"><span leaf="">CONCLUSION</span></p>
    </section>`;
    return `<section style="margin:0 20px 32px;">
  <section style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
    <p style="font-size:10px;color:#9CA3AF;margin:0;text-transform:uppercase;letter-spacing:2px;font-weight:600;"><span leaf="">📦 ${chapters.length + 1} Parts + Conclusion</span></p>
    <p style="font-size:10px;color:#9CA3AF;margin:0;"><span leaf="">👉 滑动</span></p>
  </section>
  <section style="overflow-x:scroll;-webkit-overflow-scrolling:touch;white-space:nowrap;padding-bottom:8px;">
    ${items}${last}
  </section>
</section>`;
  }

  // ============================================================
  // 4. 组件：章节标题
  // ============================================================

  function chapter(num, title, T, isLast) {
    const en = englishTag(title);
    const numText = isLast ? '∞' : String(num).padStart(2, '0');
    const partText = isLast ? 'LAST' : 'PART';
    return `<section style="margin-top:48px;margin-bottom:32px;padding:0 20px;">
  <section style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
    <section style="text-align:center;flex-shrink:0;">
      <p style="margin:0;font-size:28px;font-weight:900;color:${T.primary};line-height:1;letter-spacing:-2px;"><span leaf="">${numText}</span></p>
      <p style="margin:0;font-size:8px;font-weight:700;color:#D1D5DB;letter-spacing:2px;"><span leaf="">${partText}</span></p>
    </section>
    <span style="width:1px;height:36px;background:#E5E7EB;flex-shrink:0;"><span leaf=""><br></span></span>
    <section>
      <p style="margin:0 0 1px;font-size:17px;font-weight:900;color:#111827;letter-spacing:0.3px;"><span leaf="">${esc(title)}</span></p>
      <p style="margin:0;font-size:11px;font-weight:600;color:#9CA3AF;letter-spacing:1.5px;"><span leaf="">${esc(en)}</span></p>
    </section>
  </section>
</section>`;
  }

  function englishTag(title) {
    const map = { '总结': 'SUMMARY', '结语': 'CONCLUSION', '最后': 'ENDING', '教程': 'TUTORIAL', '实战': 'PRACTICE', '方法': 'METHOD', '工具': 'TOOLS', '案例': 'CASES', '思路': 'THINKING', '复盘': 'REVIEW', '开始': 'START', '步骤': 'STEPS', '清单': 'CHECKLIST', '技巧': 'TIPS', '常见问题': 'FAQ' };
    for (const [k, v] of Object.entries(map)) {
      if (title.includes(k)) return v;
    }
    return 'PART';
  }

  // ============================================================
  // 5. 组件：引言卡 / 金句 / 提示
  // ============================================================

  // 开头引言（第一段 > 内容）
  function introQuote(text, T) {
    return `<section style="margin:0 20px 32px;background:${T.softBg};border-left:4px solid ${T.primary};border-radius:0 12px 12px 0;padding:20px 22px;">
  <p style="font-size:15px;font-weight:800;color:${T.deep};margin:0 0 10px;line-height:1.7;"><span leaf="">「${text}」</span></p>
  <p style="font-size:11px;color:#9CA3AF;margin:0;letter-spacing:1px;"><span leaf="">— 开篇导读</span></p>
</section>`;
  }

  // 文中引用（> 内容）→ 金句左竖条块
  function quoteBlock(text, T) {
    return `<section style="margin:0 20px 24px;background:${T.softBg};border-radius:0 10px 10px 0;border-left:4px solid ${T.primary};padding:14px 18px;">
  <p style="font-size:15px;font-weight:700;color:${T.deep};margin:0;line-height:1.8;">${text}</p>
</section>`;
  }

  // 提示/注意块（!> 或 [!NOTE] 前缀）
  function tipBlock(text, T, label) {
    return `<section style="margin:0 20px 24px;background:${T.softBg};border-radius:0 8px 8px 0;border-left:4px solid ${T.primary};padding:14px 18px;">
  <p style="margin:0 0 6px;"><span style="display:inline-block;background:${T.primary};color:#FFFFFF;font-size:11px;font-weight:700;padding:2px 10px;border-radius:4px;letter-spacing:1px;"><span leaf="">${esc(label || '提示')}</span></span></p>
  <p style="font-size:14px;color:#374151;margin:0;line-height:1.8;">${text}</p>
</section>`;
  }

  // ============================================================
  // 6. 组件：列表
  // ============================================================

  function ulList(items, T) {
    const lis = items.map(it =>
      `<section style="display:flex;align-items:flex-start;gap:10px;margin:0 20px 10px;">
        <span style="width:6px;height:6px;background:${T.primary};border-radius:50%;margin-top:9px;flex-shrink:0;"><span leaf=""><br></span></span>
        <p style="font-size:14px;color:#374151;margin:0;line-height:1.8;flex:1;text-align:justify;">${renderInline(esc(it), T)}</p>
      </section>`).join('');
    return `<section style="margin-bottom:20px;">${lis}</section>`;
  }

  function olList(items, T) {
    const lis = items.map((it, i) =>
      `<section style="display:flex;align-items:flex-start;gap:10px;margin:0 20px 12px;">
        <span style="display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;background:${T.primary};color:#fff;font-size:11px;font-weight:700;border-radius:50%;flex-shrink:0;margin-top:2px;"><span leaf="">${i + 1}</span></span>
        <p style="font-size:14px;color:#374151;margin:0;line-height:1.9;flex:1;text-align:justify;">${renderInline(esc(it), T)}</p>
      </section>`).join('');
    return `<section style="margin-bottom:20px;">${lis}</section>`;
  }

  // ============================================================
  // 7. 组件：代码块（深色卡片，每行一个 <p>）
  // ============================================================

  function codeBlock(code, lang, T) {
    const lines = code.split('\n');
    const lineHtml = lines.map(l =>
      `<p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:#E2E8F0;"><span leaf="">${l || '　'}</span></p>`
    ).join('');
    return `<section style="margin:0 20px 24px;border-radius:8px;overflow:hidden;background:#1E293B;box-shadow:0 4px 16px -8px rgba(15,23,42,0.4);">
  <section style="display:flex;align-items:center;padding:9px 14px;background:#0F172A;">
    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#FF5F56;margin-right:7px;font-size:0;line-height:0;overflow:hidden;">.</span>
    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#FFBD2E;margin-right:7px;font-size:0;line-height:0;overflow:hidden;">.</span>
    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#27C93F;font-size:0;line-height:0;overflow:hidden;">.</span>
    <span style="margin-left:12px;font-size:12px;color:#64748B;font-family:Consolas,Monaco,monospace;letter-spacing:1px;"><span leaf="">${esc(lang || 'code')}</span></span>
  </section>
  <section style="padding:11px 14px;">${lineHtml}</section>
</section>`;
  }

  // ============================================================
  // 8. 组件：图片（圆角卡片 + 居中说明）
  // ============================================================

  function image(src, alt, T) {
    const cap = alt ? `<p style="font-size:12px;color:#9CA3AF;text-align:center;margin:0 0 24px;"><span leaf="">— ${esc(alt)}</span></p>` : '';
    return `<section style="text-align:center;margin:0 20px 8px;border-radius:12px;overflow:hidden;">
  <img src="${esc(src)}" alt="${esc(alt)}" style="max-width:100%;height:auto;display:block;margin:0 auto;border-radius:8px;box-shadow:0 4px 12px -2px rgba(0,0,0,0.08);">
</section>${cap}`;
  }

  // ============================================================
  // 9. 组件：表格
  // ============================================================

  function table(headers, rows, T) {
    const th = headers.map(h => `<th style="background:${T.primary};color:#fff;font-weight:700;padding:8px 12px;text-align:left;"><span leaf="">${esc(h)}</span></th>`).join('');
    const trs = rows.map((r, i) => {
      const bg = i % 2 === 1 ? 'background:#F9FAFB;' : '';
      return `<tr>${r.map(c => `<td style="padding:8px 12px;border-bottom:1px solid #E5E7EB;color:#374151;${bg}"><span leaf="">${esc(c)}</span></td>`).join('')}</tr>`;
    }).join('');
    return `<section style="margin:0 20px 24px;overflow-x:auto;">
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead><tr>${th}</tr></thead>
    <tbody>${trs}</tbody>
  </table>
</section>`;
  }

  // ============================================================
  // 10. 组件：分割线 / 参考资料 / 签名区
  // ============================================================

  function divider(T) {
    return `<section style="margin:28px 20px;display:flex;align-items:center;gap:8px;">
  <section style="flex:1;height:1px;background:${T.softBorder};"><span leaf=""><br></span></section>
  <span style="width:6px;height:6px;background:${T.primary};border-radius:50%;"><span leaf=""><br></span></span>
  <section style="flex:1;height:1px;background:${T.softBorder};"><span leaf=""><br></span></section>
</section>`;
  }

  function referencesList(refs, T) {
    if (!refs || !refs.length) return '';
    const items = refs.map((r, i) =>
      `<p style="font-size:13px;color:#374151;margin:0 0 8px;line-height:1.9;"><span leaf=""><strong style="color:${T.primary};"><span leaf="">[${i + 1}]</span></strong> ${esc(r.text)}：<span style="color:#9CA3AF;word-break:break-all;">${esc(r.url)}</span></span></p>`
    ).join('');
    return `<section style="margin:32px 20px 0;padding:18px 10px 24px;border-top:1px solid ${T.softBorder};">
  <p style="font-size:15px;font-weight:800;color:#1C1917;margin:0 0 14px;padding-left:10px;border-left:3px solid ${T.primary};line-height:1.4;"><span leaf="">参考资料</span></p>
  ${items}
</section>`;
  }

  function signature(sig, T) {
    // sig: { author, bio } 来自用户设置（localStorage）
    if (!sig || (!sig.author && !sig.bio)) return '';
    const nameLine = sig.author ? `<p style="font-size:14px;font-weight:700;color:#111827;margin:0 0 4px;line-height:1.6;"><span leaf="">我是 ${esc(sig.author)}${sig.bio ? '' : '。'}</span></p>` : '';
    const bioLine = sig.bio ? `<p style="font-size:13px;color:#6B7280;margin:0 0 12px;line-height:1.7;"><span leaf="">${esc(sig.bio)}</span></p>` : '';
    return `<section style="margin:0 20px 20px;padding:8px 0;">
  ${nameLine}${bioLine}
  <p style="font-size:13px;font-weight:bold;color:#111827;margin:0;line-height:1.6;"><span leaf="">如果你觉得今天这篇有收获，欢迎<strong style="color:${T.primary};">点赞、在看、转发</strong>三连，我们下篇见。</span></p>
</section>`;
  }

  // ============================================================
  // 11. 主渲染器
  // ============================================================

  /**
   * parseFrontMatter(md)
   * 解析文档顶部 --- front-matter 块（若存在）。
   * 返回 { data: {...}, body: 去除 front-matter 后的正文 }。
   * data 字段：title/subtitle/brand/tags/topLabel/strike/author/bio/date。
   * tags 支持数组 ['原创'] 或逗号分隔字符串 '原创,深度'。
   * 无 front-matter 时 data = {}(空对象), body = 原文。
   */
  function parseFrontMatter(md) {
    const text = String(md || '');
    const m = text.match(/^\uFEFF?---\s*\r?\n([\s\S]*?)\r?\n---\s*/);
    if (!m) return { data: {}, body: text };
    const raw = m[1];
    const body = text.slice(m[0].length);
    const data = {};
    raw.split('\n').forEach(line => {
      const mm = line.match(/^\s*([\w-]+)\s*:\s*(.*)$/);
      if (!mm) return;
      const k = mm[1].trim();
      let v = mm[2].trim();
      // 去掉引号
      v = v.replace(/^["']|["']$/g, '');
      if (k === 'tags') {
        // JSON 数组或逗号分隔
        try { const a = JSON.parse(v); if (Array.isArray(a)) { data.tags = a.map(String); return; } } catch (_) {}
        data.tags = v.split(/[,，]/).map(s => s.trim()).filter(Boolean);
        return;
      }
      if (k === 'date' || k === 'topLabel' || k === 'strike' || k === 'subtitle' || k === 'brand' || k === 'title' || k === 'bio') {
        data[k] = v;
        return;
      }
      data[k] = v;
    });
    return { data, body };
  }

  /**
   * render(md, theme, options)
   *  md      — 标准化后的 Markdown 文本（可含顶部 --- front-matter 块）
   *  theme   — 色板对象 { primary, secondary, softBg, softBorder, deep, ink, underline, hlBg, codeBg, codeText, name }
   *  options — { cover:true, toc:true, underline:true, signature:{author,bio}, date, brand, topLabel, subtitle }
   * 返回 { html, refs, chapters, frontmatter }
   *
   * front-matter 支持字段（优先于 options/签名兜底）：
   *   title, subtitle, brand, tags(数组|逗号), topLabel, strike, author, bio, date
   */
  function render(md, theme, options) {
    const T = theme;
    const opt = options || {};
    // 解析 front-matter（文档顶部 --- 块），正文用去头后的内容渲染
    const fm = parseFrontMatter(md);
    const body = fm.body;
    const F = fm.data || {};
    // 组装封面/签名有效配置：front-matter 优先，其次 options，最后内置默认
    const eff = {
      date: F.date || opt.date || '',
      topLabel: F.topLabel || opt.topLabel || 'STARLINE · 原创',
      strike: F.strike || opt.strike || '你还在用普通排版？',
      subtitle: F.subtitle || opt.subtitle || (opt.signature && opt.signature.bio) || '一份内容，多种输出。',
      brand: F.brand || F.author || (opt.signature && opt.signature.author) || opt.brand || 'Starline Writer',
      tag1: (F.tags && F.tags[0]) || opt.tag1 || '原创',
      tag2: (F.tags && F.tags[1]) || opt.tag2 || '深度',
    };
    // 签名合并：front-matter 的 author/bio 优先于设置面板
    let effSig = opt.signature || null;
    if (F.author || F.bio) {
      effSig = {
        author: F.author || (effSig && effSig.author),
        bio: F.bio || (effSig && effSig.bio),
      };
    }
    const lines = body.split('\n');
    const blocks = [];   // { type, ... }
    let i = 0;
    let inCode = false;
    let codeBuf = [];
    let codeLang = '';

    // 1) 分块
    while (i < lines.length) {
      const line = lines[i];
      // 代码块
      if (/^\s*```/.test(line)) {
        if (!inCode) {
          inCode = true;
          codeLang = line.replace(/^\s*```\s*/, '').trim();
          codeBuf = [];
        } else {
          inCode = false;
          blocks.push({ type: 'code', code: codeBuf.join('\n'), lang: codeLang });
        }
        i++;
        continue;
      }
      if (inCode) { codeBuf.push(line); i++; continue; }
      // 空行
      if (!line.trim()) { i++; continue; }
      // 标题
      const hm = line.match(/^(#{1,6})\s+(.+)$/);
      if (hm) {
        blocks.push({ type: 'h', level: hm[1].length, text: hm[2].trim() });
        i++;
        continue;
      }
      // 水平线
      if (/^\s*([-*_])\s*(\1\s*){2,}$/.test(line)) {
        blocks.push({ type: 'hr' });
        i++;
        continue;
      }
      // 引用（收集连续引用行）
      if (/^\s*>\s?/.test(line)) {
        const quoteLines = [];
        while (i < lines.length && /^\s*>\s?/.test(lines[i])) {
          quoteLines.push(lines[i].replace(/^\s*>\s?/, ''));
          i++;
        }
        blocks.push({ type: 'quote', text: quoteLines.join(' ').trim() });
        continue;
      }
      // 无序列表（收集连续项）
      if (/^\s*[-*+]\s+/.test(line)) {
        const items = [];
        while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
          items.push(lines[i].replace(/^\s*[-*+]\s+/, '').trim());
          i++;
        }
        blocks.push({ type: 'ul', items });
        continue;
      }
      // 有序列表
      if (/^\s*\d+[.、]\s+/.test(line)) {
        const items = [];
        while (i < lines.length && /^\s*\d+[.、]\s+/.test(lines[i])) {
          items.push(lines[i].replace(/^\s*\d+[.、]\s+/, '').trim());
          i++;
        }
        blocks.push({ type: 'ol', items });
        continue;
      }
      // 表格（| a | b | 后跟 |---|）
      if (/^\s*\|.*\|\s*$/.test(line)) {
        const headerRow = line.split('|').map(s => s.trim()).filter((s, idx, arr) => !(idx === 0 && s === '') && !(idx === arr.length - 1 && s === ''));
        i++;
        if (i < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i])) {
          i++; // 跳过分隔行
          const rows = [];
          while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
            const cells = lines[i].split('|').map(s => s.trim()).filter((s, idx, arr) => !(idx === 0 && s === '') && !(idx === arr.length - 1 && s === ''));
            rows.push(cells);
            i++;
          }
          blocks.push({ type: 'table', headers: headerRow, rows });
          continue;
        }
        blocks.push({ type: 'p', text: line.trim() });
        continue;
      }
      // 图片
      const imgM = line.match(/^!\[([^\]]*)\]\(([^)]+)\)\s*$/);
      if (imgM) {
        blocks.push({ type: 'img', src: imgM[2], alt: imgM[1] });
        i++;
        continue;
      }
      // 普通段落（收集连续行直到空行/块级标记）
      const paraLines = [line.trim()];
      i++;
      while (i < lines.length && lines[i].trim() && !/^\s*```/.test(lines[i]) && !/^#{1,6}\s/.test(lines[i]) && !/^\s*>\s?/.test(lines[i]) && !/^\s*[-*+]\s+/.test(lines[i]) && !/^\s*\d+[.、]\s+/.test(lines[i]) && !/^\s*\|.*\|\s*$/.test(lines[i]) && !/^\s*([-*_])\s*(\1\s*){2,}$/.test(lines[i])) {
        paraLines.push(lines[i].trim());
        i++;
      }
      blocks.push({ type: 'p', text: paraLines.join('') });
    }

    // 2) 收集章节 + 链接脚注
    const chapters = [];
    const refs = [];
    const refMap = new Map();
    blocks.forEach(b => {
      if (b.type === 'h' && b.level === 2) {
        chapters.push({ title: b.text, en: englishTag(b.text) });
      }
    });
    // 链接 → 脚注编号
    function collectRefs(text) {
      const re = /\[([^\]]+)\]\(([^)]+)\)/g;
      let m;
      const out = [];
      let last = 0;
      while ((m = re.exec(text))) {
        out.push(text.slice(last, m.index));
        let num = refMap.get(m[0]);
        if (!num) {
          num = refMap.size + 1;
          refMap.set(m[0], num);
          refs.push({ text: m[1], url: m[2] });
        }
        out.push(`${m[1]}<sup style="font-size:0.62em;color:${T.primary};font-weight:700;vertical-align:super;line-height:0;margin-left:1px;"><span leaf="">[${num}]</span></sup>`);
        last = m.index + m[0].length;
      }
      out.push(text.slice(last));
      return out.join('');
    }

    // 3) 组装 HTML
    const parts = [];
    const title = blocks.find(b => b.type === 'h' && b.level === 1);
    // front-matter title 优先于 H1；若都没则不显示封面标题（但封面卡仍渲染副标题/标签）
    const coverTitle = F.title || (title && title.text) || '';
    if (opt.cover !== false) {
      parts.push(cover(coverTitle, T, eff));
    }
    // 目录（章节 ≥ 2 时）
    if (opt.toc !== false && chapters.length >= 2) {
      parts.push(toc(chapters, T));
    }
    let chapterIdx = 0;
    let firstIntroDone = false;
    blocks.forEach(b => {
      switch (b.type) {
        case 'h':
          if (b.level === 1) return;
          if (b.level === 2) {
            chapterIdx++;
            const isLast = b.text.includes('总结') || b.text.includes('结语') || b.text.includes('写在最后');
            parts.push(chapter(chapterIdx, b.text, T, isLast));
          } else {
            parts.push(`<section style="margin:28px 20px 14px;font-size:16px;font-weight:800;color:#1C1917;line-height:1.5;border-left:4px solid ${T.primary};padding-left:12px;"><span leaf="">${esc(b.text)}</span></section>`);
          }
          break;
        case 'p': {
          let text = collectRefs(b.text);
          // 开头引言：第一段如果是引用式开头（首个块是 p 且紧跟 quote）
          parts.push(paragraph(text, T, opt));
          break;
        }
        case 'quote': {
          const q = collectRefs(b.text);
          if (!firstIntroDone && !parts.some(p => p.includes('cover'))) {
            // 开头引言
            parts.push(introQuote(q, T));
            firstIntroDone = true;
          } else {
            parts.push(quoteBlock(`<span leaf="">${q}</span>`, T));
          }
          break;
        }
        case 'ul': parts.push(ulList(b.items, T)); break;
        case 'ol': parts.push(olList(b.items, T)); break;
        case 'code': parts.push(codeBlock(b.code, b.lang, T)); break;
        case 'img': parts.push(image(b.src, b.alt, T)); break;
        case 'table': parts.push(table(b.headers, b.rows, T)); break;
        case 'hr': parts.push(divider(T)); break;
      }
    });
    // 参考资料（置于签名前）
    if (refs.length) parts.push(referencesList(refs, T));
    // 签名区
    parts.push(signature(effSig, T));

    const html = `<section style="max-width:677px;margin:0 auto;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:#374151;line-height:1.75;letter-spacing:0.5px;overflow-x:hidden;">
${parts.join('\n')}
</section>`;

    return { html, refs, chapters, frontmatter: F };
  }

  // 供诊断/预览用的公开函数
  return {
    render,
    esc,
    fullwidth,
    pickKeyword,
    splitTitle,
    englishTag,
    parseFrontMatter,
  };
})();
