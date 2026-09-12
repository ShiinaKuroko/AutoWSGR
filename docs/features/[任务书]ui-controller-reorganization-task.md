# UI Controller 代码重组任务书

日期：2026-09-06
范围：`AutoWSGR/autowsgr/application/ui/pages` 及其生产、测试、工具调用方。
`application/ui/navigation` 本轮冻结，只允许同步页面迁移产生的导入路径。

## 一、任务目标

只整理页面操作代码，把：

```text
autowsgr/application/ui/pages/
```

重组为：

```text
autowsgr/application/ui/controller/
```

这不是单纯改目录名。迁移时要同步调整页面代码的归属、公开入口、内部依赖、common
下沉和所有调用方，让业务代码真正使用 `controller`，不再依赖旧的 `pages` 路径。

## 二、职责边界

### 1. navigation：本轮冻结

保留现有 `application/ui/navigation` 的全部实现和行为：

- 跨页面寻路。
- 页面识别注册和页面栈。
- 公共、战斗、后勤导航图。

页面迁移后，navigation 只更新指向 Controller 新路径的 import；不得修改导航算法、
导航边集合或导航行为。

### 2. controller：页面操作层

Controller 负责已经进入页面后的页面内操作：

- 判断截图是否为当前页面。
- 点击按钮、标签、浮层和面板。
- 读取页面状态。
- 组合页面内的点击、等待、识别和校验。
- 向业务层提供有页面语义的 Controller 方法。

Controller 不负责任务队列、优先级、业务生命周期、跨任务调度或完整业务任务编排。

### 3. common 下沉和 shared Controller 能力

以下代码虽然当前位于 `pages`，但不是单一页面私有实现：

- `tabbed_page.py`：多个标签页面共用的页面识别能力。
- `choose_ship.py`：通用选船页面操作。
- `battle_preparation/fleet_change/`：普通、活动、演习、战役、决战共用的编队操作。

坐标、颜色、像素签名、OCR 区域、模板加载和纯设备操作等没有页面语义的代码必须下沉
到 `common`；页面状态、页面名称和页面流程留在 Controller。共享页面能力可以放在
`controller/shared/`，也可以保留在某个 Controller 包中，但必须记录依赖理由；不得只
为了目录对称增加空转发层。

### 4. common

继续提供无页面业务语义的底层能力：

- 设备截图、点击、滑动。
- OCR、模板匹配、像素匹配。
- 坐标、颜色、签名和 OCR 校准数据。
- 通用等待、异常和日志。

Controller 可以调用 common；common 不得反向引用 Controller。

## 三、目标目录和迁移策略

### 1. 页面 Controller 归属

以下页面保持独立 Controller，并迁入 `application/ui/controller/`：

```text
backyard_page.py
build_page.py
canteen_page.py
friend_page.py
intensify_page.py
sidebar_page.py
start_screen.py
main_page/
map/
bath_page/
battle_preparation/
decisive/
event/
mission_page/
```

页面包的 `__init__.py` 只导出该页面明确的 Controller 和页面契约，不执行注册或隐式副作用。

### 2. 共享能力处理

先根据真实 import 图确认 `tabbed_page.py`、`choose_ship.py` 和 `fleet_change/` 的共享关系，
再决定是否放入：

```text
application/ui/controller/shared/
```

如果共享模块依赖某个页面的基础状态，必须先拆出无页面语义的依赖或保留在页面 Controller
内部，并在 `findings.md` 说明原因。

### 3. 旧路径处理

- 新代码、测试、工具和文档全部切换到 `application.ui.controller`。
- 不保留 `application.ui.pages` 兼容转发包。
- 旧兼容壳只有在仍有真实消费者且本任务无法安全移除时才能保留，并必须记录消费者。
- 不恢复用户未暂存删除的文档和其他独立修改。

## 四、执行阶段

### 阶段 0：任务书和基线

- [x] 创建本独立任务书。
- [x] 重读任务书，确认 navigation 冻结。
- [x] 记录 backend/meta 当前 Git 状态和用户未暂存修改。

