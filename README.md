# Starline Content Studio

把 GitHub 仓库里的 Markdown 作为内容源资产，自动构建成可搜索的内容工作台，并输出阅读页与多主题微信公众号 HTML。公众号是第一个出口，未来可在同一内容模型上扩展学习笔记、简历编辑和其他发布适配器。

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

## 内容模型

每个 Markdown 文件可通过 frontmatter 描述 `title`、`slug`、`type`、`category`、`tags`、`status`、`theme` 与 `summary`。`type` 当前支持 `article`、`study-note`、`resume`、`project`，后两类先作为路线图与内容分类，不宣称已提供完整编辑器。

## 产物

- 内容目录：搜索、类型筛选、状态/标签摘要和排序；
- 每篇内容的阅读视图、公众号预览和内容契约说明；
- `wechat.html`：可复制的微信公众号 HTML；
- `index.json`：可被未来目录前端复用的稳定内容索引；
- GitHub Actions 失败时的构建日志。

## 设计取舍

本次重构借鉴了 [eternityspring/article-tools](https://github.com/eternityspring/article-tools) 的“零依赖、打开即用、Markdown 输入、多工具输出”思路，以及 `starline-study-web` 的任务优先、证据入口和渐进披露契约；没有复制其代码、素材、品牌或推广内容。

## 边界

这是第一版静态 MVP，不调用 AI，不保存 Token，也不直接写 GitHub 内容。AI 选区改写、差异审阅和 Fireworks 技术图将作为后续阶段加入。

## 许可证

MIT License，版权归 墨点星痕 (starline)。
