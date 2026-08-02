# 多级聚焦 + Peer 渐变色重构方案

## Context
用户要求重新设计地图聚焦结构为四级（L1全部地图→L2全部节点→L3区域→L4单节点），peer 会话用节点大小+渐变色集成在地图上，移除连线闪动（jitter）和节点光圈放大（pulse）动画。已 peer 的节点与未 peer 的节点需要有明显的视觉区分。

## 文件变更清单

| 文件 | 操作 |
|------|------|
| `app/templates/map.html` | 修改：HTML 结构（移除 jitter 按钮/pulse group/gradient defs，新增焦点指示器，更新图例）；JS 全面重构（焦点状态机、渐变色、节点渲染、交互） |
| `app/static/styles.css` | 修改：删除 pulse/jitter 旧样式，新增 ring/hollow/indicator/gradient 样式 |

## 实施步骤

### 1. CSS 变更 (`styles.css`)

**删除**（L7725-7750）：`.node-dot-ok/good/warn/err`（drop-shadow filter）、`.node-pulse` 及 `.node-pulse-*` 颜色类、`@keyframes ospf-pulse-anim`（L7178-7189）。

**保留**：`.node-dot` transition 基础规则（L7711-7713）、`.node-dot.node-dim`、`.node-dot.node-highlight`、`.node-name` 标签样式。

**新增**：
```css
/* 已 Peer 节点：实心 + 外环 */
.node-dot-peered { stroke: rgba(0,0,0,0.25); stroke-width: 0.5; }
.node-ring { fill: none; stroke-width: 1.5; pointer-events: none; opacity: 0.6; }
/* 未 Peer 节点：空心 */
.node-dot-hollow { fill: none; stroke: #64748b; stroke-width: 1.5; }
.node-dot-offline { fill: none; stroke: #475569; stroke-width: 1.2; opacity: 0.5; }
/* 焦点指示器 pill */
.focus-indicator { padding: 3px 10px; font-size: 0.7rem; color: var(--text-3); background: var(--map-panel-bg); border: 1px solid var(--map-panel-border); border-radius: 999px; text-align: center; white-space: nowrap; margin-top: 4px; }
.focus-indicator.active { color: var(--accent); border-color: var(--accent); }
/* 渐变图例 */
.legend-gradient { width: 120px; height: 8px; border-radius: 4px; background: linear-gradient(to right, hsl(140,75%,48%), hsl(90,75%,48%), hsl(40,75%,48%), hsl(0,75%,48%)); }
.legend-gradient-labels { display: flex; justify-content: space-between; font-size: 0.65rem; color: var(--text-3); }
.legend-hollow-dot { width: 10px; height: 10px; border: 1.5px solid #64748b; border-radius: 50%; display: inline-block; }
```

### 2. HTML 结构变更 (`map.html`)

- **移除**：`#jitter-btn` 按钮、`<g id="map-pulses">` group、`<radialGradient id="pulse-grad">` def
- **新增**：焦点指示器 `<div class="focus-indicator" id="focus-indicator">全部地图</div>`（在控件栏下方）
- **图例**：替换 "Peer 数量" 离散圆点为渐变条 + "无 Peer" 空心圆

### 3. JS 配色重构

删除 `getPeerClass`、`getPeerLabel`、旧 `getPeerColor(_class)`。新增：

```javascript
// HSL 渐变：绿(140°) → 黄(60°) → 红(0°)，0 peer 返回灰色
function getPeerColor(count) {
  if (!count || count <= 0) return '#64748b';
  var t = Math.min(1, count / 30);
  var hue = 140 * (1 - t);
  return 'hsl(' + Math.round(hue) + ',75%,48%)';
}
// 半径：max(4, min(14, 4 + count*0.4))
function getPeerRadius(count) {
  if (!count || count <= 0) return 5;
  return Math.max(4, Math.min(14, 4 + count * 0.4));
}
```

保留 `getLatencyClass`/`getLatencyColor`/`getLatencyLabel`（链路着色不变）。

### 4. JS 焦点状态机

