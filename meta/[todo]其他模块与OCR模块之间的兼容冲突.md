# 其他模块与 OCR 模块之间的兼容冲突

状态：`TODO`，暂不进入 OCR 模块优化；待 OCR 专题统一处理。

所属任务：`20260830-sakuya-exercise-consolidated-7a6c`

## 当前结论

当前页面和选船功能依赖现有 OCR 实现，暂时保持运行行为不变。本台账只
记录兼容边界，不在本阶段新增公共接口、复制匹配算法或调整 OCR 生命周期。

## 已发现的冲突

OCR 模块中的 `_fuzzy_match()` 是下划线私有函数，但多个外部模块直接导入
并调用它。当前 OCR 公共导出没有提供“将已经得到的原始 OCR 文本匹配为标准
舰名”的等价接口。

直接调用方：

- `autowsgr/application/ui/controller/bath_page/recognition.py:32,204`
- `autowsgr/common/vision/ship_list.py:24,157`
- `autowsgr/application/ui/controller/shared/choose_ship.py:29,558`
- `autowsgr/application/ui/controller/battle_preparation/fleet_change/_detect.py:115,160,257`

实现位置：

- `autowsgr/common/vision/ocr.py:632`：`_fuzzy_match()` 实现。
- `autowsgr/common/vision/ocr.py:257`：公开的
  `OCREngine.recognize_ship_name()`。
- `autowsgr/common/vision/ocr.py:304`：公开的
  `OCREngine.recognize_ship_names()`。
- `autowsgr/common/vision/__init__.py`：公开 OCR 导出列表，不包含
  `_fuzzy_match()`。

## 为什么不能现在直接替换

`recognize_ship_name()` 和 `recognize_ship_names()` 接收图片，会重新执行
OCR；BathPage 和选船流程已经拿到了带坐标的 `OCRResult`，需要对其中的原始
文本做匹配，不能直接换成这两个公开方法。

`_fuzzy_match()` 当前还承载以下行为，替换时必须保持一致：

- 标准舰名和用户别名展开；
- OCR 文本规范化与自定义后缀处理；
- 编辑距离阈值；
- 最近候选并列时拒绝猜测；
- 单字、短文本和长舰名片段的特殊规则。

如果 OCR 专题只改名、移动或删除该私有函数，以上 4 个直接调用方都会受
影响；只修 BathPage 会留下同样的兼容冲突。

## 后续专题范围

进入 OCR 专题时，先统一决定以下事项：

1. 是否提供公开的原始文本匹配函数，例如接收
   `text`、候选舰名和阈值并返回唯一安全匹配。
2. 公共函数放在 `common.vision` 的哪个边界，并由谁负责别名展开和规范化。
3. 4 个调用方是否全部迁移，避免公共 API 与私有 API 并存。
4. 如何覆盖当前匹配规则，尤其是别名、歧义、短文本和自定义后缀。

## 本阶段处理边界

- 不修改 `_fuzzy_match()`。
- 不在 `bath_page` 或其他调用方复制一套模糊匹配实现。
- 不将图片级 OCR API 强行用于已经完成 OCR 的文本结果。
- 不因本台账创建新的兼容层或 fallback。

## 2026-09-07 UI Controller 样板审查

- 本批三个目标页面没有新增 OCR 调用方，现有 `_fuzzy_match()` 兼容冲突保持
  原样，延期到 OCR 专题统一处理。

## 2026-09-08 Home Page 审查

- `home` 没有页面专属 OCR 规则，也没有新增 OCR 调用方；本次未发现新的
  OCR 兼容冲突，既有跨模块私有 API 问题继续留待 OCR 专题统一处理。

## 2026-09-08 出征模块治理审查

- 选船检测 `battle_preparation/fleet_change/_detect.py` 继续直接调用
  `common.vision.ocr._fuzzy_match`；它与 `shared/choose_ship.py`、
  `common/vision/ship_list.py` 和浴室识别共同依赖同一个私有文本匹配实现。
- `decisive_page/recognition.py` 已集中决战章节、节点、战备舰队和技能舰船 OCR；其
  仍依赖上下文注入的 OCR 引擎、共享 `common.vision.ship_list` 和地图 DLL。
- 本批只完成职责归位，不优化 OCR 算法、不替换共享私有匹配实现，也不改变选船行为；
  后续上下文/OCR 专题继续处理生命周期和跨模块兼容。
- OCR 专题需要一次性决定原始 OCR 文本匹配的公开边界，并覆盖选船、决战、地图和
  浴室全部调用方；本批只记录兼容冲突，保留现有行为。

## 2026-09-09 决战模块第二轮治理

- `decisive_page/recognition.py` 已按职责集中决战 OCR；仍依赖注入的 OCR 引擎、
  `common.vision.ship_list` 和地图 DLL，未改变现有识别算法。
- `map_page.read_node()` 仍在 DLL 识别外围捕获宽泛 `Exception` 并按识别失败重试；
  这是 OCR/错误边界问题，留待专题处理。
- `common.vision.ocr._fuzzy_match` 的共享私有 API 依赖和选船模块兼容性继续保留，
  不在本轮改动。

## 2026-09-09 公共区域与登录阶段复核

- `LoginPage` 没有 OCR 文本识别；启动画面使用 `PixelSignature`，不新增 OCR 消费者。
- `shared/top_tabs.py` 只做顶部标签模板/像素匹配，不涉及 OCR；`shared/choose_ship.py`
  仍是 `_fuzzy_match` 的直接调用方，已由本台账的既有四方兼容清单覆盖。
- 本轮未修改 OCR 引擎、私有匹配函数、选船算法或 ROI 公共接口；相关冲突继续留待
  OCR 专题统一处理。

## 2026-09-09 阶段二 OCR/ROI 复核

- 通用 ROI、OCR 引擎、船池行定位和战斗结果识别均已有 `common.vision` 实现；本阶段
  没有重复迁移或新增兼容包装。
- `shared/choose_ship.py`、`battle_preparation/fleet_change/_detect.py` 和任务 OCR
  已改为导入整个 `common.vision.ocr` 模块访问私有函数，匹配行为保持不变。
- BathPage 和 `common/vision/ship_list.py` 仍直接导入 `_fuzzy_match`，任务 OCR 的
  其他私有匹配边界也继续保留；必须在同一 OCR 专题中统一公开接口并覆盖所有消费者。
- 决战节点 DLL 宽泛异常、页面 OCR 生命周期和选船 OCR/ROI 混合职责继续按台账延期，
  本阶段没有修改浴室代码、OCR 算法或公共视觉接口。
