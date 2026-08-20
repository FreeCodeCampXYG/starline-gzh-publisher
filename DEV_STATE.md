# DEV_STATE

## 当前目标

- 基于了 [eternityspring/article-tools](https://github.com/eternityspring/article-tools) 改造为带 Starline 自身特色的内容创作工具集。
- 保留零依赖、打开即用的成熟能力：md→微信富文本复制、封面生成、二维码、本地直推草稿箱。
- 新增小红书排版功能（md→小红书图文，纯文本 + #话题标签 + 图片复制）。
- 规划简历排版等后续扩展。

## 已完成

- **公开仓库**：`FreeCodeCampXYG/starline-gzh-publisher`；Pages：`https://freecodecampxyg.github.io/starline-gzh-publisher/`。
- **工具集**（`tools/` 目录）：
  - `index.html` — Starline 工具箱首页，品牌白标，无推广内容
  - `cover.html` — 封面生成器（13 配色、4 装饰、8 预设、10 模板，导出 PNG / 复制图片）
  - `md-to-wechat.html` — Markdown → 微信公众号富文本（44 主题：35 原版 + 9 Starline 主题，ClipboardItem 富文本复制）
  - `md-to-xiaohongshu.html` — **Markdown → 小红书图文**（纯文本 + #话题标签 + 图片复制，Starline 粉色主题，字数统计）
  - `md-to-x.html` — Markdown → X 排版
  - `qrcode.html` — 生成与解析二维码
  - `draft.md` / `demo.md` — 写作规范与封面配置
- **本地发布服务**（`server/`）：
  - `publish-wechat.mjs` — 直推公众号草稿箱（零依赖，需 Node ≥ 18，配置 AppID/Secret 后 `npm start`）
- **去推广化**：所有工具无「烁皓/AI 交流群/hao_dev/Coverly/eternityspring」品牌残留，已替换为 Starline/墨点星痕。
- **Pages 构建**（`scripts/build_site.py`）：
  - 9 个主题 mock
  - 多平台输出：`wechat.html` / `xiaohongshu.html` / `visual-card.svg`
  - 内容索引 `index.json`
  - 工作台编辑器（左编辑右预览）
- **测试**：`scripts/test_build_site.py` 回归测试通过（1/1 OK）。
- **`git diff --check`**：通过（无空白/冲突问题）。

## 当前边界

- 静态 Pages 无后端、无 AI、无 Token。
- 本地草稿编辑、远程发布和凭据服务未实现（需本地 `server/publish-wechat.mjs`）。
- 小红书富文本渲染为纯文本格式（小红书平台限制），不支持样式主题切换。
- 封面生成器依赖 `html-to-image` CDN，离线时导出功能不可用。
- `resume` 当前仅路线图，不是投递级简历编辑器。
- `study-note` 当前仅模块路线图，非来源分析成品。

## 验证

- 本地 Python 构建通过（`python scripts/build_site.py --content content --output _site`）。
- 回归测试通过（1/1）。
- `git diff --check` 通过。
- 生成 HTML 危险 URL、外部脚本和 `onclick` 扫描无命中。

## 下一步

1. 补充 frontmatter/schema 校验、媒体安全检查与更完整 Markdown/主题组件。
2. 把内容索引契约拆成可复用的 `data/` 与前端模块，支持本地草稿 import/export。
3. 设计 AI 选区编辑的 before/after、版本锚定、接受/拒绝/局部接受/回退协议。
4. 接入真实简历排版功能（`resume` 模块）。
5. 接入真实学习材料来源定位（页码/时间戳）。