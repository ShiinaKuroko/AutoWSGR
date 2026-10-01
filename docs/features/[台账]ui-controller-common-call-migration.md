# UI Controller common 调用迁移台账

状态：进行中
适用范围：`autowsgr/application/ui/controller`
建立日期：2026-09-20

## 迁移规则

- UI Controller 只能调用当前 common 架构文档中存在的公开入口。
- common 没有一对一能力时，不在 common 增加兼容方法、别名或旧类。
- 已有 application、business 所有者的类型和视觉资源，迁移到其真实所有者。
- `application/ui/navigation/interaction.py`、`application/vision/calibration` 等非 UI Controller 文件的残留问题只记录，不在本轮越界修改。
- 每次迁移都必须保留原业务语义；仅改变 import 所有者或使用当前公开入口的必要参数。

## 可直接迁移的调用

| 旧调用 | 当前入口 | 状态 | 说明 |
| --- | --- | --- | --- |
| `common.device.AndroidController` | `common.device.service.DeviceService` | 待迁移 | 设备服务保留 `click`、`swipe`、`long_tap`、`key_event`、`text`、`screenshot` 等语义入口。 |
| `common.device.interaction.*` | `application.ui.navigation.interaction.*` | 待迁移 | 这些是 UI 导航能力，不再属于 common/device。目标模块自身仍有旧 vision 依赖，暂记外部阻塞。 |
| `common.types.PageName` | `application.ui.navigation.types.PageName` | 待迁移 | 页面枚举归 navigation。 |
| `common.vision.PageMatch` | `application.ui.navigation.types.PageMatch` | 待迁移 | 页面识别结果归 navigation。 |
| `common.vision.resources.*` | `application.vision.resources.*` | 待迁移 | 页面、战斗和操作模板归 application vision。 |
| `common.vision.ocr_rules` | `application.vision.ocr_rules` | 待迁移 | OCR 业务规则归 application vision。 |
| `common.vision.combat/map/blood/ship_list/api_dll` | 对应 `application.vision.*` 模块 | 待迁移 | 这些是领域识别或 native 适配，不属于 common vision。 |
| `common.calibration.*` | `application.vision.calibration.*` | 待迁移 | 校准数据归 application vision；其内部旧依赖另行记录。 |
| `common.types.ShipDamageState` | `business.logistics.types.ShipDamageState` | 待迁移 | 维修/损伤状态归后勤领域。 |
| `common.types.FleetSelection/ShipType` | `business.combat.types` | 待迁移 | 战斗舰队领域类型归 business combat。 |
| `common.types.DecisiveEntryStatus/DecisivePhase` | `business.combat.decisive.types` | 待迁移 | 决战状态归决战业务。 |
| `common.fleet.FleetSlotRule/ShipSelector` | `business.combat.fleet_models` | 待迁移 | 编队规则和值对象归战斗业务。 |
| `common.system.logger.get_logger` | `common.system.logger.get_logger` | 可保留 | 符合 system 架构文档，通道由 UI 模块自行定义。 |

本轮已完成上述表中以下路径迁移：`DeviceService`、`application.ui.navigation.interaction`、
`application.ui.navigation.types.PageName`、application vision 资源和领域识别模块、
application vision calibration、business combat/logistics 类型以及舰队规则模型。

## 当前没有一对一入口的调用

