# DEV_STATE.md — Starline Content Studio

## 当前目标

全面改造 starline-gzh-publisher 项目，包括：
1. ✅ md-filter.js Markdown 过滤层（非标准格式转标准 MD，不支持的格式转 SVG）
2. ✅ 三大工具（wechat / x / xiaohongshu）统一为明亮「写作转换」v2 设计
3. ✅ 格式诊断交互：行号定位 + 左侧高亮 + 修复建议
4. ✅ 主页 index.html 改为明亮主题 + 深浅主题切换
5. ✅ 品牌升级为「Starline Writer · 一份内容，三种平台」
6. ✅【本次】杂志组件排版引擎：wechat 与 x 两工具接入组件化排版（封面卡/目录/章节编号/关键词标记/签名区），告别生硬单调；署名用户可设 & localStorage 缓存；主题系统修复并扩展为 9 套

## 本次专项：杂志组件排版引擎

用户反馈旧排版「生硬单调」。借鉴 starline-gzh-design 技能精髓，新建组件引擎并接入公众号与 X 两工具，遵循「slow is fast」：新增隔离、不做整体重构。

### 新增核心文件
- **`tools/md-components.js`**：组件排版引擎 ≈430 行，高内聚（组件函数集中）低耦合（主题仅当参数）
  - 分块器：标题/段落/引用/列表/代码/图片/表格/分割线 → 结构化 block 流（含代码块围栏、连续引用/列表收集、表格解析）
  - 组件函数：封面卡（标题按标点断两行、渐变底条、顶部 TOP LABEL、底部品牌渐变条）、横向滚动目录（前 3 章 + 写在最后）、编号章节（`PART 01` 大数字 + 英文标签，末章 `∞`）、引言/金句/提示左竖条块、正文关键词下划线、深色代码卡（mac 三圆点抬头 + 语言标签）、圆角图片卡、期刊表格（主色表头斑马纹）、参考资料脚注列表、署名区
  - 公众号规范：全文全角标点、内联 `<span leaf="">` 包裹所有文本节点（粘贴素材不丢样式）、链接→上标脚注（`<sup>` 标记 + 文末纯文本 URL 列表，不保留可点击 `<a>`）
  - 关键词标记：尊重 `==高亮==` / `++下划线++` / `**加粗**`；未标记的普通段落启发式挑 1 个关键词（引号内短语 → 含数字/英文短语 → 首个完整短语）
- **`tools/md-themes.js`**：9 套主题色板（摸鱼绿 / 科技钴蓝 / 红白 / 石墨极简 / 苹果公开课 / 留白禅意 / 摸鱼票据 / 橄榄手记 / 克莱因蓝），每套 `primary/secondary/softBg/softBorder/deep/ink/underline/hlBg/codeBg/codeText`；组件函数按色板渲染

### 封面文案 front-matter 引入 + 一步操作
- **`md-components.js` 新增 `parseFrontMatter(md)`**：解析文档顶部 `---` front-matter 块 → `{ data, body }`（body 为去掉 front-matter 的正文），支持 `title/subtitle/brand/tags[数组|逗号]/topLabel/strike/author/bio/date`，兼容 BOM（`^\uFEFF?---`）
- `render()` 内部自动调用 parseFrontMatter；封面/签名字段优先级：`front-matter > options/签名设置 > 内置默认`；返回对象新增 `frontmatter` 字段
- **一步操作**：粘贴含 front-matter 的 Markdown → 「杂志排版」开关（默认开）自动读取封面文案 + 主题 + 签名联动，无需手动输入

### 关键词下划线截断 bug 修复
- 原 `pickKeyword` 第 2 条正则会把连续英文词组拦腰截断（如「Starline Content Studio」被标成「Starline Cont」+ 残缺「ent Studio」）
- 重写为优先选「含数字完整短语」→「完整英文/数字单词（词边界内）」→「中文短语」，保证关键词是完整词、不破坏句子
- 用去标签纯文本验证「Starline Content Studio 要解决的问题」「管理 GraphQL 状态很优雅」等句子完整保留

