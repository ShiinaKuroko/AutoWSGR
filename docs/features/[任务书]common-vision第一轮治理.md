# [任务书] common/vision 第一轮治理

Task Status: in_progress

Next Step: 等待用户验收；验收后再安排能力 parity 和上层联调。

## 1. 任务目标

将 `autowsgr/common/vision` 治理为只提供通用视觉基础能力的模块：

- 以 `from autowsgr.common import vision` 作为唯一公共入口；
- 以 `vision.XXX(...)` 提供稳定能力，不平铺旧类和旧模块；
- 保留图像数据模型、ROI、像素检查、模板匹配、OCR 后端和基础图像变换；
- 将页面、战斗、舰船、伤害等领域识别移出通用层；
- 将没有明确所有者的定义暂存到 `autowsgr/common/TEMP2/vision`；
- 第一轮不适配旧上层调用方，不增加兼容别名。

本轮只治理模块边界、定义归属和临时收容，不承诺完整业务链路已经迁移完成。

## 2. 用户原始要求

> @C:/ShiinaKuroko/01.Project/AutoWSGR/.worktrees/ShiinaSkuya-upgrade/autowsgr/common/vision 参考system模块的任务书，复制一份，变成治理vision模块的任务书，然后执行第一轮治理，不要的方法丢到temp2里去。

本任务书参考 `docs/features/[任务书]common-system第一轮治理.md` 的组织方式，
但只以本节用户要求和当前 vision 代码事实作为执行依据。

## 3. 执行范围

### 3.1 范围内

- `autowsgr/common/vision` 的 Python 定义、公共出口和私有后端；
- vision 私有模板、OCR 模型和图像资源定位；
- 从 vision 移出的领域识别和工具归属记录；
- `autowsgr/common/TEMP2/vision` 的临时收容内容；
- vision 专项导入、编译和静态边界检查。

### 3.2 范围外

- 不恢复旧的 `ImageChecker`、`PixelChecker`、`OCREngine` 公开导入路径；
- 不适配 application、business、server、testing 或 GUI 的旧调用方；
- 不把页面流程、设备截图、业务终态或任务调度放回 common/vision；
- 不在本轮重写领域识别算法，不新增兼容层、代理层或重复状态源；
- 不把临时收容区当成长期公共 API。

## 4. 目标公共契约

```python
from autowsgr.common import vision

vision.crop(image, roi)
vision.read(image, mode='text')
vision.match(image, template_or_rule)
vision.inspect(image, pixel_signature)
vision.sample(image, x, y)
vision.crop_rotated(image, bl_x, bl_y, tr_x, tr_y, angle)
vision.transform(image, operation)
```

| 入口 | 业务语义 | 返回值 |
| --- | --- | --- |
| `vision.crop` | 按 ROI 裁剪图像 | `ndarray` |
| `vision.read` | 读取文字并按模式规范化 | `ReadResult` |
| `vision.match` | 执行模板或图像规则匹配 | `ImageMatchResult` |
| `vision.inspect` | 检查像素签名 | `PixelMatchResult` |
| `vision.sample` | 读取一个相对坐标的 RGB 值 | `Color` |
| `vision.crop_rotated` | 裁剪并拉正旋转矩形 | `ndarray` |
| `vision.transform` | 执行受限基础图像变换 | `ndarray` |

公共入口只聚合稳定能力。`_ocr.py`、`_pixel_matcher.py`、
`_template_matcher.py`、`_opencv.py`、`_ocr_models.py` 和 `_resources/`
属于私有实现，不被上层直接依赖。

## 5. 第一轮定义分类

### 5.1 保留在 common/vision

| 位置 | 语义 |
| --- | --- |
| `image_template.py` | 图像模板、匹配规则和匹配结果数据模型 |
| `pixel.py` | RGB、像素规则、像素签名和结果数据模型 |
| `roi.py` | 与分辨率无关的 ROI 几何模型 |
| `_pixel_matcher.py` | 私有像素检测实现 |
| `_template_matcher.py` | 私有模板匹配实现 |
| `_ocr.py` | 私有 OCR 引擎和检测结果实现 |
| `_ocr_models.py` | 私有 OCR 模型准备与校验实现 |
| `_opencv.py` | 私有基础 OpenCV 变换实现 |
| `_resources/` | 私有模板和模型资源索引 |
| `__init__.py` | `vision.XXX` 公共门面 |

### 5.2 已移交明确所有者

