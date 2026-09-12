# UI Controller 公共区域与登录阶段一报告

主任务：`20260830-autowsgr-upgrade`

日期：2026-09-09

分支：`codex/20260830-autowsgr-upgrade`

工作区：`C:\ShiinaKuroko\01.Project\AutoWSGR\.worktrees\20260830-autowsgr-upgrade`

## 1. 本阶段范围

本阶段按以下规范完成登录页面迁移和公共 Controller 能力盘点：

- `meta/[规范]ui-controller-code-style.md`
- `meta/[规范]navigation-code-style.md`

本阶段没有修改 `backyard/bath_page`，没有修改选船算法、导航状态机或业务流程。

## 2. 登录模块

- 原 `application/ui/controller/start_screen.py` 已迁移为
  `application/ui/controller/login/`，包含 `__init__.py`、`constants.py` 和
  `page.py`，没有空的 `recognition.py`。
- 页面控制器统一为 `LoginPage`，状态检查统一为 `check_current_page`，进入动作
  保留为 `click_enter`；生产运行时、初始化流程、文档和测试引用已同步。
- 启动画面点击坐标和像素签名已私有化到 `login/constants.py`，四位归一化坐标在
  1280x720 下保持原像素；旧 common 校准和 YAML 资源暂保为兼容事实。
- 启动画面只存在于游戏进入前，没有游戏内父页面，因此不提供业务意义上的
  `go_back`；启动流程负责进入后的页面确认。

## 3. 公共区域结论

当前 `controller/shared/` 保留两个独立出口：

- `top_tabs.py`：顶部标签模板/像素匹配、页面类型识别、激活标签读取和 checker
  工厂，消费者为地图、任务、建造、强化和好友页面。
- `choose_ship.py`：选船页面搜索、OCR 卡片定位、约束校验和单舰点击，消费者为
  普通、战役和决战编队分支。

没有新增地图导航包装或智能选船策略包装，原因如下：

- `battle_page/base.py` 已经是五个地图顶部标签共用的地图页面基类；普通出征和
  决战地图的状态、坐标、浮层和回退终态不同，抽到 shared 会隐藏页面契约。
- `ChooseShipPage` 只拥有选船页面 UI/视觉边界；编队规划、固定槽位、搜索开关和
  决战分支属于 `battle_preparation/fleet_change` 的业务/页面组合逻辑。
- 重复的 `read_active_panel`、`select_tab`、`go_back`、`change_fleet` 等入口均有
  不同状态类型或页面终态，未发现可安全合并的未知共享实现。

为两个公共子模块补充了 `__all__`，明确稳定导出；没有复制实现、第二套上下文或
跨业务隐藏状态。

## 4. 延后问题

- `shared/choose_ship.py` 和准备页编队检测共同依赖
  `common.vision.ocr._fuzzy_match` 私有 API，已记录在
  `meta/[todo]其他模块与OCR模块之间的兼容冲突.md`。
- `ChooseShipPage`、`BaseBattlePreparation` 和决战准备页对 `ctx.ocr`/`ctx.ship_ocr`
  的优先级与生命周期尚未统一，已记录在 `meta/[todo]上下文问题汇总.md`。
- 旧 common 校准入口暂不删除，待后续确认全部外部消费者和兼容契约后再处理。

## 5. 验证证据

- login/初始化 focused 测试：`11 passed`。
- 选船/准备页 focused 回归：`163 passed`。
- login 和 shared 导入 smoke、compileall、坐标/签名 parity、目标 pre-commit、
  `git diff --check`：通过。
- 未执行真实设备 E2E 和完整全量 pytest；当前 worktree 仍有其他既有未提交修改。