### md-to-wechat.html 接入
- 控制栏新增「杂志排版」开关（默认开，记忆 `md2wechat-components`）+「署名」按钮（弹窗填署名/简介，缓存 `md2wechat-signature`；`getSignature()` 读取）
- `render()` 分支：开关开 → `MdComponents.render(md, MdThemes.get(currentThemeKey), {signature,...})`；关 → 原有 marked+CSS 渲染
- **修复主题菜单 bug**：删除 `THEME_GROUPS = THEME_DATA.groups`（原 undefined），改由 `MdThemes.all()` 构建 `buildStyleMenu`，9 套主题可点选即时换色
- `buildWechatHTML()` 组件模式直接克隆预览里 `section[style*=max-width:677px]`（已内联+leaf）
- 初始化同步开关 UI + 应用记忆主题/开关

### md-to-x.html 接入
- 同样加脚本引用、`render()` 组件分支、开关、署名、主题下拉（默认石墨极简，贴近 X 气质）
- `buildXHTML()` / `copyRichText()` 沿用 `.x-content` 克隆逻辑，组件 HTML 已在其中，无需改动

### md-to-xiaohongshu.html 接入
- 同样加脚本引用、`render()` 组件分支（默认摸鱼票据主题，贴合小红书）、开关、署名、主题下拉
- 组件模式：小红书卡片（头像/作者/时间）内渲染组件化正文；仍用 `convert()` 提取 #话题标签 + 字数哨兵（「全文 N 字 · 偏长可精简」）照常工作
- 复制适配：`buildXhsText()` 组件模式取 `.xhs-body` 纯文本（含 PART 01 章节编号，保留杂志感）；`copyRichText()` 富文本=组件 HTML、纯文本=纯文本，双格式
- 实测（Edge headless）：xhs-card 内组件封面/正文渲染成功，标签「工具在哪里 封面生成器…」+ 字数哨兵正常

## 实测（Edge headless --dump-dom）

| 页面 | leaf | 封面 | 目录 | 关键词下划线 | 链接→脚注 | 主题 | 开关 |
|------|------|------|------|------------|----------|------|------|
| md-to-x.html | 164 | ✅ | 📦 9 Parts | `#52525B` ✅ | 项目地址:[1] ✅ | 下拉✅ | ✅ |
| md-to-wechat.html | 167 | ✅ | — | — | — | 摸鱼绿✅ | ✅ |
| md-to-xiaohongshu.html | — | ✅ | 📦 9 Parts | — | — | 摸鱼票据✅ | ✅ |

- 9 套主题 `MdComponents.render` 逐一通过（Node 冒烟）；含 BOM 的 front-matter 文档在 9 套下均正确解析 title/brand/topLabel/strike/tags/author/bio/date 且回退正常
- 全部 JS 过 `vm.Script` 语法校验

## 核心文件

| 文件 | 用途 |
|------|------|
| `tools/md-components.js` | 杂志组件排版引擎（新增核心） |
| `tools/md-themes.js` | 9 套主题色板（新增） |
| `tools/md-filter.js` | Markdown 过滤 + 诊断 |
| `tools/md-to-wechat.html` | 微信公众号排版（接入组件模式） |
| `tools/md-to-x.html` | X 文章（接入组件模式） |
| `tools/md-to-xiaohongshu.html` | 小红书图文（接入组件模式） |
| `tools/index.html` | 主页（明亮 + 深浅切换） |

## 已知问题

1. `_site/` 已 .gitignore，构建产物不入库；改动只提交 `tools/`
2. `file://` 下 `fetch('./draft.md')` 被浏览器拦截，需 HTTP 服务访问
3. 封面 `topLabel/brand/subtitle/日期/标签/strike 划线句` 已通过 front-matter 可配；未在 front-matter 声明时回退内置默认/签名
4. 传统 CSS 模式（开关关）仍渲染 marked HTML，与组件模式视觉不同属预期（组件是新排版）
5. 正文关键词为启发式选取：无 `**`/`==`/`++` 标记的段落偶发挑词不准
6. pitch 到公众号时建议用组件模式默认；传统模式保留章样式/表格设置等旧能力（未删）
7. 小红书组件模式计数基于 `.xhs-body` 纯文本（含 PART 章节编号等组件文本），与纯文本模式字数口径略有差异（属预期）

## 下一步

- 用户实机打开三个工具（wechat / x / xiaohongshu）粘贴含 front-matter 的内容走「杂志排版」验收
- 若需，把章节标题英文标签 / 作者头像等做成可设置项（当前英文标签按标题关键词映射）
- 提交并推送 GitHub（autocrlf=false）