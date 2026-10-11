# UI Controller 模块治理台账

本台账记录 UI Controller 模块的规范治理和用户验收状态。只有完成代码治理、专项验证并获得用户明确验收的模块，才能登记为“用户已验收”。

## 阶段划分

### 阶段一：已验收模块

以下 14 个模块已完成治理并通过用户验收，构成当前 UI Controller 治理的第一阶段：

- `autowsgr/application/ui/controller/operations/sortie_page/campaign_page`
- `autowsgr/application/ui/controller/operations/mission_page`
- `autowsgr/application/ui/controller/backyard/main_page`
- `autowsgr/application/ui/controller/backyard/canteen_page`
- `autowsgr/application/ui/controller/login`
- `autowsgr/application/ui/controller/sidebar/friend_page`
- `autowsgr/application/ui/controller/backyard/bath_page`
- `autowsgr/application/ui/controller/home/main_page`
- `autowsgr/application/ui/controller/sidebar/intensify_page`
- `autowsgr/application/ui/controller/sidebar/build_page`
- `autowsgr/application/ui/controller/operations/sortie_page/main_page`
- `autowsgr/application/ui/controller/operations/sortie_page/expedition_page`
- `autowsgr/application/ui/controller/sidebar/main_page`
- `autowsgr/application/ui/controller/operations/sortie_page/exercise_page`

### 后续阶段：暂缓治理

- `autowsgr/application/ui/controller/home/event_page`：暂缓治理，尚未验收。

