```json
"changes": {
  "background": {
    "type": "scheme",
    "index": 1,
    "name": "翡翠"
  },
  "content": {
    "label": "Starline 的开源工具",
    "title": "开源了我的写作三件套：封面生成 + 公众号排版 + X 排版",
    "subtitle": "专注写作，其他的交给工具",
    "author": "@starline · 墨点星痕"
  },
  "typography": {
    "labelSize": 2.7,
    "titleSize": 5.3,
    "subtitleSize": 3.1,
    "contentWidth": 77
  }
}
```

## 正文

写完文章，还有几件事要做：出封面、公众号排版、小红书图文、X 排版。

每件事都要开不同的工具，反复复制粘贴、对齐格式。写了半小时，收尾花了一小时。

我开源了五个浏览器工具解决这个问题，零安装，打开即用。

---

### 工具在哪里

项目地址：[https://github.com/FreeCodeCampXYG/starline-gzh-publisher](https://github.com/FreeCodeCampXYG/starline-gzh-publisher)

克隆或下载后，启动一个 web 服务即可访问。无需安装任何依赖。

目前包含五个工具：

| 工具 | 文件 | 用途 |
|---|---|---|
| 封面生成器 | `cover.html` | 生成文章封面图 |
| MD → 微信排版 | `md-to-wechat.html` | Markdown 转微信富文本 |
| MD → 小红书图文 | `md-to-xiaohongshu.html` | Markdown 转小红书图文 |
| MD → X 排版 | `md-to-x.html` | Markdown 转 X 长文格式 |
| 二维码工具 | `qrcode.html` | 生成与解析二维码 |

---

## 封面生成器

写完文章的第一件事：出封面。

打开 `cover.html`，工具会自动读取 `draft.md` 里的封面配置，标题、副标题、作者、字体、配色全部自动填入。

左侧选一个预设（8 个快速起点），点一下颜色、装饰全部联动切换。不满意再微调。右上角「下载 PNG」或「复制图片」，完成。

熟悉之后，从打开工具到出图不超过两分钟。

---

## MD → 微信排版

Markdown 写完，直接粘贴到公众号编辑器，格式全乱。

打开 `md-to-wechat.html`，工具会自动读取 `draft.md` 里的文章内容，右侧实时预览微信样式。点「复制富文本」，直接粘贴进公众号编辑器，格式完整保留。

支持标题、正文、引用块、代码块、加粗、列表，覆盖日常写作的全部需求。

---

## MD → 小红书图文

小红书需要的是口语化、有情绪、带话题的短文案。

打开 `md-to-xiaohongshu.html`，工具会自动读取 `draft.md` 里的文章内容，右侧实时预览小红书图文样式。点「复制富文本」，直接粘贴进小红书编辑器，自动带上 #话题标签。

注意：小红书是纯文本平台，代码块会保留但样式从简；图片需要单独点「复制图片」粘贴。

---

## MD → X 排版

在 X 发长文，换行和格式是最大的问题。

打开 `md-to-x.html`，工具会自动读取 `draft.md` 里的文章内容，右侧按 X 的排版规则实时渲染：段落间距、粗体保留、代码块转纯文本。复制后直接粘贴发布。

注意：X 不支持代码块，所以代码块会转成纯文本。x也不会自动上传图片。所以需要点击图片上的复制按钮，手动到 x 文章编辑器中粘贴。

---

## 完整工作流

```
写 draft.md
  ↓
cover.html → 封面图（下载 / 复制）
  ↓
md-to-wechat.html → 复制富文本 → 粘贴公众号
  ↓
md-to-xiaohongshu.html → 复制富文本 → 粘贴小红书
  ↓
md-to-x.html → 复制内容 → 粘贴 X
```

五个工具独立，按需取用。全部基于本地文件，没有账号、没有服务器、不联网。

---

## 最后

所有代码都在单个 HTML 文件里，可以让你的 Agent 按自己的需求编排优化。

这个工具是独立的，每写完一次内容，可以做一个归档 .skill，把草稿和封面图一起归档到你指定的位置。

---
*运行 /score 评分 | 修改满意后运行 /archive 存档*