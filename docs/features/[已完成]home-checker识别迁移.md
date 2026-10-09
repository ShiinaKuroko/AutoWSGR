# [任务书] home checker 识别迁移（第二批 · v5 · 设计定稿待执行）

> 状态：**设计已定稿，待批准执行**（2026-10-10）
> Task ID：`20260913-shiinaskuya-upgrade-7b3e`｜分支：`codex/20260913-shiinaskuya-upgrade-7b3e`
> 关联：`[规范]architecture-document.md`｜`[规范]python-code-style.md`｜`[规范]ui-controller-code-style.md`｜
> `[规范]dispatch-context临时规范.md`｜样板：`[架构]application-ui-navigation-event-checker.md`

## 0. 本批范围

**做**：把主页**识别**（主页模板识别 + 每日浮窗识别）从 UI 控制器物理迁移到导航器的
`page_checker/home_checker/`，拆清识别与点击边界。

**不做（下一批再议）**：主页导航流程、浮窗处理流程与它们的编排；模板中心点击（固定坐标与模板
匹配的关联问题单独讨论）。

## 1. 现状盘点（已核实）

| 位置 | 内容 | 性质 |
| --- | --- | --- |
| `page_checker/home.py`（62 行） | `check_home_page`＝截图 + 调控制器清浮窗 + 主页模板匹配 | 识别混编排 |
| `controller/home/main_page/recognition.py` | 浮窗模型与解析、模板文件名、`load_template`、`read_*_match`、`read_overlay`、`match_center`、红点识别 | 识别放在控制器（含坏引用 `vision.opencv`） |
| `controller/home/main_page/constants.py` | 5 个浮窗 ROI + `NAV_POSITIONS` 等点击坐标 | 识别与点击混放 |
| `controller/home/main_page/operations.py` | 5 个原子点击 | 点击（保留） |
| `controller/home/main_page/page.py`、`workflow.py` | 浮窗主流程与子流程 | 流程（本批不动） |

## 2. 浮窗识别模板与识别点（本轮盘点）

| 浮窗 | 识别点 | 模板 | ROI |
| --- | --- | --- | --- |
| 每日公告 | 公告浮窗在不在 | `HOME_NEWS_TEXT_720P.png` | `NEWS_TEXT_ROI` 0.0867,0.8764,0.2125,0.9403 |
| 每日公告 | 勾选框已勾选 | `HOME_NEWS_CHECKBOX_CHECKED_720P.png` | `NEWS_CHECKBOX_ROI` 0.0383,0.8653,0.0875,0.9458 |
| 每日公告 | 勾选框未勾选 | `HOME_NEWS_CHECKBOX_UNCHECKED_720P.png` | 同上 |
| 每日奖励 | 奖励浮窗在不在 | `HOME_REWARD_TEXT_720P.png` | `REWARD_TEXT_ROI` 0.1016,0.2681,0.3313,0.3361 |
| 每日奖励 | 领奖按钮在不在 | `HOME_REWARD_CLAIM_BUTTON_720P.png` | `REWARD_CLAIM_BUTTON_ROI` 0.4406,0.6292,0.5594,0.7028 |
| 奖励确认 | 确认浮窗在不在 | `HOME_REWARD_CONFIRM_BUTTON_720P.png` | `REWARD_CONFIRM_BUTTON_ROI` 0.4352,0.5194,0.5695,0.6208 |

不迁移：`LEGACY_*` 7 个旧模板（历史遗物，另行清理）；红点识别（用户决定留在 UI 控制器）。

## 3. 目标结构

```text
# 识别（导航器）
autowsgr/application/ui/navigation/page_checker/home_checker/
├── __init__.py        # 模块入口：导出识别入口与浮窗事实模型
├── checker.py         # 识别入口：check_home_page / check_home_news_overlay /
│                      #          check_home_reward_overlay / check_home_reward_confirm
├── recognition.py     # 模板匹配与结果解析，垂直调用 common.vision
└── constants.py       # 识别模板路径 + 识别 ROI

# 点击（UI 控制器）
autowsgr/application/ui/controller/home/main_page/
├── operations.py      # 点击方法，垂直调用 common.system
├── constants.py       # 点击坐标（NAV_POSITIONS 等）
└── recognition.py     # 仅保留红点识别（用户决定）
```

