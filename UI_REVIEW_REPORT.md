# 知行录前端 UI 全面审查报告

> 审查日期：2026-05-13
> 审查范围：app/static/index.html、js/ 全部文件、report/ 模板文件、浏览器视觉验证
> 原则：不修改任何代码，仅输出分析与建议

---

## 一、总体评价

知行录的 UI 设计整体质量较高，具有以下亮点：

- **独特的设计语言**：米色纸张背景 + 深墨绿主色 + 金色点缀，营造出沉稳、有书卷气的投资工具氛围，区别于常见的红绿配色交易软件
- **字体选择讲究**：标题使用 Noto Serif SC 衬线体传递文化感，正文使用 Noto Sans SC 保证可读性，数字使用 IBM Plex Mono 保证对齐
- **组件一致性较好**：卡片、按钮、模态框在不同页面间保持了统一的圆角、阴影和配色
- **加载体验用心**：报告页有进度条 + 文字提示，诊断页有分步进度指示器

但也存在以下需要改进的问题，按优先级排列如下：

---

## 二、P0 — 必须修复（影响核心体验）

### P0-1：删除操作缺少二次确认（历史记录页）

**位置**：`index.html` — renderHistory() 函数、mailbox.js — deleteLetter()

**问题**：历史分析列表和信箱列表的删除按钮（垃圾桶图标）始终可见，在移动端极易误触。虽然 `deleteHistory()` 和 `deleteLetter()` 函数中使用了 `confirm()` 弹窗，但视觉上删除图标与卡片的可点击区域过于接近。

**改进方案**：
- 方案A：删除按钮默认隐藏，hover 卡片时显示（桌面端），移动端改为长按触发或滑动删除
- 方案B：增大删除按钮与卡片的间距，减小删除按钮的视觉权重（降低 opacity 到 0.2）
- 方案C：将删除操作收进一个 "..." 更多操作菜单中

**代码位置**：`index.html` L212-214（历史分析删除按钮）、`mailbox.js` L62-66（信箱删除按钮）

---

### P0-2：搜索建议无键盘导航支持

**位置**：`index.html` L101-124 — fetchHomeSuggestions()

**问题**：搜索下拉建议列表只能通过鼠标点击选择，不支持键盘 Up/Down 方向键导航和 Enter 选择。这对习惯键盘操作的用户（包括使用屏幕阅读器的用户）是严重的无障碍障碍。

**改进方案**：
- 监听 search-input 的 keydown 事件，支持 ArrowUp/ArrowDown 在建议项间移动
- Enter 键选中当前高亮项
- Escape 键关闭建议列表
- 为高亮建议项添加 `aria-selected="true"` 和 `role="option"`

---

### P0-3：ECharts 图表 resize 监听存在内存泄漏

**位置**：`charts.js` L167

**问题**：`_pie()` 方法中每次创建图表都执行 `window.addEventListener('resize', () => chart.resize())`，但从未移除监听器。用户多次切换 "实盘穿透" tab 后会累积大量 resize 监听器，导致性能下降。

**改进方案**：
- 在 `Charts` 对象中维护所有 chart 实例的引用
- 在 render 新图表前先 dispose 旧实例
- 使用单次全局 resize 监听，遍历所有实例调用 resize

```js
// 建议修改
const Charts = {
  _charts: [],
  _pie(id, title, data, customColors) {
    const el = document.getElementById(id);
    if (!el || !data.length) return;
    // 销毁旧实例
    const existing = echarts.getInstanceByDom(el);
    if (existing) existing.dispose();
    const chart = echarts.init(el);
    this._charts.push(chart);
    chart.setOption({ ... });
  },
  dispose() {
    this._charts.forEach(c => c.dispose());
    this._charts = [];
  }
};
// 全局 resize 只需注册一次
window.addEventListener('resize', () => {
  Charts._charts.forEach(c => c.resize());
});
```

---

### P0-4：截图导入无图片压缩/预览

**位置**：`import-screenshot.js` L45-77

**问题**：用户上传截图后直接以原图发送到服务器，没有前端压缩。券商 App 截图可能达到 5-10MB，上传耗时且消耗服务器带宽。同时上传后没有图片预览，用户无法确认上传的是否为正确的截图。

