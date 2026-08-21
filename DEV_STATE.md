# DEV_STATE.md — Starline Content Studio

## 当前目标

全面改造 starline-gzh-publisher 项目，包括：
1. ✅ md-filter.js Markdown 过滤层（非标准格式转标准 MD，不支持的格式转 SVG）
2. ✅ 三大工具（wechat / x / xiaohongshu）统一为明亮「写作转换」v2 设计
3. ✅ 格式诊断交互：行号定位 + 左侧高亮 + 修复建议
4. ✅ 主页 index.html 改为明亮主题 + 深浅主题切换
5. ✅ 品牌升级为「Starline Writer · 一份内容，三种平台」

## 已完成工作

### md-filter.js（Markdown 过滤层增强）
- 原有归一化与 SVG 转换保留
- **diagnose() 全面增强**：每条诊断统一带 `line`（1 基行号）与 `fix`（修复建议）
- 新增检查项：无空格标题（`#标题`）、引用块 `>` 无空格、未闭合加粗定位到行、表格对齐行定位、列表标记不统一的逐行提示、标题层级跳跃、全角标点统计
- 三个工具共用此诊断输出，前端据此定位左侧编辑器行号

### 统一 v2 工具外壳（wechat / x / xiaohongshu 三页一致）
- 编辑栏结构统一：顶栏（品牌+动作）→ 控制栏 → 双栏工作区（编辑器 | 手机模拟框）
- 每页独立品牌强调色：wechat 明亮蓝、x 一抹深蓝、小红书玫红
- 控制栏含「背景色切换」色点（白/米/淡/粉/深），深色背景自动反白文字
- 编辑区下方新增「诊断面板」：点击控制栏诊断按钮展开，列出问题（错误/警告/提示）、行号、修复建议，点击条目跳转原稿对应行并高亮
- `MdFilter.process()` 后调用 `updateDiagnosisBtn()` 动态显示问题数徽章

### md-to-wechat.html
- 品牌改名：`Starline微排` → `Starline Writer`，标语改「一份内容，三种平台」
- 新增背景色切换（含深色反白逻辑 `setAppBg` + `luminance`）
- 新增诊断面板（`renderDiagnosisPanel` / `jumpToLine` / `toggleDiagnosisPanel`）
- 保留 44 主题、章节样式、表格设置等既有功能

### md-to-x.html（重写为 v2）
- 从 398 行的双栏旧版升级为完整 v2 外壳
- 修复：render() 不再删除 H1（保留文章标题）；`copyRichText()` 经 `buildXHTML()` 克隆并剔除图片悬浮按钮/覆盖 UI 元素
- 新增诊断面板、背景色切换（深色反白）、字号滑块、滚动同步
- X 文章手机模拟框预览

### md-to-xiaohongshu.html（重写为 v2）
- 玫红色品牌 + 明亮修改，卡片式手机框（xhs-card）
- 修复 `buildXhsText()` 大小写 bug（原名 `buildXHSText()`）
- `copyRichText()` 输出克隆后的纯文本（剔除图片悬浮 UI），含 HTML/纯文本双格式
- 保留小红书字数哨兵（buildStatus）+ 标签生成逻辑

### 主页 index.html（明亮化 + 主题切换）
- `:root` 改为明亮主题默认；新增 `.theme-dark` 覆盖暗色原值
- 右上角新增深浅主题切换按钮（太阳/月亮图标，localStorage 记忆 `starline-theme`）
- 硬编码深色值改为 CSS 变量：导航栏 `--color-navbar`、网格 `--color-grid`、代码块全套 `--color-code-*`、卡片 `--color-card`、光晕 `--color-glow-*`、成功标签 `--color-success-*`
- 新增 `--color-border-hover` / `--color-accent-border`

## 核心文件

| 文件 | 用途 |
|------|------|
| `tools/md-filter.js` | Markdown 过滤 + 诊断（行号/建议）层 |
| `tools/md-to-wechat.html` | 微信排版 v2 |
| `tools/md-to-x.html` | X 文章 v2 |
| `tools/md-to-xiaohongshu.html` | 小红书图文 v2 |
| `tools/index.html` | 主页（明亮 + 深浅切换） |
| `tools/cover.html` / `qrcode.html` | 未改动 |

## 已知问题

1. `_site/` 已 .gitignore，构建产物不入库；改动只提交 `tools/`、`md-filter.js`
2. `file://` 下 `fetch('./draft.md')` 被浏览器拦截，需 HTTP 服务访问
3. 三个工具的「背景色切换」仅作用于预览/文章体，不改整个工作区 UI 主题——全局 UI 深浅由主页切换（工具页自身未加全局暗色，避免改动过度）
4. `cover.html` / `qrcode.html` 未集成 md-filter（不处理 Markdown 正文）
5. 已完成的内联 JS 均通过 Node `vm.Script` 语法校验；功能级交互（剪贴板/图片转 base64）需浏览器实机验证

## 下一步

- 微信排版「风格多选 + 主题风格库分流派」（杂志/卡片/简约/复古）增强
- 浏览器实测三工具 + 主页的深浅切换与诊断定位交互
- 提交并推送 GitHub（autocrlf=false）