```javascript
var CONTINENT_GROUPS = [
  { key:'asia', label:'亚洲', names:['Tokyo','Hong Kong','Singapore','Beijing','Shanghai','Guangzhou'] },
  { key:'europe', label:'欧洲', names:['London','Paris','Frankfurt','Warsaw','Amsterdam'] },
  { key:'north_america', label:'北美', names:['San Francisco','Los Angeles','New York'] }
];
var focusState = { level:'L1', continent:null, nodeId:null };
```

**状态转移**：
| 当前 | 触发 | 目标 |
|------|------|------|
| L1 | 焦点按钮 | L2 |
| L2 | 焦点按钮 | L3(asia) |
| L3(asia) | 焦点按钮 | L3(europe) |
| L3(europe) | 焦点按钮 | L3(north_america) |
| L3(north_america) | 焦点按钮 | L1 |
| L4 | 焦点按钮 | L2 |
| 任意 | 点击节点 | L4（透传 continent） |
| L4 | 空白/Esc | L3（有 continent）或 L2 |
| L3 | 空白/Esc | L2 |
| L2 | 空白/Esc | L1 |

核心函数：`setFocusLevel(level, opts)` 计算目标 viewBox 并 `animateView()`；`cycleFocusButton()` 执行循环；`backFocusLevel()` 退回上一级；`updateFocusIndicator()` 更新 pill 文字。

`computeBBoxFor(nodeList)` 从现有 `focusOnNodes` 逻辑抽取，返回 `{x,y,w,h}`。

### 5. JS 节点渲染重构 (`renderNodes`)

- 移除 pulse circle 创建和 `filter:'url(#glow)'`
- **已 peer (count>0)**：内圈实心 circle（`fill=color`）+ 外圈 ring（`fill=none stroke=color r=size+3`）
- **未 peer (count=0)**：空心 circle（`fill=none stroke=#64748b`）
- **离线**：空心 circle（`fill=none stroke=#475569 opacity=0.5`）
- 事件绑定仅挂到主 circle

### 6. JS 交互重构

- `onNodeClick`：调用 `setFocusLevel('L4', {nodeId, continent: focusState.continent})`
- `deselectNode`：末尾调用 `backFocusLevel()`
- `onNodeHover`/`showNodeDetail`：用 `getPeerColor(count)` 替代 class 查表
- 焦点按钮：调用 `cycleFocusButton()`
- 删除 jitter 按钮监听和 `startJitter`/`stopJitter`/`applyJitter`
- 删除 `animatePulses` 及其 rAF 调用
- 初始加载：`setFocusLevel('L2')`（首屏展示全部节点）
- resize：按 `focusState.level` 分发重新计算

### 7. 删除清单

| 函数/变量 | 原因 |
|-----------|------|
| `getPeerClass`, `getPeerLabel`, 旧`getPeerColor` | 被 HSL 渐变替代 |
| `animatePulses` | 移除光圈动画 |
| `applyJitter`, `startJitter`, `stopJitter`, `jitterInterval`, `jitterActive` | 移除连线闪动 |
| `pulsesGroup` | 不再使用 |
| `isFocused` | 被 `focusState` 替代 |
| `setFocusState` | 被 `updateFocusIndicator` 替代 |

## 验证步骤

1. 首屏加载看到全部节点（L2），焦点按钮指示器显示"全部节点"
2. 点击焦点按钮：L2→L3(亚洲)→L3(欧洲)→L3(北美)→L1(世界)→L2 循环
3. 点击任意节点：进入 L4，打开详情面板，高亮链路，指示器显示节点名
4. 按 Esc 或点击空白：从 L4 退回 L3（若从 L3 进入）或 L2
5. 已 peer 节点为实心圆+外环，颜色随 peer 数量从绿→黄→红渐变
6. 未 peer 节点为空心灰圆，视觉上明显区分
7. 无光圈放大动画，无连线闪动
8. 图例显示渐变条 + "无 Peer" 空心圆
9. 节点大小随 peer 数量变化（4-14px 半径）
10. 窗口缩放后视图自动重新计算