| 模块 | 治理状态 | 用户验收 | 验收日期 | 验收依据 |
| --- | --- | --- | --- | --- |
| `autowsgr/application/ui/controller/operations/sortie_page/campaign_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；page.py 仅保留战役出征入口，recognition.py 负责难度、次数和统计事实，constants.py 仅保留页面动作坐标，未新增 operations.py/workflow.py；6 个 campaign_page focused tests 通过；compileall、import smoke、Code Graph、scoped pre-commit、`git diff --check` 通过。server/routes/game.py 的旧统计入口按范围暂未适配。|
| `autowsgr/application/ui/controller/operations/mission_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；page.py 直接编排任务面板切换、任务识别和奖励领取，workflow.py 已删除，operations.py 仅保留原子 UI 操作，recognition.py 聚合识别坐标和颜色阈值；compileall、Code Graph、scoped pre-commit、`git diff --check` 通过。focused pytest 因并行 `sortie_page` 导出迁移导致页面包导入阻塞，尚未执行。|
| `autowsgr/application/ui/controller/backyard/main_page` | 已成功治理 | 用户已验收 | 2026-09-14 | UI Controller/Python 规范；36 个专项测试通过；compileall、import smoke、Code Graph、scoped pre-commit、`git diff --check` 通过。 |
| `autowsgr/application/ui/controller/backyard/canteen_page` | 已成功治理 | 用户已验收 | 2026-09-14 | UI Controller/Python 规范；原子页面操作移入 `operations.py`，page 保留完整入口和页面回退；14 个 canteen/后院/导航回归测试通过；目标 pre-commit、compileall、import smoke、AST/public-method 检查和 `git diff --check` 通过。真实设备 E2E 因无连接设备未执行。 |
| `autowsgr/application/ui/controller/login` | 已成功治理（架构升级后重写） | 用户已验收 | 2026-10-11 | UI Controller/Python 规范；`constants.py` 只留进入游戏、换区入口与四个区服条目落点，`page.py` 三个单击入口收 `ctx`，删除 `recognition.py`/`calibration.py`/`data/`，识别全部归 `login_checker`；登录页与换区入口支持识别中心优先、固定落点兜底；8 项控制器单测通过，scoped pre-commit 与 `git diff --check` 通过；架构文档 `docs/AutoWSGR3.0/application/ui/controller/[架构]login.md` 已建。未验证项：实机点击链路（依赖启动流程）。 |
| `autowsgr/application/ui/controller/sidebar/friend_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；页面仅保留框架、识别和返回边界；7 个好友/侧边栏/导航回归测试通过；compileall、import smoke、Code Graph、scoped pre-commit、`git diff --check` 通过。后续好友业务功能待开发。 |
| `autowsgr/application/ui/controller/home/event_page` | 暂缓治理 | 未验收 | - | 活动地图存在活动专属布局、入口状态和运行时页面差异，待活动开启后结合真实页面行为重新评估 page/recognition/operations/workflow 边界、终态与日志；当前不纳入治理验收。 |
| `autowsgr/application/ui/controller/backyard/bath_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；`page.py` 保留单一 `repair` 入口，`workflow.py` 已移除，`operations.py` 仅保留原子 UI 操作，`recognition.py` 负责页面事实，常量和日志按规范归属；24 个浴室/后勤 focused tests 通过；compileall、import smoke、Code Graph、scoped pre-commit、`git diff --check` 通过。真实设备 E2E 未执行。 |
| `autowsgr/application/ui/controller/home/main_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；page 负责导航和有序浮层流程，recognition 负责事实，operations 负责内部浮层操作，`workflow.py` 已移除，重复导航包装已收缩；8 个主页面浮层测试通过；compileall、Code Graph、scoped pre-commit、`git diff --check` 通过。导航器契约仍需后续单独调整；真实设备 E2E 未执行。 |
| `autowsgr/application/ui/controller/sidebar/intensify_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；page 仅提供强化页面检查和返回侧边栏导航，强化业务保留明确 TODO，constants 仅保留返回坐标，INFO 日志统一使用中文业务字段和结果；3 个专项测试通过；compileall、import/public-surface smoke、scoped pre-commit、`git diff --check` 通过。真实设备 E2E 未执行，外部聚合 E2E 的旧标签调用暂不适配。 |
| `autowsgr/application/ui/controller/sidebar/build_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；page 仅提供建造和解体两个 workflow 入口，operations 负责 tab/原子操作，workflow 分离主流程与收取、新建子流程，开发/废弃保留明确 TODO，四级日志已按中文业务语义和终态规范治理；6 个专项测试、compileall、import smoke、scoped pre-commit、日志格式/级别断言和 `git diff --check` 通过。真实设备 E2E 未执行，业务层旧入口暂未适配。 |
| `autowsgr/application/ui/controller/operations/sortie_page/main_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；`data.py` 已合并进 `page.py`，page 负责页面壳/标签切换/回退，recognition 负责标签栏模板识别和页面事实，包入口仅导出页面类型；28 个地图页面测试通过；compileall、Code Graph、scoped pre-commit、`git diff --check` 通过。真实设备 E2E 未执行。 |
| `autowsgr/application/ui/controller/operations/sortie_page/expedition_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；`page.py` 持有唯一完整远征收取流程，`operations.py` 仅保留槽位和跳过结算原子点击，`recognition.py` 仅负责就绪槽位事实读取，`workflow.py` 已移除；远征页及相邻地图回归测试 32 个通过；compileall、import smoke、AST 边界检查、scoped pre-commit、`git diff --check` 通过。真实设备 E2E 未执行。 |
| `autowsgr/application/ui/controller/sidebar/main_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；`page.py` 保留单一 `navigate_to(target)` 入口和内部二级菜单分支，`go_back` 统一页面返回语义，`operations.py` 仅保留一级/二级菜单原子点击，`recognition.py` 负责页面事实，未新增 `workflow.py` 或目标专用 `go_to_*`；6 个专项测试通过；compileall、import/public smoke、AST 边界检查、fresh Code Graph build/check/explain、scoped pre-commit、`git diff --check` 通过。外部旧调用方暂未适配。 |
| `autowsgr/application/ui/controller/operations/sortie_page/exercise_page` | 已成功治理 | 用户已验收 | 2026-09-15 | UI Controller/Python 规范；`page.py` 保留对手状态读取和单一线性 `challenge_rival(rival_index, refresh_rival=...)` 流程，刷新作为参数控制的流程步骤，`operations.py` 仅保留点击/滑动原子操作，`recognition.py` 负责列表和挑战按钮事实，未新增 `workflow.py`，旧中间入口和未实现编队接口已移除；4 个专项测试通过；compileall、项目虚拟环境 import smoke、Code Graph build/check、scoped pre-commit、`git diff --check` 通过。业务层旧调用方暂未适配。 |
