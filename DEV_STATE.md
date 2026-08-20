# DEV_STATE

## 当前目标

- 独立维护 Markdown → 多主题微信公众号 HTML → GitHub Pages 内容管理器。
- 首版采用无后端、无 AI、无 Token 的静态 MVP；后续再接入 AI 选区编辑、差异审阅和 Fireworks 技术图。

## 已完成

- 创建公开仓库：`FreeCodeCampXYG/starline-gzh-publisher`。
- 首次提交：`0c7dd38`，已推送到 `main`。
- 配置 GitHub Actions：`.github/workflows/pages.yml`。
- 配置 Pages：`https://freecodecampxyg.github.io/starline-gzh-publisher/`。
- Actions 构建与部署成功：workflow run `32362727544`。
- 本地 MVP 构建成功：生成索引、文章预览和公众号 HTML。
- 示例文章：`content/welcome.md`。
- 已注册 9 个主题 ID，首版渲染器支持主题色和基础结构切换。
- GitHub 治理文件和 MIT License 已加入。

## 当前边界

- 首版不调用模型 API，不做浏览器端远程写入，不保存 GitHub Token。
- 当前 Markdown 渲染器是 MVP，不等同于完整 `starline-gzh-design` 组件库的全部排版能力。
- Pages 线上页面和 Actions 已验证；真实微信编辑器粘贴仍缺人工证据。

## 下一步

1. 将 `starline-gzh-design` 的完整主题组件渲染逻辑迁移为可复用构建模块。
2. 增加 frontmatter 校验、分类/标签索引、状态筛选和文章详情元数据。
3. 增加主题切换器和内容管理视图。
4. 增加安全媒体检查、完整 `validate_gzh_html.py` 和自动化测试。
5. 再设计 AI 选区编辑与接受/拒绝/回退流程，不把 API Key 暴露给 Pages 前端。
