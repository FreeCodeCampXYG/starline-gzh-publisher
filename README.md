# starline-gzh-publisher

把 GitHub 仓库里的 Markdown 自动转换成多主题微信公众号 HTML，并部署为 GitHub Pages 内容目录。

## 使用方式

1. 将文章放进 `content/`。
2. 在 Markdown 顶部填写可选 frontmatter：

```yaml
---
title: 我的文章
slug: my-article
theme: apple-open-course
category: AI
tags: AI,产品,实践
status: published
---
```

3. 提交并推送到 `main`。
4. GitHub Actions 自动构建并部署 Pages。

当前已注册主题：`moyu-green`、`tech-cobalt`、`red-white`、`graphite-minimal`、`apple-open-course`、`zen-whitespace`、`moyu-ticket`、`olive-journal`、`klein-blue`。

## 产物

- 内容目录与搜索页；
- 每篇文章的浏览器预览；
- `wechat.html`：可复制的微信公众号 HTML；
- `index.json`：内容索引；
- Actions 构建失败时的错误日志。

## 边界

这是第一版静态 MVP，不调用 AI，不保存 Token，也不直接写 GitHub 内容。AI 选区改写、差异审阅和 Fireworks 技术图将作为后续阶段加入。

## 许可证

MIT License，版权归 墨点星痕 (starline)。
