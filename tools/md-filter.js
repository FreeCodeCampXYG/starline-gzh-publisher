/**
 * md-filter.js — Starline Markdown 过滤层
 * ============================================
 *
 * 功能：
 *   1. 将各类非标准 Markdown 强制归一化为标准 Markdown，
 *      确保 marked.js 能正确解析。
 *   2. 对微信公众号不支持的格式（数学公式、Mermaid 图等），
 *      自动转换为内联 SVG 图片，保留视觉信息。
 *   3. 提供校验与诊断信息，帮助用户定位格式问题。
 *
 * 使用方式：
 *   <script src="md-filter.js"></script>
 *   const result = MdFilter.process(inputText);
 *   // result.md        → 标准化后的 Markdown
 *   // result.report    → 诊断报告（警告、建议）
 *   // result.hasIssue  → 是否有格式问题
 *
 * 设计原则：
 *   - 极简：每个函数只做一件事，名称即文档
 *   - 零依赖：不依赖任何外部库，纯字符串/正则操作
 *   - 渐进增强：不影响已标准的内容，只修正异常
 *   - 安全优先：不执行任何 HTML/JS，仅做文本转换
 */

const MdFilter = (() => {
  'use strict';

  // ============================================================
  // 1. 常量与配置
  // ============================================================

  /** 微信公众号不支持的格式标记列表 */
  const UNSUPPORTED_PATTERNS = [
    { regex: /\$\$[\s\S]*?\$\$/g,          label: '数学公式（块级 $$）' },
    { regex: /\$[^$\n]*?\$/g,               label: '数学公式（行内 $）' },
    { regex: /```mermaid[\s\S]*?```/g,      label: 'Mermaid 图表' },
    { regex: /```(?:math|latex)[\s\S]*?```/g, label: 'LaTeX 公式块' },
    { regex: /```(?:dot|graphviz)[\s\S]*?```/g, label: 'Graphviz 图' },
    { regex: /```(?:plantuml)[\s\S]*?```/g, label: 'PlantUML 图' },
    { regex: /:{3,}\s*([a-zA-Z]+)[\s\S]*?:{3,}/g, label: '自定义块（:::）' },
  ];

  /** 中文排版修复映射 */
  const CJK_PUNCT_FIX = {
    '，': ',', '。': '.', '；': ';', '：': ':',
    '！': '!', '？': '?', '（': '(', '）': ')',
    '【': '[', '】': ']', '《': '<', '》': '>',
  };

  /** 不规范的标题标记（如「一、」「1.」做标题） */
  const HEADING_TITLE_RE = /^(?:第[一二三四五六七八九十]+章|[一二三四五六七八九十]+[、．.])\s*/;

  // ============================================================
  // 2. 核心转换函数
  // ============================================================

  /**
   * 将全角标点转为半角 —— 保证 Markdown 解析器正确识别
   * 控制原因：marked.js 对全角标点附近的语法标记可能解析异常，
   * 例如全角 # 不被识别为标题。
   */
  function normalizePunctuation(text) {
    return text.replace(/[，。；：！？（）【】《》]/g, ch => CJK_PUNCT_FIX[ch] || ch);
  }

  /**
   * 修复不规范的标题行 —— 确保 # 后有空格、清理多余空格
   * 控制原因：`#标题`（无空格）在某些解析器中不被识别为标题；
   * `#  标题`（多空格）虽可解析，但影响渲染一致性。
   */
  function normalizeHeadings(text) {
    return text
      // 确保 # 后有一个空格
      .replace(/^(#{1,6})(?!\s)(.+)$/gm, '$1 $2')
      // 压缩 # 后的多个空格为一个
      .replace(/^(#{1,6})\s{2,}/gm, '$1 ')
      // 清理标题末尾多余空格
      .replace(/^(#{1,6}\s.+?)\s+$/gm, '$1');
  }

  /**
   * 修复中文与 Markdown 语法之间的空格问题
   * 控制原因：中文与英文/数字之间加空格可提高可读性，
   * 但 Markdown 语法标记（如 **、*、`）两侧不应加空格，
   * 否则解析器可能不识别。
   */
  function normalizeSpacing(text) {
    return text
      // 中文与英文之间加空格
      .replace(/([\u4e00-\u9fff])([a-zA-Z0-9@])/g, '$1 $2')
      .replace(/([a-zA-Z0-9@])([\u4e00-\u9fff])/g, '$1 $2')
      // 但 Markdown 语法标记两侧不空格
      .replace(/(\*\*)\s+/g, '$1')
      .replace(/\s+(\*\*)/g, '$1')
      .replace(/(\*)\s+/g, '$1')
      .replace(/\s+(\*)/g, '$1')
      .replace(/(`)\s+/g, '$1')
      .replace(/\s+(`)/g, '$1');
  }

  /**
   * 修复无序列表标记 —— 统一为 `-` 加空格
   * 控制原因：`*` 和 `+` 作为列表标记在某些语境下可能被
   * 误解析为斜体或强调；`-` 是最安全的列表标记。
   */
  function normalizeUnorderedList(text) {
    return text
      // 行首的 * 或 + 改为 -（前提是确实是列表上下文）
      .replace(/^(\s*)[*+]\s+/gm, '$1- ')
      // 修复列表标记后无空格的问题
      .replace(/^(\s*[-*+])(?!\s)/gm, '$1 ');
  }

  /**
   * 修复代码块 —— 确保前后有空行，语言标记合规
   * 控制原因：marked.js 要求代码块前后有空行才能正确解析；
   * 语言标记中包含空格会导致语法高亮异常。
   */
  function normalizeCodeBlocks(text) {
    return text
      // 代码块前确保有空行
      .replace(/([^\n])\n```/g, '$1\n\n```')
      // 代码块后确保有空行
      .replace(/```\n([^\n])/g, '```\n\n$1')
      // 清理语言标记中的多余空格（只保留第一个单词）
      .replace(/```(\s+)(\w+)/g, '```$2');
  }

  /**
   * 修复引用块 —— 确保 > 后有一空格
   * 控制原因：`>文字` 在某些解析器中不被识别为引用。
   */
  function normalizeBlockquote(text) {
    return text
      .replace(/^(\s*>)(?!\s)/gm, '$1 ')
      // 嵌套引用 > > 修复为 >>
      .replace(/^(\s*)>\s*>/gm, '$1>>');
  }

  /**
   * 修复分隔线 —— 统一为 `---`
   * 控制原因：`***` 和 `---` 在大多数解析器中等价，
   * 但 `***` 可能被误解析为强调开始。
   */
  function normalizeThematicBreak(text) {
    return text
      .replace(/^[\*_]{3,}\s*$/gm, '---')
      .replace(/^\-{3,}\s*$/gm, '---');
  }

  /**
   * 修复表格 —— 确保对齐行格式正确
   * 控制原因：对齐行 `|---|` 中缺少 `-` 或冒号位置不对
   * 会导致表格不被解析。
   */
  function normalizeTable(text) {
    return text.replace(/^\|(\s*:?-{3,}:?\s*\|)+$/gm, match => {
      // 确保每个单元格至少有 3 个 -
      return match.replace(/:?-{1,2}:?/g, seg => {
        if (seg.startsWith(':') && seg.endsWith(':')) return ':---:';
        if (seg.startsWith(':')) return ':---';
        if (seg.endsWith(':')) return '---:';
        return '---';
      });
    });
  }

  /**
   * 修复行内代码中的特殊字符 —— 防止被解析为 Markdown 语法
   * 控制原因：代码中的 `_` `*` `$` 等字符可能被解析器误处理。
   */
  function escapeCodeContent(text) {
    // 在行内代码中，反引号内的内容不做转义
    // 但需要确保反引号对是匹配的
    return text.replace(/(`+)(.+?)\1/g, (match, ticks, content) => {
      // 如果内容中已经包含相同数量的反引号，跳过
      if (content.includes(ticks)) return match;
      return ticks + content + ticks;
    });
  }

  /**
   * 检测并提取不支持的格式，转换为 SVG 占位符
   * 返回 { text, svgBlocks, report }
   *
   * 控制原因：微信公众号编辑器不支持数学公式、Mermaid 图等，
   * 直接保留这些格式会导致粘贴后内容丢失或显示异常。
   * 转换为 SVG 图片可保留视觉信息。
   */
  function convertUnsupportedToSVG(text) {
    let result = text;
    const svgBlocks = [];
    const report = [];
    let counter = 0;

    // 对每个不支持的格式模式进行处理
    for (const pattern of UNSUPPORTED_PATTERNS) {
      result = result.replace(pattern.regex, (match) => {
        // 生成一个简单的 SVG 图片，显示原始内容
        const lines = match.split('\n');
        const displayText = lines
          .map(l => l.replace(/^(```\w*|\$\$|\s*:::)/, '').trim())
          .filter(Boolean)
          .slice(0, 15); // 限制最多 15 行，防过长

        const svgId = `md-filter-svg-${counter++}`;
        const label = pattern.label;
        const svgContent = generateFallbackSVG(displayText, label);

        svgBlocks.push({
          id: svgId,
          original: match,
          svg: svgContent,
          label,
        });

        report.push({
          type: 'converted',
          label,
          detail: `已转换为 SVG 图片（${displayText.length} 行内容）`,
        });

        // 返回占位图片标记
        return `\n\n![${label} - 已自动转换为图片](${svgId})\n\n`;
      });
    }

    return { text: result, svgBlocks, report };
  }

  /**
   * 生成简易 fallback SVG —— 将不支持的格式内容呈现为图片
   * 控制原因：纯文本的 SVG 比 base64 图片更轻量、可缩放，
   * 且粘贴到微信公众号后仍可保持视觉完整性。
   */
  function generateFallbackSVG(lines, label) {
    const lineHeight = 22;
    const padding = 16;
    const charWidth = 8;
    const maxLineWidth = Math.max(
      200,
      ...lines.map(l => l.length * charWidth)
    );
    const width = Math.min(maxLineWidth + padding * 2, 600);
    const height = Math.max(lines.length * lineHeight + padding * 2 + 24, 60);

    const escapedLines = lines.map(l =>
      l.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    );

    const textElements = escapedLines.map((line, i) =>
      `  <text x="${padding}" y="${padding + 20 + i * lineHeight}" font-size="13" font-family="monospace" fill="#333">${line || ' '}</text>`
    ).join('\n');

    const labelText = label.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <rect width="100%" height="100%" fill="#f8f9fa" rx="6"/>
  <rect x="0" y="0" width="100%" height="24" fill="#e9ecef" rx="6"/>
  <text x="${padding}" y="17" font-size="11" font-family="sans-serif" fill="#6c757d">${labelText}</text>
${textElements}
</svg>`;
  }

  /**
   * 检查常见的 Markdown 格式问题，返回诊断报告
   * 每个 issue 统一携带 line（行号，1 基）与 fix（修复建议），
   * 供前端定位到左侧编辑器对应行并高亮提示。
   */
  function diagnose(text) {
    const issues = [];
    const lines = text.split('\n');

    // 检查未闭合的代码块 —— 定位到第一个开头的行
    const fenceLines = [];
    lines.forEach((line, i) => {
      if (/^\s*```/.test(line)) fenceLines.push(i);
    });
    if (fenceLines.length % 2 !== 0) {
      const openAt = fenceLines[fenceLines.length - 1];
      issues.push({
        severity: 'error',
        line: openAt + 1,
        message: '代码块未闭合：缺少结束的 ```',
        fix: '在内容末尾补上 ``` 结束代码块',
      });
    }

    // 未闭合的加粗标记 —— 定位到奇数标记所在行
    let boldOpen = false;
    let boldCount = 0;
    lines.forEach((line, i) => {
      const matches = line.match(/\*\*/g) || [];
      for (let j = 0; j < matches.length; j++) boldCount++;
      if (boldCount % 2 !== 0 && !boldOpen) {
        // 尝试定位未闭合的 ** 是否在本行
        const openAt = line.lastIndexOf('**');
        if (openAt >= 0) {
          issues.push({
            severity: 'warn',
            line: i + 1,
            message: '可能存在未闭合的加粗标记 **',
            fix: '检查该行，为 ** 补上对应的结束标记',
          });
          boldOpen = true;
        }
        boldCount = 0;
      }
    });

    // 检查表格对齐行前面是否为表头行
    lines.forEach((line, i) => {
      if (/^\s*\|[\s:-]+\|\s*$/.test(line.trim()) || /^[\s:-]+\|[\s:-]+$/.test(line.trim())) {
        if (i === 0 || !lines[i - 1].trim().startsWith('|')) {
          issues.push({
            severity: 'warn',
            line: i + 1,
            message: '表格对齐行前缺少表头行',
            fix: '请在分隔行上方补充以 | 开头的表头行',
          });
        }
      }
    });

    // 检查无序列表标记一致性，并针对每个不同标记行提示
    const listMarkers = new Map();
    lines.forEach((line, i) => {
      const m = line.match(/^(\s*)([*+-])\s/);
      if (m) listMarkers.set(m[2], (listMarkers.get(m[2]) || 0) + 1);
    });
    if (listMarkers.size > 1) {
      // 找出"非主流"标记行（首个出现次数最多的作为基准）
      const sorted = [...listMarkers.entries()].sort((a, b) => b[1] - a[1]);
      const mainMarker = sorted[0][0];
      lines.forEach((line, i) => {
        const m = line.match(/^(\s*)([*+])\s/);
        if (m && m[2] !== mainMarker) {
          issues.push({
            severity: 'info',
            line: i + 1,
            message: `列表标记用 ${m[2]}，与其他列表不一致（基准为 ${mainMarker}）`,
            fix: `将该行开头的 ${m[2]} 改为 -`,
          });
        }
      });
    }

    // 检查标题层级跳跃
    let prevLevel = 0;
    let prevLine = 0;
    lines.forEach((line, i) => {
      const m = line.match(/^(#{1,6})\s/);
      if (m) {
        const level = m[1].length;
        if (prevLevel > 0 && level > prevLevel + 1) {
          issues.push({
            severity: 'info',
            line: i + 1,
            message: `标题层级跳跃：h${prevLevel} → h${level}（越过 h${prevLevel + 1}）`,
            fix: `将第 ${i + 1} 行的标题改为 h${prevLevel + 1}（即 ${'#'.repeat(prevLevel + 1)} 后接内容）`,
          });
        }
        prevLevel = level;
        prevLine = i + 1;
      }
    });

    // 检查无空格的标题（#标题）
    lines.forEach((line, i) => {
      if (/^#{1,6}[^\s#]/.test(line)) {
        issues.push({
          severity: 'warn',
          line: i + 1,
          message: '标题 # 后缺少空格，可能无法被识别为标题',
          fix: `在 # 后补一个空格：${line.replace(/^(#{1,6})/, '$1 ')}`,
        });
      }
    });

    // 检查引用块 > 后无空格
    lines.forEach((line, i) => {
      if (/^>\S/.test(line)) {
        issues.push({
          severity: 'info',
          line: i + 1,
          message: '引用块 > 后缺少空格',
          fix: `改为 > 加空格：> ${line.slice(1)}`,
        });
      }
    });

    // 检查全角标点（大量时提示，已自动转换）
    let cjkCount = 0;
    lines.forEach((line) => {
      cjkCount += (line.match(/[，。；：！？（）【】《》]/g) || []).length;
    });
    if (cjkCount > 10) {
      issues.push({
        severity: 'info',
        line: 1,
        message: `检测到 ${cjkCount} 个全角标点，已自动转换为半角`,
        fix: '无需处理，系统已自动转换',
      });
    }

    return issues;
  }

  // ============================================================
  // 3. 公开 API
  // ============================================================

  /**
   * 主处理函数 —— 执行完整的 Markdown 过滤与转换
   *
   * @param {string} input - 原始 Markdown 文本
   * @param {Object} [options] - 可选配置
   * @param {boolean} [options.convertSVG=true] - 是否将不支持的格式转为 SVG
   * @returns {{ md: string, report: Array, hasIssue: boolean, svgBlocks: Array }}
   *
   * 使用示例：
   *   const result = MdFilter.process(input);
   *   if (result.hasIssue) console.table(result.report);
   *   preview.innerHTML = marked.parse(result.md);
   */
  function process(input, options = {}) {
    const { convertSVG = true } = options;
    const report = [];

    // 步骤 1：诊断原始文本
    const diagnostics = diagnose(input);
    report.push(...diagnostics);

    // 步骤 2：归一化处理
    let md = input;
    md = normalizePunctuation(md);
    md = normalizeHeadings(md);
    md = normalizeSpacing(md);
    md = normalizeUnorderedList(md);
    md = normalizeCodeBlocks(md);
    md = normalizeBlockquote(md);
    md = normalizeThematicBreak(md);
    md = normalizeTable(md);
    md = escapeCodeContent(md);

    // 步骤 3：转换不支持的格式为 SVG
    let svgBlocks = [];
    if (convertSVG) {
      const converted = convertUnsupportedToSVG(md);
      md = converted.text;
      svgBlocks = converted.svgBlocks;
      report.push(...converted.report);
    }

    // 步骤 4：最终清理
    md = md
      // 移除多余的空行（连续超过 3 个空行 → 2 个）
      .replace(/\n{4,}/g, '\n\n\n')
      // 行尾空白
      .replace(/[ \t]+$/gm, '')
      .trim();

    return {
      md,
      report,
      hasIssue: report.length > 0,
      svgBlocks,
    };
  }

  /**
   * 获取 SVG 占位符的 HTML 渲染内容
   * 用于在预览中将 SVG 占位标记替换为实际 SVG
   *
   * @param {string} html - marked 渲染后的 HTML
   * @param {Array} svgBlocks - process() 返回的 svgBlocks
   * @returns {string} 替换后的 HTML
   */
  function injectSVG(html, svgBlocks) {
    if (!svgBlocks || !svgBlocks.length) return html;
    let result = html;
    for (const block of svgBlocks) {
      // 替换 <img alt="..." src="...svg-id..."> 为实际的 SVG
      const imgRe = new RegExp(
        `<img[^>]*src="[^"]*${escapeRegex(block.id)}[^"]*"[^>]*>`,
        'g'
      );
      result = result.replace(imgRe, block.svg);
    }
    return result;
  }

  /** 辅助：转义正则特殊字符 */
  function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // ============================================================
  // 4. 导出
  // ============================================================

  return {
    process,
    injectSVG,
    // 以下是单个归一化函数，供按需调用
    normalizePunctuation,
    normalizeHeadings,
    normalizeSpacing,
    normalizeUnorderedList,
    normalizeCodeBlocks,
    normalizeBlockquote,
    normalizeThematicBreak,
    normalizeTable,
    escapeCodeContent,
    diagnose,
    generateFallbackSVG,
  };
})();