依赖方向：`导航器 → home_checker → recognition → constants / common.vision`；
`导航器 → controller.operations → common.system`。控制器不得反向依赖导航器。

## 4. 识别入口草案

| 入口 | 识别点 | 模板 | 语义 |
| --- | --- | --- | --- |
| `check_home_page(ctx)` | 主页模板 | `HOME_MAIN_720P.png` | 只看主页模板；浮窗态返回 False（用户要求"必须先识别浮窗，再识别首页"） |
| `check_home_news_overlay(ctx)` | 公告浮窗 + 勾选框 | `NEWS_TEXT` + `CHECKED` / `UNCHECKED` | 前识别；一次识别多个模板 |
| `check_home_reward_overlay(ctx)` | 奖励浮窗 + 领奖按钮 | `REWARD_TEXT` + `REWARD_CLAIM` | 前识别 |
| `check_home_reward_confirm(ctx)` | 确认浮窗 | `CONFIRM` | 前识别 |

四个入口都使用前识别（重试到命中），不用单帧探测；等待与顺序由导航器流程层编排（不在本批）。

## 5. 迁移映射

| 现在 | 去哪 |
| --- | --- |
| `main_page/recognition.py` 的浮窗模型与解析 | `home_checker/recognition.py` |
| `main_page/recognition.py` 的红点识别 | 留 `main_page/recognition.py` |
| `main_page/recognition.py` 的模板文件名常量 | `home_checker/constants.py` |
| `main_page/constants.py` 的 5 个浮窗 ROI | `home_checker/constants.py` |
| `main_page/constants.py` 的点击坐标 | 控制器 `constants.py`（不动） |
| `main_page/operations.py` | 控制器（不动） |
| `page_checker/home.py` | 拆入 `home_checker/checker.py` + `home_checker/constants.py`，原文件删除 |
| 6 个浮窗模板 + 主页模板 | `resources/image/application/ui/navigation/page_checker/home/`（小写目录） |

## 6. 本批之后的状态（阵痛期）

浮窗流程与导航流程暂时失效（用户已确认可接受）；最终按流程联调修复。
受影响调用方只登记不改：`route_manage/registry.py`、`runtime/initialize/*`、
`testing/ui/page_checker/test_home_page_checker.py`、E2E `cases/screenshot.py`。

## 7. 验证方案

