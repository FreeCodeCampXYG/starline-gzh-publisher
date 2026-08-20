# DEV_STATE

## 当前目标

- 将独立 Markdown → 微信 HTML Pages MVP 重构为 Starline Content Studio：内容源资产、内容目录、多视图预览与输出适配器。
- 公众号是第一个出口；后续扩展学习笔记、事实保真的简历编辑和可逆 AI 选区编辑。

## 已完成

- 公开仓库：`FreeCodeCampXYG/starline-gzh-publisher`；Pages：`https://freecodecampxyg.github.io/starline-gzh-publisher/`。
- 保留 GitHub Actions 静态构建、9 个主题、`wechat.html` 输出和 `index.json` 索引。
- 新增 `experience-brief.md`，明确首要任务、唯一主行动、移动端目标、渐进披露与视觉禁区。
- `scripts/build_site.py` 重构为可编辑的多平台工作台：左侧 textarea 编辑/粘贴，右侧实时公众号、小红书图文或 SVG 视觉卡片预览；支持平台/主题切换、复制当前 HTML、导出当前 HTML、本地草稿保存；同时保留文章详情、内容索引和未来类型元数据。
- 新增平台输出契约：`wechat`、`xiaohongshu`、`visual`；构建文章额外生成 `xiaohongshu.html` 与 `visual-card.svg`。SVG 为安全的文本/几何图卡，不调用远程图片或 API。
- 更新 `content/welcome.md`；新增 `content/resume-roadmap.md` 与 `content/study-note-roadmap.md`，用真实内容验证未来模块边界。
- 新增 `scripts/test_build_site.py`，覆盖索引元数据、多视图产物和公众号输出。
- README 已记录借鉴 [eternityspring/article-tools](https://github.com/eternityspring/article-tools) 的范围与不复制原则。

- 公众号复制已对齐 `starline-gzh-design`：复制与 `wechat.html` 只输出 `data-wechat-root` 内的纯 `<section>` 正文片段，不再复制工作台的 `<html>/<style>/<script>/<button>` 外壳；使用 `starline-gzh-design/scripts/validate_gzh_html.py` 校验通过。

## 当前边界

- 静态 Pages 无后端、无 AI、无 Token，浏览器不直接写 GitHub；本地草稿编辑、远程发布和凭据服务未实现。
- 当前微信公众号适配已使用 Apple Open Course 主题结构：任务封面、导读、STEP 章节、关键词标记、结论块、END/签名区；不再使用工作台页面样式作为公众号正文。
- Markdown 渲染器仍是 MVP，不等同于 `starline-gzh-design` 完整主题组件库；真实微信粘贴、完整浏览器设备视口、真人可用性评审是 `missing evidence`。
- `resume` 当前是分类与路线图内容，不是投递级简历编辑器；完整简历工作流仍归 `qiaomu-campus-resume`。
- `study-note` 当前是模块路线图，不是来源分析成品；真实来源输入后应遵循 `starline-study-web` 证据与公开发布 gate。

## 验证

- 编辑—预览工作台构建成功。
- Python 回归测试通过：1/1。
- `git diff --check` 通过。
- 生成 HTML 危险 URL、外部脚本和 `onclick` 扫描无命中。

## 下一步

1. 补充 frontmatter/schema 校验、媒体安全检查与更完整 Markdown/主题组件。
2. 把内容索引契约拆成可复用的 `data/` 与前端模块，支持本地草稿 import/export（不远程写入）。
3. 设计 AI 选区编辑的 before/after、版本锚定、接受/拒绝/局部接受/回退协议。
4. 根据真实学习材料接入页码/时间戳来源定位；根据事实数据接入简历适配器。