完成本阶段后重新读取本任务书，再进入阶段 1。

### 阶段 1：代码依赖盘点

- [x] 统计 `pages` 的全部文件、Controller、Mixin、数据、识别和兼容模块。
- [x] 找出生产、测试、工具和文档中的 `application.ui.pages` 引用。
- [x] 画出页面 Controller、共享能力和 common 的实际依赖方向。
- [x] 标出会形成循环依赖的模块。

完成本阶段后重新读取本任务书，并把发现写入 meta `findings.md`。

### 阶段 2：建立 Controller 代码入口

- [x] 创建 `application/ui/controller/` 包和公开入口。
- [x] 将页面代码迁入 Controller 归属，保持页面行为不变。
- [x] 按真实依赖把无页面语义代码下沉到 common，处理标签页、选船和编队共享能力。
- [x] navigation 只更新因路径迁移产生的导入路径，不改 navigation 实现。
- [x] 删除旧 `pages` 目录，不建立旧路径兼容包。

完成本阶段后重新读取本任务书，确认 navigation 仍未被改动。

### 阶段 3：修正真实调用方

- [x] 更新 business、application、server、testing、tools、examples 的导入路径。
- [x] 更新动态导入、patch 目标、测试断言和文档链接中的旧路径。
- [x] 搜索确认生产代码、测试和工具没有残留 `application.ui.pages`。
- [x] 确认 Controller 不反向引用 business、dispatch 或 server。

完成本阶段后重新读取本任务书，再运行 canonical import smoke。

### 阶段 4：代码治理和 Ponytail 审查

- [x] 页面 Controller 的公开方法按页面职责组织。
- [x] 将应归 common 的校准、视觉和设备实现从 pages 中下沉，并更新所有消费者。
- [x] 共享能力不再伪装成单一页面私有实现，或记录明确保留理由。
- [x] 删除没有真实消费者的页面兼容导出和旧路径说明。
- [x] 注释使用业务语言，说明调用方、职责和依赖路径。
- [x] 用 Ponytail 审查新增目录、包装层和抽象；没有真实消费者的代码不保留。
- [x] 遵守 Ruff/pre-commit 的空行和格式规则。

完成本阶段后重新读取本任务书，并记录剩余兼容项。

### 阶段 5：验证和报告

- [x] 运行 Controller、navigation 和受影响页面 focused pytest。
- [x] 运行 compileall、canonical import smoke 和 `git diff --check`。
- [x] 运行受影响文件的 pre-commit，不运行无关的全量测试。
- [x] 检查 Git diff 不包含 navigation 实现变更。
- [x] 写独立报告，列出目录变化、依赖变化、common 下沉、验证结果和未完成项。

完成本阶段后重新读取本任务书，确认所有复选项和报告一致。

## 五、禁止事项

- 不修改 `application/ui/navigation` 的实现。
- 不把页面语义操作下沉到 common。
- 不创建万能 `UIService.execute()` 或字符串分发器。
- 不为了目录对称复制代码或增加纯转发层。
- 不修改业务规则、任务契约和 GUI API。
- 不恢复或覆盖用户现有未暂存修改。
- 不在静态验证前执行实机 E2E。

## 六、验收标准

1. `application/ui` 保留 `navigation/`，页面操作统一归入 `controller/`。
2. 页面业务操作从 `application.ui.controller` 的真实 Controller 代码进入。
3. `application/ui/navigation` 的实现和行为没有被修改，只允许路径同步。
4. 应下沉的无页面语义代码已经进入 `common`，其余页面编排留在 Controller。
5. 旧 `application.ui.pages` 路径不再被生产代码、测试和工具使用。
6. 受影响 focused 测试和格式门禁通过。
7. 交付报告与本任务书逐项一致。

## 七、变更记录

- 2026-09-06：创建任务书。
- 2026-09-06：根据用户修正，明确 navigation 本轮冻结，只调整 pages 到 controller，并加入 common 下沉和 Ponytail 审查。