- **focused 单测**：四个识别入口的命中/未命中；合成数据 + 替身，不依赖外挂图。
- **静态帧验证**：外挂样本在 `C:\ShiinaKuroko\01.Project\debug\nav\静态模板\`：
  `首页/`（主页样本）、`每日公告浮窗-勾选.png`、`每日奖励浮窗1.png`、`每日奖励浮窗2.png`、
  `每日奖励确认浮窗.png`、`每日浮窗文字.png`。
  缺口：**没有"公告未勾选"样本**，未勾选分支只能靠单测覆盖。
- 本批不跑全量 pytest / pre-commit（worktree 规则）。

## 8. 已确认结论（用户逐条答复）

| # | 结论 |
| --- | --- |
| 1 | 先做**物理迁移**、拆清边界，之后再微调 |
| 2 | `check_home_page` **只负责识别是否在主页** |
| 3 | 按**浮窗维度**出识别入口：`check_home_news_overlay` / `check_home_reward_overlay` / `check_home_reward_confirm` |
| 4 | 识别入口使用**前识别**；顺序为"先识别每日浮窗，再识别是否在首页"，顺序编排属导航器（本批不管） |
| 5 | 命名按第 3 条 |
| 6 | 红点通知识别**留在 UI 控制器**（导航器只负责页面到页面） |
| 7 | 浮窗态**不算在主页**：必须识别到主页模板，且先识别浮窗再识别首页 |
| 8 | 静态样本目录：`debug/nav/静态模板/` |
| 9 | 模板中心点击（固定坐标与模板匹配的关联）**本批不引入**，单独深入讨论 |
| 10 | 包名 `home_checker`；模板目录小写 `home/`；架构说明等验收通过后再补 |
| 11 | 公告勾选状态**在同一个 def 里产出**（不单独加 checkbox 入口） |
| 12 | 返回事实**先不含坐标** |
| 13 | 奖励浮窗：**奖励文字命中或领奖按钮命中**即算在（OR） |
| 14 | 重试参数统一固定；出现特殊场景时再为该入口单独加覆盖参数 |
| 15 | "公告未勾选"截图已补 |
| 16 | `LEGACY_*` 7 个旧模板**本批删除** |
| 17 | 中心坐标不统一产出，只对确有用处的模板特殊处理（换船模块会用到）；需要时用户会点名 |
| 18 | 奖励浮窗、确认浮窗**只返回存不存在**；公告浮窗返回"在不在 + 勾选状态" |
| 19 | 确认浮窗叠加时奖励浮窗**仍算在**（各自独立报事实）；实际顺序是"识别奖励→点→识别确认→点→再识别奖励"，顺序属流程层 |
| 20 | `calibration` 的用法**参考 event checker**（保持现有形态，home 复用同一加载入口） |
| 21 | **命名规范：目录小写、模板文件名全大写**（`home/` + `HOME_MAIN_720P.png`） |
| 22 | E2E 工具（是否加 `home_check` 静态 case）由我决定：加 |
| 23 | 公告事实字段：`matched` + `checked: bool \| None` |
| 24 | 红点识别先不管（保持现状，包括它引用的旧 API 已失效） |
| 25 | 主页模板与 ROI 原样继承（GPT 遗产，值不改，只换目录） |
| 26 | 旧文件处理三条一起做：删 `page_checker/home.py`、`HOME/` 并入 `home/`、删 7 张 `LEGACY_*` |

## 9. 执行时由我自定的实现细节（设计已定，以下不阻塞执行）

1. `match_center`（从匹配结果算点击中心）迁入 `home_checker/recognition.py` 保留能力，
   但**不作为本批识别出口**（本批不产出坐标）；
2. 旧的 `read_overlay`（单帧读浮窗）**删除**，由三个浮窗入口取代；
3. 旧测试 `testing/ui/page_checker/test_home_page_checker.py` 改为验证新包的四个入口
   （不再测试已删除的 `page_checker/home.py`）；
4. E2E：新增 `cases/home_check.py`（样本走 `debug/nav/静态模板/首页/`）；同时把
   `cases/event_check.py` 的样本路径改到 `debug/nav/静态模板/推图活动/`（用户已重整目录）；
5. 架构说明等本批验收通过后再补（用户第 8 条）。

## 10. 变更记录

| 日期 | 变更 |
| --- | --- |
| 2026-10-10 | v1 起草：范围限定识别迁移，列 8 条待确认 |
| 2026-10-10 | v2：记录用户 10 条结论；盘点 6 个模板与 5 个 ROI；把识别入口定为四个；更新待确认 6 条 |
| 2026-10-10 | v5：记录第 23–26 条结论；待确认清零，把 5 条实现细节登记为"执行时自定"；状态改为设计定稿待执行 |
| 2026-10-10 | v4：记录用户第 18–22 条结论（奖励/确认只报存在、浮窗叠加各自独立、calibration 参考 event、目录小写+文件名全大写、E2E 由我定）；待确认收敛到 4 条 |
| 2026-10-10 | v3：记录用户第 11–17 条结论（同 def 产勾选、先不含坐标、奖励 OR、重试固定、样本补齐、删 LEGACY、中心坐标特殊处理）；更新待确认 5 条 |
