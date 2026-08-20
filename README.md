# Starline Content Studio

一个源内容，多种输出。

按照 Markdown 格式写作，剩下的交给工具。封面、公众号排版、小红书图文、X 文章——打开即用，点击完成。

## 工具列表

所有工具在 `tools/` 目录下，直接用浏览器打开即可：

| 工具 | 文件 | 用途 |
|------|------|------|
| 封面生成器 | `cover.html` | 生成文章封面图，13 配色、4 装饰风格、8 预设、10 模板，支持导出 PNG / 复制图片 |
| 二维码工具 | `qrcode.html` | 生成带 Logo 的二维码，支持解析（拖放/粘贴图片） |
| MD → 微信排版 | `md-to-wechat.html` | Markdown 转微信公众号富文本，44 种主题风格，支持复制富文本 |
| MD → 小红书图文 | `md-to-xiaohongshu.html` | Markdown 转小红书图文格式，纯文本 + #话题标签 + 图片复制 |
| MD → X 排版 | `md-to-x.html` | Markdown 转 X（Twitter）长文格式 |
| 简历排版 | — | 将结构化简历排版为可投递格式（即将上线） |

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

参考 `tools/draft.md` 和 `tools/demo.md` 的格式：

1. 在 Markdown 正文顶部用 ` ```json ` 块配置封面元数据（标题、副标题、作者、配色等）。
2. 从 `## 正文` 开始写正文内容。
3. 打开对应工具，自动读取配置并渲染。

## 使用方式（Pages 构建）

1. 将文章放进 `content/`（仅在需要 Pages 静态构建时）。
2. 在 Markdown 顶部填写可选 frontmatter（title, slug, theme, 等）。
3. 提交并推送到 `main`。
4. GitHub Actions 自动构建并部署 Pages。

当前已注册主题：`moyu-green`、`tech-cobalt`、`red-white`、`graphite-minimal`、`apple-open-course`、`zen-whitespace`、`moyu-ticket`、`olive-journal`、`klein-blue`。

## 设计取舍

- 零依赖：所有工具是纯前端单文件 HTML，无需安装，打开即用。
- 无需服务器：封面、排版、二维码全部在浏览器本地完成。
- 借鉴了 [eternityspring/article-tools](https://github.com/eternityspring/article-tools) 的成熟思路，改为 Starline 品牌并增加了小红书排版功能。
- 公众号没有富文本主题切换，但可复制多种风格的排版产物。

## 边界

- 静态 Pages 无后端、无 AI、无 Token。
- 本地草稿编辑、远程发布和凭据服务未实现（需本地 `server/publish-wechat.mjs`）。
- AI 选区改写、差异审阅和 Fireworks 技术图将作为后续阶段加入。

## 许可证

MIT License，版权归 墨点星痕 (starline)。