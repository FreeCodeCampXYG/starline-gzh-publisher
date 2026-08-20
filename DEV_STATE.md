# DEV_STATE.md — Starline Content Studio

## 当前目标

全面改造 starline-gzh-publisher 项目，包括：
1. ✅ 创建 md-filter.js Markdown 过滤层（非标准格式转标准 MD，不支持的格式转 SVG）
2. ✅ 改造 md-to-wechat 列设置界面（表格列宽、边框、斑马纹、悬停效果、表头对齐）
3. ✅ 重做主页 index.html（引导用户进入各功能，工作流指引，快速开始）
4. ✅ 完善首页文档 draft.md / demo.md / README.md
5. ✅ 更新其他工具适配 md-filter

## 已完成工作

### md-filter.js（Markdown 过滤层）
- 新建 `tools/md-filter.js`，纯前端零依赖，IIFE 自执行
- 格式归一化：全角标点→半角、标题修复（`#标题`→`# 标题`）、列表统一为 `-`、代码块前后补空行、引用块修复、分隔线统一、表格对齐修复、中文与英文间加空格
- 不支持的格式转 SVG：数学公式（$$）、Mermaid 图、LaTeX、Graphviz、PlantUML、自定义块（:::）→ 自动生成 SVG 图片
- 格式诊断：检测未闭合代码块、标题层级跳跃、表格对齐问题、列表标记不统一
- 公开 API：`MdFilter.process()`、`MdFilter.injectSVG()` 及各个归一化子函数

### md-to-wechat.html（微信排版）
- 集成 md-filter.js，渲染时自动过滤
- 新增设置面板（齿轮按钮）：表格列设置界面
  - 全局设置：显示边框、斑马纹、悬停高亮、表头对齐方式
  - 列宽设置：各列百分比宽度，留空自动均分
  - 诊断区域：显示 md-filter 格式诊断结果
- 底部统计栏：字数 + 行数 + 诊断按钮
- 表格渲染实时响应设置变更
- 全面中文注释，每个控制点说明原因

### index.html（主页）
- 品牌标识（S 图标）+ 渐变标题
- 3 步工作流指引：写 Markdown → 打开工具 → 一键输出
- 6 卡网格：封面、二维码、微信、小红书、X、简历（即将上线）
- 每张卡片附带特性标签（13 配色、44 主题等）
- 快速开始区域：写作规范展示 + 使用说明
- 使用说明按钮（锚点跳转）
- GitHub Star 计数

### 文档完善
- `draft.md`：更新为完整写作规范，增加 md-filter 说明，5 工具表格
- `demo.md`：更新为演示文档，与 draft.md 结构一致
- `README.md`：更新为完整项目文档，增加 md-filter 章节，特性表格

### 其他工具适配
- `md-to-x.html`：集成 md-filter.js，渲染时自动过滤
- `md-to-xiaohongshu.html`：集成 md-filter.js，渲染时自动过滤

## 核心文件

| 文件 | 大小 | 用途 |
|------|------|------|
| `tools/md-filter.js` | ~15KB | Markdown 过滤层（新建） |
| `tools/md-to-wechat.html` | ~87KB | 微信排版（改造完成） |
| `tools/index.html` | ~13KB | 主页（重做完成） |
| `tools/md-to-x.html` | ~20KB | X 排版（已适配 md-filter） |
| `tools/md-to-xiaohongshu.html` | ~30KB | 小红书排版（已适配 md-filter） |
| `tools/cover.html` | ~136KB | 封面生成器（未修改） |
| `tools/qrcode.html` | ~14KB | 二维码工具（未修改） |
| `tools/draft.md` | ~3KB | 写作规范（更新） |
| `tools/demo.md` | ~3KB | 演示文档（更新） |
| `README.md` | ~3KB | 项目文档（更新） |

## 已知问题

1. `cover.html` 和 `qrcode.html` 未集成 md-filter.js（它们不处理 Markdown 正文，暂不需要）
2. 预览中的表格设置面板（列设置界面）在切换主题后需要手动触发重新渲染
3. SVG 转换后的图片在微信公众号中可能因编辑器限制而显示异常，建议复制前先预览确认
4. `file://` 协议下 `fetch('./draft.md')` 被浏览器拦截，工具无法自动加载草稿，需通过 HTTP 服务访问

## 下一步计划

- 简历排版工具实现
- 封面生成器增加更多模板
- 微信排版主题增加更多自定义选项
- 考虑将 md-filter.js 作为 npm 包发布
- 写作规范增加更多示例