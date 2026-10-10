# [任务书] 出征页 checker + 识别入口改名（第三批）

> 状态：**已执行，待验收**（2026-10-10）
> Task ID：`20260913-shiinaskuya-upgrade-7b3e`｜分支：`codex/20260913-shiinaskuya-upgrade-7b3e`
> 关联：`[规范]python-code-style.md`（§6.5 坐标）｜`[规范]architecture-document.md`｜
> `[规范]dispatch-context临时规范.md`｜样板：`[架构]application-ui-navigation-event-checker.md`、`...-home-checker.md`

## 0. 本批范围（三件事，一次做完）

1. **识别入口改名**：`common.vision` 的六个入口从"前/后识别"改成**"识别存在 / 识别不存在"**语义；
2. **PageName 按语义调整**：出征 `MAP → SORTIE_MAP`，新增演习 / 远征 / 战役，决战沿用 `DECISIVE_BATTLE`；
3. **新建出征页 checker**：`page_checker/sortie_checker/`，五个 `check_XXX_page` 入口（识别 tab 激活）。

**不做**：UI 控制器那份坏的 tab 识别（之后单独修）、导航流程与路由编排、`navigation_old`（只读备份）。

## 1. 识别入口改名（用户已确认用 `expect`）

| 现在 | 新名 | 语义 |
| --- | --- | --- |
| `before_template` | `expect_template` | 前识别：重试直到目标**存在** |
| `before_ocr` | `expect_ocr` | 同上 |
| `before_pixels` | `expect_pixels` | 同上 |
| `after_template` | `expect_template_absent` | 后识别：重试直到目标**不存在** |
| `after_ocr` | `expect_ocr_absent` | 同上 |
| `after_pixels` | `expect_pixels_absent` | 同上 |

命名理由：点击后仍然要用"重试到出现/消失"的循环，用 before/after 描述时序会让人误以为是两个不同动作；
`expect_*` / `expect_*_absent` 直接表达"期望存在 / 期望不存在"。**不留旧别名**。

需要同步改的位置（已 grep 全量）：

| 位置 | 数量 |
| --- | --- |
| `common/vision/service.py`（定义）与 `common/vision/__init__.py`（门面） | 6 + 导出名单 |
| `page_checker/event_checker/normal/recognition.py` | 6 |
| `page_checker/home_checker/recognition.py` | 4 |
| `controller/home/main_page/page.py`、`workflow.py`（暂时失效的旧流程） | 7 |
| `testing/vision/test_recognition_flow.py`、`testing/common/vision/test_service.py` | 全量 |
| `testing/ui/page_checker/test_{event,home}_checker.py`（monkeypatch 名） | 3 |
| `docs/AutoWSGR-3.0/[架构]common-vision.md`（§2.4、§14 出口表） | 文档 |
| `page_checker/sortie.py` | 随本批删除而消失 |

## 2. PageName 调整

```text
MAP = '地图页面'            →  SORTIE_MAP = '出征页面'
新增  EXERCISE   = '演习页面'
新增  EXPEDITION = '远征页面'
新增  CAMPAIGN   = '战役页面'
沿用  DECISIVE_BATTLE = '决战页面'
```

态度：直接改名、不留别名。同步引用（活的代码与测试）：

- `route_manage/registry.py`（HOME ↔ 出征的两条边）；
- `business/`：`logistics/expedition.py`、`combat/exercise/executor.py`、`combat/bettle/normal_fight.py`、`combat/campaign/executor.py`；
- `controller/`：`home/main_page/page.py`、`fleet/main_page/page.py`、`operations/sortie_page/main_page/{page,recognition}.py`、`operations/sortie_page/expedition_page/page.py`；
- `server/routes/game.py`：现在是硬编码字符串 `'地图页面'`，改成使用枚举值，避免改名后静默失效；
- `tools/debug_toolkit/function/e2e_runner/cases/{map_navigation,decisive_stability}.py`；
- `testing/`：`ui/navigation/{test_service,test_registry}.py`、`business/system/initialize/test_initialize_unit.py`、`ui/{main_page,map_page}/e2e.py`（字符串形式）。

不动：`application/ui/navigation_old/*`（只读备份）、`application/runtime/context/game_context.py`（旧上下文，已跑不通）。

## 3. 出征页 checker

### 3.1 结构

```text
autowsgr/application/ui/navigation/page_checker/sortie_checker/
├── __init__.py        # 导出五个识别入口
├── checker.py         # 五个入口：check_sortie_page / check_exercise_page /
│                      #   check_expedition_page / check_campaign_page / check_decisive_page
├── recognition.py     # tab 激活识别（每个 tab 一次前识别）
└── constants.py       # 5 个 tab 的 ROI + 10 个模板路径
```

### 3.2 入口语义

五个入口各自判断"当前页面里某个 tab 是否被激活"，都使用 `expect_template`（前识别，重试到命中）：

| 入口 | 判定 | 对应 PageName |
| --- | --- | --- |
| `check_sortie_page(ctx)` | 出征 tab 激活 | `SORTIE_MAP` |
| `check_exercise_page(ctx)` | 演习 tab 激活 | `EXERCISE` |
| `check_expedition_page(ctx)` | 远征 tab 激活 | `EXPEDITION` |
| `check_campaign_page(ctx)` | 战役 tab 激活 | `CAMPAIGN` |
| `check_decisive_page(ctx)` | 决战 tab 激活 | `DECISIVE_BATTLE` |

