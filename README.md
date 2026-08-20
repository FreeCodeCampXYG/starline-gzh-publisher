# Starline Content Studio

一个源内容，多种输出。

按照 Markdown 格式写作，剩下的交给工具。封面、公众号排版、小红书图文、X 文章——打开即用，点击完成。

## 工具列表

所有工具在 `tools/` 目录下，直接打开 `tools/index.html` 即可看到完整工具列表：

| 工具 | 文件 | 用途 | 特性 |
|------|------|------|------|
| 封面生成器 | `cover.html` | 生成文章封面图 | 13 配色、4 装饰、8 预设、10 模板，PNG 导出/复制 |
| 二维码工具 | `qrcode.html` | 生成与解析二维码 | 支持 Logo 嵌入，拖放/粘贴解析 |
| MD → 微信排版 | `md-to-wechat.html` | Markdown 转微信富文本 | 44 主题、格式自动修复、不支持的格式转 SVG、表格列设置 |
| MD → 小红书图文 | `md-to-xiaohongshu.html` | Markdown 转小红书图文 | 纯文本 + #话题标签、字数建议、图片复制 |
| MD → X 排版 | `md-to-x.html` | Markdown 转 X 长文格式 | 粗体保留、代码块转纯文本、图片单独复制 |
| 简历排版 | — | 将结构化简历排版为可投递格式 | 即将上线 |

## Markdown 过滤层

所有工具内置了 `md-filter.js` 过滤层，自动执行以下操作：

### 格式归一化
- 全角标点 → 半角（保证 marked.js 正确解析）
- 标题修复（`#标题` → `# 标题`）
- 列表标记统一为 `-`
- 代码块前后补空行
- 引用块修复（`>` 后加空格）
- 分隔线统一为 `---`
- 表格对齐行修复
- 中文与英文之间自动加空格

### 不支持的格式 → SVG
对微信公众号不支持的格式（数学公式 `$$`、Mermaid 图、LaTeX、Graphviz 等），自动转换为 SVG 图片插入，保留视觉信息。

### 格式诊断
检测未闭合代码块、标题层级跳跃、表格对齐问题等，在界面底部给出提示。

## 发布到公众号草稿（可选）

`md-to-wechat.html` 右上角有「发布到草稿」按钮，可把排好版的文章一键推送到公众号**草稿箱**（只建草稿、不群发）。

需要本地启动一个小服务：

```bash
cd server
cp .env.example .env      # 填 WECHAT_APPID / WECHAT_APPSECRET / 封面
npm start                 # 需 Node ≥ 18，零依赖
```

启动后通过 `http://127.0.0.1:3007/md-to-wechat.html` 打开工具即可使用发布功能。

## 写作规范

参考 `tools/draft.md` 的格式：

1. 在 Markdown 正文顶部用 ` ```json ` 块配置封面元数据（标题、副标题、作者、配色等）。
2. 从 `## 正文` 开始写正文内容。
3. 打开对应工具，自动读取配置并渲染。

## 使用方式

1. 在 `tools/draft.md` 中按规范写作。
2. 打开 `tools/index.html` 选择对应工具。
3. 工具自动读取草稿，实时预览。
4. 点击复制/导出，粘贴到对应平台发布。

## 设计取舍

- **零依赖**：所有工具是纯前端单文件 HTML，无需安装，打开即用。
- **无需服务器**：封面、排版、二维码全部在浏览器本地完成。
- **格式容错**：内置 md-filter.js 过滤层，自动修复非标准 Markdown 格式。
- **借鉴了** [eternityspring/article-tools](https://github.com/eternityspring/article-tools) 的成熟思路，改为 Starline 品牌并增加了小红书排版、格式过滤等功能。

## 边界

- 静态 Pages 无后端、无 AI、无 Token。
- 本地草稿编辑、远程发布和凭据服务未实现（需本地 `server/publish-wechat.mjs`）。
- AI 选区改写、差异审阅和 Fireworks 技术图将作为后续阶段加入。

## 许可证

MIT License，版权归 墨点星痕 (starline)。