| 旧调用 | 影响 | 处理决定 |
| --- | --- | --- |
| `ImageChecker.find_template/find_any/template_exists` | 旧 API 返回 `ImageMatchDetail`，当前 API 要求 `Template` 并返回 `TemplateMatchResult`。 | 不增加 `ImageChecker` 兼容层；按页面模块逐项改用 `vision.match_template`，无法在本轮明确转换的记录调用位置。 |
| `PixelChecker.get_pixel/check_signature` | 当前 common 只提供 `vision.numpy.sample_pixel` 和 `vision.match_pixels`，规则模型构造方式已变化。 | 不增加 `PixelChecker`；简单采样迁移到 `vision.numpy`，签名构造需页面模块自行适配。 |
| `OCREngine` / `common.vision.ocr.OCREngine` | 当前入口是 `vision.ocr`/`vision.recognize_text`，返回 `TextDetection` 列表，不再提供旧对象接口。 | 不创建单对象兼容层；依赖运行时 OCR 对象的页面先记录，待上层 OCR 契约统一后迁移。 |
| `ImageTemplate` | 当前模板模型定义在 `common.vision.adapters.template_matching.Template`，没有根门面重导出。 | 不恢复旧类；页面资源由 `application.vision.resources` 和 dispatch cache 统一提供。 |
| `common.system.exceptions.ActionFailedError` | 当前 system 只提供错误基类，没有该具体错误。 | 已归位：`application.errors.ActionFailedError`（继承 `ApplicationError`），调用方改新路径。 |
| `common.system.ManualRepairRequiredError` | 当前 system 架构没有该具体错误定义。 | 已归位：`application.errors.ManualRepairRequiredError`，由 application 修理工作流与 business 战斗共用。 |
| `Color.of/from_rgb_tuple`、`PixelRule.of`、`PixelSignature.from_dict`、`ROI.from_tuple` | 旧模型工厂方法已不存在，当前模型只保证构造器和数据类入口。 | 不在 common 增加兼容工厂；页面常量需由对应页面治理时逐项重写。 |

## 外部阻塞，不在本轮修改

| 模块 | 问题 | 原因 |
| --- | --- | --- |
| `application/ui/navigation/interaction.py` | 仍直接导入已删除的 `common.vision._template_matcher`，并使用旧 `ImageChecker`。 | 这是 navigation 模块自身的迁移任务，不为 UI Controller 适配而越界修改。 |
| `application/vision/calibration/*` | 校准加载器仍引用旧 `vision.Color.of`、`PixelSignature.from_dict` 等接口。 | 这是 application vision 校准任务，不由 UI Controller 迁移顺手修复。 |
| `application/vision/resources/*` | 部分资源声明仍依赖 dispatch/context 和旧路径契约。 | 这是 application vision/resources 与 dispatch 的并行治理范围。 |
| `application/vision/shipnames.py`、校准加载链 | 仍从 `common.system` 根包导入已下沉到 `system.files` 的 `load_yaml`，或依赖旧 vision 模型工厂。 | 这是 application vision/system 出口适配任务，不在 UI Controller 范围内修复。 |
| `application/ui/controller` 中依赖旧视觉对象的页面 | 调用语义不只是 import 替换，需要重新定义 ROI、模板和 OCR 结果边界。 | 记录调用位置后等待对应页面或 OCR 专项治理，避免伪造 common 能力。 |

当前仍可检索到的旧调用类别：

- `ImageChecker`、`PixelChecker`、`OCREngine`、`ImageTemplate`；
- `common.vision` 中混合导入上述旧对象的页面模块；
- `common.calibration.tabbed`，当前 application calibration 没有对应模块；
- `ActionFailedError`、`ManualRepairRequiredError` 与 system 根包中的 `TaskPaused`/`TaskStopped` 均已归位，见下节。

## 验收记录

本轮已完成明确所有者 import 路径迁移，并运行 UI controller import smoke：92 个模块中 13 个成功、79 个失败。失败均归入本台账的外部阻塞或无一对一入口，不代表 UI Controller 全部迁移完成。

每完成一组真实视觉/OCR/错误契约迁移，继续补充文件、入口和验证命令；所有未完成项在对应所有者治理前保持显式记录。

### 领域错误归属补齐（2026-10-01）

- `ActionFailedError`、`ManualRepairRequiredError` 归位到 `application/errors.py`；`TaskPaused`/`TaskStopped` 归位到 `application/signals.py`（任务控制信号，不属于错误树）；`DockFullError` 就地定义在 `business/combat/decisive/chapter.py`。
- 全部生产与测试调用方改新路径，异常基类由 `UIError` 改为 `ApplicationError`，构造参数与错误文本保持不变。
- 验证命令：`pytest testing/dispatch -q`。
