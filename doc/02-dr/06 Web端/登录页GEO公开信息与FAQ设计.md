# 关联文档

| 类型 | 文档路径 |
|:---|:---|
| 原始需求 | `hipp-or/doc/01-or/【Web端】登录页GEO公开信息与FAQ.md` |
| 关联设计 | `hipp-or/doc/02-dr/06 Web端/Web用户端设计.md` |
| 测试设计 | `hipp-or/doc/03-tr/06 Web端/登录页GEO公开信息与FAQ测试设计.md` |
| GEO 源稿 | `hipp-geo/products/hipp-or/content/00-实体声明.md`、`01-FAQ-免费评估与边界.md` |

# 功能设计

## 路由

| 路径 | 登录 | 说明 |
|:---|:---|:---|
| `/login` | 否 | 左栏产品公开信息 + FAQ 摘要；右栏登录（原逻辑） |
| `/faq` | 否 | 完整 FAQ 文档页；顶栏链回登录 |
| `/` | — | 未登录 → `/login`；已登录 → `/requirement`（不变） |

静态文件（Vite `public/` → 构建进 `dist/`）：

| 路径（生产 base `/or/`） | 说明 |
|:---|:---|
| `/or/faq.html` | 无框架依赖的 FAQ 全文，供爬虫与分享 |

## 数据

`hipp-web/src/data/geoPublic.js` 导出：

- `displayName`、`oneLiner`、`canonicalUrl`、`doNotClaim[]`
- `advantages[]`：短标题 + 说明（与 `hipp-geo` entity、`rules-geo-public-advantages` 对齐）
- `shots[]`：截图相对路径（`geo/shot-*.png`）、图注、对应优势标题
- `faqItems[]`：`{ q, a }`（与 GEO FAQ 对齐）

LoginView / FaqView / 静态 HTML 同源文案；改文案先改该文件并核对 `hipp-geo` 源稿。截图放 `hipp-web/public/geo/`。

## 登录页布局

- 大屏两列：左 `story` 放实体 + **优势** + **截图（2 张）** + FAQ 摘要 +「不做」；右 `panel` 登录表单不变。
- 小屏上下：上信息公开，下登录。
- FAQ 页 `/faq` 与 `faq.html` 展示完整优势、4 张截图与全部问答。
- 不新增后端接口。

## SEO / GEO

- `index.html`：`meta name="description"` 含产品一句话。
- `application/ld+json`：`FAQPage`（问题列表与 `faqItems` 一致）。
- 静态 `faq.html` 含同构正文与指向 `/or/login` 的 CTA。

# 约束与边界

- 不承诺开发交付；不做私信接单叙事。
- 不修改 manager 鉴权与短信发送。