**改进方案**：
- 使用 Canvas 在前端将图片压缩到 1-2MB（JPEG quality 0.7-0.8）
- 上传前展示图片缩略图预览
- 添加文件大小显示和压缩比例提示

---

## 三、P1 — 重要改进（显著提升体验）

### P1-1：页面切换无加载过渡动画

**位置**：`router.js` — `_resolve()`、所有 render 函数

**问题**：路由切换时直接替换 `app.innerHTML`，页面内容瞬间变化，没有加载过渡或淡入效果。当网络较慢时用户会看到内容闪烁。

**改进方案**：
- 在 Router 中添加淡出 → 渲染 → 淡入的过渡
- 或使用 CSS 动画：新内容进入时 `opacity: 0 → 1` 配合 `transform: translateY(8px) → 0`
- 异步数据加载时展示骨架屏（Skeleton）或 spinner，而不是纯文字 "加载中..."

```css
/* 建议添加的过渡动画 */
.route-enter { animation: routeEnter 0.25s ease-out; }
@keyframes routeEnter {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

---

### P1-2：缺少 favicon 和社交分享 Meta 标签

**位置**：`index.html` L1-13 — `<head>` 部分

**问题**：
- 无 favicon，浏览器标签页显示默认图标
- 无 Open Graph (og:) 标签，分享链接到微信/Telegram 时无预览图
- 无 viewport 之外的移动端 meta（如 theme-color、apple-mobile-web-app-capable）

**改进方案**：
```html
<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
<meta name="theme-color" content="#2C3E2D">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta property="og:title" content="知行录 — 记录投资的知与行">
<meta property="og:description" content="AI 驱动的 A股/港股分析与持仓管理工具">
```

---

### P1-3：持仓页面图表穿透在移动端三列布局不可用

**位置**：`portfolio.css` L169-173 — `.chart-row`

**问题**：`chart-row` 使用 `grid-template-columns: 1fr 1fr 1fr` 三列布局，在移动端（<768px）媒体查询中虽然改为了单列，但切换断点为 768px 偏高。在 iPad 竖屏等中等宽度屏幕上，三个饼图挤在一起非常小，难以阅读。

**改进方案**：
- 在 768px-1024px 区间使用双列布局（2+1 排列）
- 在 <768px 使用单列布局
- 考虑在小屏幕上默认隐藏某些次要图表，提供 "展开全部" 按钮

```css
@media (max-width: 1024px) {
  .chart-row { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 640px) {
  .chart-row { grid-template-columns: 1fr; }
}
```

---

### P1-4：诊断表单方向按钮颜色语义混乱

**位置**：`diagnosis.css` L92-104 — `.diag-direction-btn.active.*`

**问题**：
- "买入"和"加仓"使用橙红色（#D97757），"卖出"和"减仓"使用绿色（#7A9B6E）
- 在 A 股语境下，红色=涨、绿色=跌，但这里红色=买入操作、绿色=卖出操作，与行情颜色语义相反
- 用户在股票软件中习惯了红涨绿跌，这里的反向配色可能造成认知混淆

**改进方案**：
- 方案A：统一使用品牌色（深墨绿 #2C3E2D 或金色 #C9A961）作为选中状态，淡化方向色
- 方案B：买入用红色、卖出用绿色（与 A 股行情一致），但降低饱和度
- 方案C：改用图标 + 文字组合，减少对颜色的依赖

---

### P1-5：错误提示方式不统一

**位置**：多处代码

**问题**：
- 添加持仓时数量错误：使用内联红色文字提示（`#shares-error`）
- 成本价为空时：使用 `alert()` 弹窗
- 搜索出错：在结果区域显示文字
- 行情加载失败：在 DOM 中显示灰色文字
- 截图导入失败：使用 `alert()` 弹窗

这种不一致的错误反馈方式降低了产品的专业感。

**改进方案**：
- 建立统一的 Toast/Notification 组件，所有非表单验证错误使用 Toast
- 表单验证错误使用内联提示（已有部分实现）
- 网络错误使用顶部横幅（Banner）提示
- 彻底移除 `alert()` 调用

---

### P1-6：首页加载状态过于简陋

**位置**：`index.html` L69-74 — `#loading`

**问题**：分析加载时只显示一条细进度条和一行文字，没有：
- 取消按钮（用户无法中止正在进行的分析）
- 分步进度提示（不像报告页那样展示 "正在分析商业模式..." 等阶段）
- 超时处理（如果 LLM 响应超时，用户只能刷新页面）

**改进方案**：
- 添加 "取消" 按钮，调用 `AbortController` 中止 fetch
- 添加超时提示（30秒后提示 "分析时间较长，请耐心等待..."）
- 使用 `AbortController` 管理请求生命周期

---

### P1-7：持仓详情页操作按钮拥挤

**位置**：`portfolio.js` L208-213 — `.detail-actions`

**问题**：展开持仓详情后，底部有 4 个按钮（修改持仓、查看深度分析、诊断交易、移除）水平排列并自动换行。在窄屏设备上按钮可能重叠或换行不美观。"移除" 使用 btn-danger 红色但位置在最右侧，容易被忽略。

**改进方案**：
- 桌面端：按钮水平排列
- 移动端：改为两行排列（主要操作在上，危险操作在下）
- 或者使用图标按钮节省空间
- "移除" 按钮应添加确认对话框（目前 `showDelete` 已有确认弹窗，但视觉权重不够）

---

### P1-8：报告页直接在新窗口打开，脱离 SPA 框架

**位置**：`index.html` L144-147 — `startAnalysis()`

**问题**：`startAnalysis()` 直接使用 `window.location.href` 跳转到 `/api/report/{symbol}`，这会导致：
- 失去 SPA 的导航体验（无法通过浏览器后退返回）
- 新窗口没有返回按钮，用户需要手动关闭或后退
- 报告页是纯 HTML（由 html_template.py 生成），没有 SPA 的导航栏

**改进方案**：
- 方案A：在 SPA 内新建一个路由（`/#/report/{symbol}`），用 iframe 或 fetch 加载报告
- 方案B：至少在新窗口打开 `window.open()` 让用户保留原页面
- 方案C：给报告页的 HTML 模板添加 "返回知行录" 按钮（目前只有下载按钮）

---

## 四、P2 — 优化建议（锦上添花）

### P2-1：缺少暗色模式（Dark Mode）支持

**现状**：所有 CSS 变量使用固定的颜色值，没有 `@media (prefers-color-scheme: dark)` 适配。

**改进方案**：
- 为 `:root` 添加暗色模式变量覆盖
- 在 CSS 中使用 `@media (prefers-color-scheme: dark)` 自动适配系统主题
- 或提供手动切换按钮，将主题偏好存入 localStorage

### P2-2：滚动体验可优化

**现状**：页面未使用平滑滚动（`scroll-behavior: smooth`）。在诊断页生成结果后，内容区域没有自动滚动到顶部。

**改进方案**：
- 在 CSS 中添加 `html { scroll-behavior: smooth; }`
- 路由切换时 `window.scrollTo(0, 0)`（Router 的 `_resolve()` 中已有）
- 诊断页内容生成后自动滚动到最新卡片

### P2-3：诊断聊天消息未渲染 Markdown

**位置**：`diagnosis.js` L314-347 — `_sendChat()`

**问题**：聊天消息直接使用 `innerHTML` 插入纯文本，如果 AI 回复包含 Markdown 格式（列表、加粗、代码块等），不会渲染。

**改进方案**：
- 在 `_sendChat()` 中对 AI 回复使用 `marked.parse()` 渲染
- 为用户消息保持纯文本（防止 XSS）

### P2-4：缺少 PWA 支持

**现状**：没有 `manifest.json` 和 Service Worker。

**改进方案**：
- 添加 `manifest.json` 使应用可安装到主屏幕
- 添加基础 Service Worker 缓存静态资源，支持离线查看已加载的报告

### P2-5：表格在移动端无横向滚动

**位置**：`portfolio.js` — `_renderDetailTable()`、`charts.js` — `_renderIndustry()`

**问题**：持仓明细表和分布表使用 `<table>` 元素，在移动端可能超出屏幕宽度。

**改进方案**：
- 外层包裹 `<div style="overflow-x:auto">` 容器
- 或使用 CSS `@media` 将表格在移动端转换为卡片列表

### P2-6：CDN 依赖无 fallback

**位置**：`index.html` L11-12

**问题**：ECharts 和 marked.js 完全依赖 jsdelivr CDN。如果 CDN 不可用（某些网络环境），页面功能完全失效。

**改进方案**：
- 将 ECharts 和 marked.js 下载到 `app/static/vendor/` 作为本地备份
- 或使用 `onerror` 回退到本地文件
- 对于报告页（html_template.py 中也有 CDN 引用）同样处理

### P2-7：持仓卡片展开/收起无动画

**位置**：`portfolio.js` L249-252 — `toggleDetail()`

**问题**：点击持仓卡片展开详情时直接 `display: none/block` 切换，无过渡动画。

**改进方案**：
- 使用 CSS `max-height` + `overflow: hidden` + `transition` 实现展开/收起动画
- 或添加一个小的旋转箭头图标指示展开状态

### P2-8：诊断进度指示器可以优化

**位置**：`diagnosis.css` L328-418 — `.diag-progress`

**问题**：诊断生成时的进度指示器（步骤列表）设计简单，仅用文字 + 图标。展开状态占据大量垂直空间。

**改进方案**：
- 添加连接线（竖线）将步骤图标连接起来，增强流程感
- 当前已有 collapsed 状态，但展开时的视觉层次可以加强
- 考虑将进度指示改为侧边栏样式（桌面端）或顶部进度条（移动端）

### P2-9：信件页面 "生成今日来信" 缺少禁用状态

**位置**：`index.html` L81-83

**问题**：点击 "生成今日来信" 后按钮没有禁用状态，用户可以重复点击导致多次请求。

**改进方案**：
- 点击后设置 `disabled` 状态
- 显示 "生成中..." 文字
- 添加 loading spinner

### P2-10：搜索建议列表 XSS 风险

**位置**：`index.html` L135-141 — `fetchHomeSuggestions()`

**问题**：搜索建议的 HTML 拼接直接使用 API 返回的数据，未经 HTML 转义。如果 API 返回恶意内容，可能导致 XSS。

**改进方案**：
- 使用 `textContent` 或 DOM API 创建元素，而非 innerHTML 拼接
- 或对 API 返回数据进行 HTML 转义

---

## 五、可访问性（Accessibility）审查

| 项目 | 状态 | 说明 |
|------|------|------|
| ARIA 标签 | ❌ 缺失 | 搜索框、按钮、卡片等缺少 `aria-label` |
| 键盘导航 | ❌ 部分缺失 | 搜索建议不可键盘导航，模态框无法 Escape 关闭 |
| 焦点管理 | ❌ 缺失 | 路由切换后焦点不会重置到新页面内容 |
| 颜色对比度 | ✅ 合格 | 深绿/深灰文字在米色背景上对比度良好（WCAG AA） |
| 语义化 HTML | ⚠️ 一般 | 大量使用 `<div>` + onclick，缺少 `<nav>`、`<main>`、`<button>` 语义标签 |
| 屏幕阅读器 | ❌ 未测试 | 未使用 `role`、`aria-live` 等辅助技术属性 |
| 图片 alt 文本 | ✅ 合格 | 页面无图片，SVG 图标有 title 属性 |

**关键改进**：
1. 为所有 `<div onclick="...">` 改为 `<button>` 或添加 `role="button" tabindex="0"` 和 keydown 处理
2. 为搜索建议列表添加 `role="listbox"` 和 `role="option"`
3. 模态框添加 `role="dialog"` 和 `aria-modal="true"`
4. 路由切换后 `document.getElementById('app').focus()` 或使用 `aria-live` 区域

---

## 六、性能审查

| 项目 | 状态 | 说明 |
|------|------|------|
| 首次加载体积 | ⚠️ 可优化 | 3个 Google Fonts + 2个 CDN JS = 5个外部请求 |
| ECharts 全量加载 | ⚠️ 可优化 | 加载完整 echarts.min.js (~1MB)，首页和持仓页不需要图表 |
| CSS 内联 | ✅ 良好 | 报告页 CSS 内联减少请求 |
| localStorage 缓存 | ✅ 良好 | 行情数据有 1 小时 TTL 缓存 |
| 图片优化 | ❌ 缺失 | 截图导入无前端压缩 |
| 虚拟列表 | ❌ 缺失 | 历史记录/信箱列表较长时会一次性渲染所有 DOM |

**关键改进**：
1. 将 ECharts 改为按需加载：只在切换到 "实盘穿透" tab 时动态创建 `<script>` 标签加载
2. 使用 `font-display: swap` 优化字体加载（Google Fonts 已默认支持）
3. 历史记录和信箱列表超过 20 条时实现虚拟滚动或分页

---

## 七、响应式设计审查

| 断点 | 状态 | 说明 |
|------|------|------|
| 移动端 <640px | ✅ 基本可用 | 单列布局、字体适当缩小 |
| 平板 640-1024px | ⚠️ 待优化 | 图表三列布局过窄，表单按钮间距过大 |
| 桌面 >1024px | ✅ 良好 | max-width 居中布局，内容不会过宽 |

**已知问题**：
1. 报告页 `@media (max-width: 600px)` 只覆盖了 DCF 控件和 bull-bear 布局，缺少对模块内容的响应式处理
2. 信函模板 `@media (max-width: 768px)` 覆盖了主要组件，但数据卡片在 4 列→2 列切换时可能排版不美观
3. 诊断表单无响应式断点，在大屏幕上表单区域过窄（max-width: 600px）

---

## 八、设计风格一致性审查

| 维度 | 状态 | 说明 |
|------|------|------|
| 配色方案 | ✅ 一致 | 所有页面共享 CSS 变量，颜色使用统一 |
| 圆角大小 | ⚠️ 不完全一致 | 卡片 12px，模态框 16px，按钮 8px/10px，搜索框 12px |
| 阴影深度 | ⚠️ 不完全一致 | 卡片 `0 2px 8px rgba(0,0,0,0.06)`，搜索建议 `0 4px 12px rgba(0,0,0,0.08)` |
| 字体层级 | ✅ 一致 | serif 用于标题，sans 用于正文，mono 用于数字 |
| 间距系统 | ⚠️ 不统一 | 大量使用内联样式的硬编码像素值，而非设计 token |
| 动画风格 | ✅ 一致 | 均为 0.2s-0.3s 的 ease 过渡 |
| 图标风格 | ⚠️ 不一致 | 混合使用 SVG 图标、emoji（📊、⏰、🌡️）、Unicode 字符（○、✓） |

---

## 九、建议优先级汇总

| 优先级 | 编号 | 问题 | 影响范围 |
|--------|------|------|----------|
| P0 | P0-1 | 删除操作易误触 | 历史页、信箱页 |
| P0 | P0-2 | 搜索建议无键盘导航 | 首页 |
| P0 | P0-3 | ECharts 内存泄漏 | 持仓页 |
| P0 | P0-4 | 截图导入无压缩/预览 | 持仓页 |
| P1 | P1-1 | 页面切换无过渡 | 全局 |
| P1 | P1-2 | 缺少 favicon/Meta | 全局 |
| P1 | P1-3 | 图表移动端布局 | 持仓页 |
| P1 | P1-4 | 方向按钮颜色语义 | 诊断页 |
| P1 | P1-5 | 错误提示不统一 | 全局 |
| P1 | P1-6 | 首页加载状态简陋 | 首页 |
| P1 | P1-7 | 详情按钮拥挤 | 持仓页 |
| P1 | P1-8 | 报告页脱离 SPA | 全局 |
| P2 | P2-1~P2-10 | 各类优化建议 | 各页面 |

---

## 十、总结

知行录的前端 UI 在设计审美上已经非常成熟——独特的配色方案、精心的字体选择、一致的卡片式设计语言都展现出较高的设计水准。主要改进空间集中在**交互细节**（键盘导航、删除确认、加载状态）、**性能优化**（ECharts 内存泄漏、CDN fallback、图表按需加载）和**可访问性**（ARIA 标签、语义化 HTML）三个方面。

建议优先处理 P0 级别的 4 个问题，它们直接影响核心功能的可用性和稳定性。P1 级别的改进将显著提升整体用户体验的专业感。
