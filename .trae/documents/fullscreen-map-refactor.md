# 全屏地图重构方案

## Context
用户要求去除首页、节点、LG、对等页面，将网络地图作为唯一公开页面，铺满整个屏幕。连线只保证在屏幕范围内（移除反子午线环绕逻辑）。Portal/Admin 路由全部保留，但从公开导航中移除。顶部导航栏和页脚完全移除，改为浮动叠加层。

## 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `app/web/pages.py` | 修改 | `/` 渲染地图；`/map`、`/nodes` 重定向到 `/` |
| `app/templates/base_fullscreen.html` | **新建** | 全屏基础模板（无 topbar/footer，浮动叠加层） |
| `app/templates/map.html` | 修改 | 继承 base_fullscreen；全屏布局；简化 JS（移除环绕逻辑） |
| `app/templates/base.html` | 修改 | topbar 移除 Home/Nodes/LG/Map 导航；footer 移除对应链接；bump CSS 版本 |
| `app/static/styles.css` | 修改 | 新增 `.map-fullscreen` 及浮动层样式；bump 版本 |

**不修改**：portal.py、admin.py、lg.py、app.js、i18n.js、admin/* 模板、main.py

## 实施步骤

### 1. 修改路由 `app/web/pages.py`

- `home()` → 改为调用 `build_map_data(db, demo=..., mock=...)`，渲染 `map.html`，`active="map"`。删除原有的 Node/PeerRequest 统计逻辑。
- `map_page()` → 改为 `return RedirectResponse("/", status_code=302)`
- `nodes_page()` → 改为 `return RedirectResponse("/", status_code=302)`。删除节点统计逻辑和 `infer_region`/`REGION_KEYWORDS`（已无引用）。
- `/login`、`/logout`、`/auth/kioubit/callback`、`/telegram/auth` 保持不变。

### 2. 新建 `app/templates/base_fullscreen.html`

无 topbar/footer 的全屏基础模板，包含：
- **head**：与 base.html 相同的 meta/title/styles.css(?v=6)/i18n.js(?v=7)/主题引导脚本
- **浮动顶部层** `.map-overlay-top`：左侧品牌链接 + 右侧 `.topbar-user`（复用 base.html 的用户菜单标记结构，含 `#theme-toggle`/`#lang-toggle` 按钮，使 i18n.js 和 app.js 无需修改即可工作）
- **内容块** `{% block fullscreen_content %}{% endblock %}`
- **浮动底部层** `.map-overlay-bottom`：版本号 + 备案码（若配置）
- **script**：app.js(?v=2) + i18n 初始化（不加载 lg.js）

关键：复用 `.topbar-user`/`.user-avatar-btn`/`.user-menu`/`#theme-toggle`/`#lang-toggle` 类名和 ID，确保 app.js（用户菜单下拉）和 i18n.js（主题/语言切换）无需修改。

### 3. 重写 `app/templates/map.html`

- `{% extends "base_fullscreen.html" %}`，用 `{% block fullscreen_content %}` 替换 `{% block content %}`
- 移除 `page_header` 宏调用
- 移除 `.map-page-wrap` 和 `.ospf-dashboard` 外层包裹，改用 `.map-fullscreen`
- 统计条、控件、图例改为浮动叠加（添加 `.map-stats-floating`、`.map-legend-floating` 类）
- SVG 地图填满整个容器

### 4. 简化 map.html 内联 JS

镜像 `admin/map.html` 的实现（已有简化版）：

- **`renderLinks()`**：移除 `|dx| > MAP_W/2` 环绕分支，每条链路只画一条直接贝塞尔曲线（参考 admin/map.html L390-420）
- **`loadWorldMap()`**：只画一份大陆路径，不画偏移副本（参考 admin/map.html L950-964）
- **`focusOnNodes()`**：简化为纯包围盒计算，移除间隙检测和坐标旋转（参考 admin/map.html L259-280）
- 保留日志系统（`_log`/`_warn`/`_sprintf`），但移除环绕相关统计日志

### 5. 修改 `app/templates/base.html`

- **topbar 导航**：删除 Home/Nodes/LG/Map 四个导航链接（L23-38），保留 Brand + Portal/Admin 链接（L39-51）
- **footer 链接行**：移除 `/nodes` 和 `/lg` 链接（L139-140），保留 `/` 和外部 dn42 链接
- **静态资源版本**：`styles.css?v=5` → `styles.css?v=6`

### 6. 修改 `app/static/styles.css`

新增全屏地图布局样式（CSS 变量 `--map-bg`/`--map-panel-bg`/`--map-legend-bg` 等已存在）：

```css
body.map-body { overflow: hidden; background: var(--map-bg); }
.map-fullscreen { position: fixed; inset: 0; overflow: hidden; }
.ospf-svg-wrapper.map-svg-fullscreen { position: absolute; inset: 0; border: none; border-radius: 0; }
.map-overlay-top { position: absolute; top: 0; left: 0; right: 0; z-index: 100; display: flex; justify-content: space-between; padding: 16px 20px; pointer-events: none; }
.map-overlay-top > * { pointer-events: auto; }
.ospf-stats-bar.map-stats-floating { position: absolute; top: 16px; left: 50%; transform: translateX(-50%); z-index: 90; display: flex; backdrop-filter: blur(12px); background: var(--map-panel-bg); border: 1px solid var(--map-panel-border); border-radius: var(--r-lg); padding: 8px 12px; }
.ospf-map-legend.map-legend-floating { position: absolute; bottom: 16px; left: 20px; z-index: 90; backdrop-filter: blur(8px); }
.map-overlay-bottom { position: absolute; bottom: 12px; right: 20px; z-index: 90; backdrop-filter: blur(8px); }
```

响应式：小屏幕下统计条下移避开顶部层。

## 验证步骤

1. 访问 `/` 看到全屏地图，无 topbar/footer，SVG 填满屏幕
2. 左上角品牌可点击回 `/`；右上角登录按钮或用户菜单正常工作
3. 主题/语言切换按钮在浮动层中生效
4. 统计条、控件、图例作为半透明面板浮动于地图之上
5. 链路只画一条直接曲线，无环绕段（SVG `overflow:hidden` 自然裁剪超出部分）
6. 大陆轮廓只渲染一份
7. 直接访问 `/portal`、`/admin`、`/login` 仍正常（带 topbar/footer）
8. `/nodes`、`/lg`、`/map` 重定向到 `/`
9. 备案码在右下角浮动层显示（若配置）
10. 浅色主题为默认，深色主题地图背景正确