第一次进入出征页默认落在"出征"tab，因此 `check_sortie_page` 同时承担"是否已到达出征页"的页面身份判断。

### 3.3 模板与 ROI

- 模板：10 个（5 个激活态 `SORTIE_<TAB>_TAB_720P.png` + 5 个未激活态 `..._INACTIVE_720P.png`），
  全部从 `debug/nav/sortie_page.main_page/` 入库到
  `resources/image/application/ui/navigation/page_checker/sortie/`（目录小写、文件名全大写）；
- ROI：使用 `SORTIE_TAB_ROI_REPORT.json` 的重新裁切值（不是旧代码里的旧值），按
  `[规范]python-code-style.md` §6.5 落成四位小数并保证**比模板大**（左/上向下、右/下向上取整）；
- 旧 `page_checker/SORTIE/` 目录（5 个模板）与旧 `page_checker/sortie.py` 一并删除。

### 3.4 tab 中心点击坐标（本批只记录）

五个 tab 的 ROI 中心是"切换 tab"的点击点，按分工**由 UI 控制器持有**（现有 `TAB_POSITIONS`）。
本批只把"ROI 中心 = 点击点"这个对应关系登记在任务书和架构文档里，控制器侧等流程批一起改。

## 4. 验证方案

- **focused 单测** `testing/ui/page_checker/test_sortie_checker.py`：五个入口的命中与未命中；
  合成数据 + 替身，不依赖外挂图；
- **静态帧 case** `cases/sortie_check.py`：用 `debug/nav/静态模板/出征/` 的 5 张整页样本
  （`出征页面.png`、`选择演习 tab.png` 等）验证五个入口各自命中对应 tab；
- **改名回归**：`testing/common/vision`、`testing/vision`、`testing/ui/page_checker`、
  `testing/dispatch/context`、`testing/tools` 全跑，确认改名没有断链；
- 换名后两个既有静态 case（`event_check`、`home_check`）仍必须全过。

## 5. 已确认结论

| # | 结论 |
| --- | --- |
| 1 | 需要**五个 check**：进入出征页默认在出征 tab，五个 checker 只判当前页面里各自 tab 的激活情况 |
| 2 | PageName **按语义独立**：出征从 `MAP` 变成 `SORTIE_MAP`，演习/远征/战役新增 |
| 3 | **10 个模板全部入库** |
| 4 | tab **中心点击坐标给 UI 控制器用**，本批先记着 |
| 5 | **UI 控制器的识别不管**，之后单独修 |
| 6 | 识别入口用 `expect`（存在 / 不存在），所有引用同步改 |
| 7 | 入口命名用 `check_XXX_page`；包名 `sortie_checker` |
| 8 | 旧 `sortie.py` 与旧模板不要了，由新包取代 |

## 6. 执行时由我自定的实现细节

1. 改名的机械替换用脚本做一次、再逐个文件核对 import 与 `__all__`，避免漏改；
2. `common-vision.md` 的 §2.4、§14.1 出口表同步改名（架构文档必须与代码一致）；
3. event / home 的架构文档若写到"前识别/后识别"措辞，一并改成"识别存在/不存在"；
4. `server/routes/game.py` 的硬编码页面字符串改用 `PageName` 枚举值；
5. 架构说明（sortie checker 那份）等本批验收通过后再补。

## 7. 执行结果（2026-10-10）

| 项 | 结果 |
| --- | --- |
| 识别入口改名 | 6 个入口全部改名；生产代码 + 测试 + `AGENTS.md` + `common-vision.md` + 活动设计稿同步，代码里已无旧名 |
| PageName | `MAP → SORTIE_MAP`，新增 `EXERCISE` / `EXPEDITION` / `CAMPAIGN`；18 个活文件同步（`navigation_old` 与旧 `game_context.py` 按计划不动） |
| sortie_checker 包 | 四个文件建成，五个 `check_XXX_page` 入口；旧 `page_checker/sortie.py` 与 `SORTIE/` 目录删除 |
| 模板 | 10 个（5 激活 + 5 未激活）入库到 `page_checker/sortie/`；ROI 用报告值换算成四位小数并外扩 |
| 测试 | `test_sortie_checker.py` 6 项（参数化覆盖五个标签 + 全未激活）；相关套件 46 passed |
| 静态帧 | `sortie_check` 10 步通过；`event_check` 8 步、`home_check` 12 步回归通过 |
| 包名对齐 | `event` → `event_checker`、`normal_checker` → `normal`（与 `home_checker`/`sortie_checker` 平级），模板资源同构改名，架构文档与示例同步 |
| 顺带 | 删掉 3 个测已删模块的旧测试（`test_home_overlay_flow` / `test_home_popup_samples` / `test_sortie_page`）与 `testing/ui/navigation/test_service.py` |

**已知不在本批范围**：`testing/ui` 下 23 个旧测试仍收集失败（引用 `navigation.interaction`、
`common.calibration`、`PixelChecker`、`common.types` 等已被删或已改名的旧 API），属既有破坏，非本批引入；
UI 控制器那份走 `common.calibration.tabbed` 的标签识别仍未修；tab 中心点击坐标尚未交给控制器。

## 8. 变更记录

| 日期 | 变更 |
| --- | --- |
| 2026-10-10 | 起草：三件事（识别入口改名、PageName 调整、sortie checker）；记录 8 条已确认结论与影响面清单 |
| 2026-10-10 | 执行完成：改名 + PageName + sortie_checker + 模板入库 + 单测 + 静态帧，46 passed、三个静态 case 全过；状态改"已执行，待验收" |