| 原定义 | 第一轮落点 | 原因 |
| --- | --- | --- |
| 战斗、地图、伤害识别 | `autowsgr/application/vision` | 依赖业务状态或设备截图 |
| 舰船列表、舰名和 OCR 领域规则 | `autowsgr/application/vision` | 依赖舰船业务数据和业务容错策略 |
| 页面匹配结果 | `autowsgr/application/vision` | 页面语义属于 application/UI |
| EasyOCR 模型下载 CLI | `tools/vision` | 交互式工具不属于运行时基础层 |

### 5.3 暂无明确所有者，移入 temp2

本任务中的 `temp2` 固定指 `autowsgr/common/TEMP2/vision`，与
system 使用的 `autowsgr/common/TEMP` 分开。以下内容只保留供后续认领：

| 暂存模块 | 暂存定义 | 原因 |
| --- | --- | --- |
| `calibration_loader.py` | `_load`、`get` | 页面校准文件加载，不是视觉算法 |
| `colors.py` | `color`、`tolerance`、`param` | 领域颜色校准访问器 |
| `coordinates.py` | 坐标加载、解析、归一化和查询方法 | UI 坐标校准访问器 |
| `signatures.py` | `signature` | 页面/状态签名校准访问器 |
| `ocr.py` | `param` | 页面 OCR 参数校准访问器，和私有 OCR 后端同名易混淆 |

temp2 代码不得从 `common/vision/__init__.py` 导出，也不得为旧调用方增加别名。
后续由校准或具体 application 模块认领、重写或删除。

## 6. 第一轮执行阶段

### 阶段一：任务书和基线

- [x] 读取 system 任务书的目标、范围、阶段和验收结构；
- [x] 确认目标 Git 根目录、共享 worktree、分支和现有并行修改；
- [x] 记录 vision 当前文件、公共出口、资源和调用方基线；
- [x] 建立本任务书，状态保持 `in_progress`。

### 阶段二：定义打散与归属

- [x] 逐文件登记 vision 的类、函数、资源和直接依赖；
- [x] 区分通用视觉能力、领域识别、工具代码和校准访问器；
- [x] 维持通用核心的私有后端边界；
- [x] 将有明确所有者的领域实现移到 application/tools；
- [x] 将无明确所有者的校准包装移入 `common/TEMP2/vision`。

### 阶段三：第一轮静态门禁

- [x] 检查 `common/vision` 不再包含校准包装和领域识别入口；
- [x] 检查公共门面只导出目标 `vision.XXX` 能力和数据契约；
- [x] 运行 vision 核心的 compile/import/smoke 检查；
- [x] 运行受影响文件的 scoped pre-commit 和 `git diff --check`；
- [x] 记录旧上层导入未适配的明确范围，不以兼容别名掩盖迁移。

## 7. 依赖方向

```text
application / business / tools
              │
              ▼
       common.vision 公共门面
              │
              ▼
       私有匹配 / OCR / OpenCV / 资源
```

common/vision 可以依赖 `common.system.logger` 等程序级基础设施，但不得依赖
页面、设备、业务状态、业务配置或上层流程。校准访问器暂存于 temp2，不构成
vision 的正式依赖方向。

## 8. 验收标准

1. 本任务书包含用户原文、范围、目标契约、阶段和风险记录；
2. `common/vision` 的保留定义均有通用视觉语义；
3. 领域识别和工具代码不再作为 common/vision 的公共能力；
4. 无明确所有者的校准包装位于 `common/TEMP2/vision`；
5. `vision.XXX` 公共入口导入和最小行为 smoke 通过；
6. compile、scoped pre-commit、静态边界检查和 `git diff --check` 有记录；
7. 旧上层导入未适配范围被明确记录，不宣称全仓兼容；
8. 用户验收前不把本任务书状态改为 `done`。

## 9. 风险与后续

| 风险 | 处理 |
| --- | --- |
| 上层仍引用旧 vision 模块 | 本轮不适配，后续按新门面逐模块迁移 |
| OCR 领域规则与通用 OCR 后端边界变化 | 由 application vision 认领，不回灌 common |
| temp2 定义长期无人认领 | 后续任务逐项删除或迁入唯一业务所有者 |
| 真实 OCR、设备截图和实机路径无法离线验证 | 只记录 smoke 结果，明确实机未验证 |

## 10. 状态台账

| 阶段 | 结果 | 状态 |
| --- | --- | --- |
| 任务书和基线 | 建立 vision 专属任务书并记录现状 | 已完成 |
| 定义打散与归属 | 核心保留、领域移交、校准包装进入 temp2 | 已完成 |
| 第一轮静态门禁 | 编译、导入、边界、格式和 diff 检查 | 已完成 |
| 后续能力 parity | 逐项恢复迁出实现的行为和测试 | 待后续任务 |
| 上层联调 | 让 application/business/tools 迁移到新入口 | 待后续任务 |
