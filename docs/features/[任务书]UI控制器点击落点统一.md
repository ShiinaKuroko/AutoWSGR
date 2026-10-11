# [任务书] UI 控制器点击落点统一（识别中心 + 静态兜底）

> 状态：**已完成**（2026-10-11，提交 `15acbf9`；模板中心已下沉到 `common.vision.expect_template_center`）
> Task ID：`20260913-shiinaskuya-upgrade-7b3e`｜分支：`codex/20260913-shiinaskuya-upgrade-7b3e`
> 关联：`[规范]ui-controller-code-style.md`｜`[规范]python-code-style.md`

## 0. 口径（用户 2026-10-11 定稿）

| 范围 | 规则 |
| --- | --- |
| 活动页 UI 控制器 | 有模板匹配的点击用识别中心；没有模板的用静态坐标；**不设兜底** |
| 其他页面 UI 控制器 | 有模板匹配的点击 = 识别中心 + 静态兜底（模板匹配失败仍能点） |
| 其他页面无模板 | 直接用静态坐标 |

## 1. 改动清单

### 1.1 活动页

| 入口 | 模板 | 改法 |
| --- | --- | --- |
| `EventPage.go_to_prepare` | `EVENT_SORTIE_PREPARE_720P` | 必传中心，删 `CLICK_SORTIE_PREPARE_FALLBACK` |
| `EventPage.switch_difficulty` | `EVENT_MODE_NORMAL/HARD` | 已必传中心，不动 |
| `EventPage.go_to_overlay` | 无（章节静态表） | 静态坐标 |
| `EventPage.click_overlay_close` / `go_back` | 无 | 静态坐标 |

### 1.2 其他页面

| 页面 | 入口 | 模板 | 静态兜底 |
| --- | --- | --- | --- |
| 主页 | `HomePage.click_news_checkbox` | `HOME_NEWS_CHECKBOX_*_720P` | `OVERLAY_POSITIONS[news_checkbox]` |
| 主页 | `HomePage.click_reward_claim` | `HOME_REWARD_CLAIM_BUTTON_720P` | `OVERLAY_POSITIONS[reward_claim]` |
| 主页 | `HomePage.click_reward_confirm` | `HOME_REWARD_CONFIRM_BUTTON_720P` | `OVERLAY_POSITIONS[reward_confirm]` |
| 登录页 | `LoginPage.click_enter_game` | `LOGIN_ENTER_BUTTON_720P` | `CLICK_ENTER_GAME` |
| 登录页 | `LoginPage.click_switch_entry` | `SERVER_SWITCH_ENTRY_720P` | `CLICK_SWITCH_ENTRY` |
| 出征页 | `SortiePage.go_to` | 五个标签模板 | `TAB_POSITIONS[tab]`（已有） |

无模板、保持静态：主页 `go_to` 五个入口、主页 `click_news_close`、登录 `click_server`（OCR 序号）、出征 `go_back`。

## 2. checker 侧新增读中心入口

中心取自 `TemplateMatchResult.center`（命中模板的归一化中心）；未命中返回 None，由控制器用静态兜底。

| checker | 新增入口 |
| --- | --- |
| `home_checker` | `read_news_checkbox_center` / `read_reward_claim_center` / `read_reward_confirm_center` |
| `login_checker` | `read_enter_button_center` / `read_switch_entry_center` |
| `sortie_checker` | `read_tab_center` |
| `stage_push` | `read_sortie_prepare_center` |

## 3. 验收

- focused 单测覆盖：传中心点中心、不传点静态兜底、活动页必传中心；
- 公开入口 import smoke；
- scoped `pre-commit` 与 `git diff --check`。
