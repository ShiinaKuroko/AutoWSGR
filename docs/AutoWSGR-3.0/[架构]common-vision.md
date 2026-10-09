# common/vision 架构说明

版本：AutoWSGR-3.0 第一版
状态：草案
适用范围：`autowsgr/common/vision`
实现基线：`codex/20260913-shiinaskuya-upgrade-7b3e`，2026-10-01（识别入口重排：`9e6674a`）

本文描述当前重构后的通用视觉实现。上层旧调用方尚未完成迁移，FastOCR 实机模型链路也未由本轮单元测试覆盖，因此本文暂不作为全仓兼容契约。

## 1. 模块定位

`common/vision` 是 common 层的通用视觉基础模块，为上层提供 NumPy 数组处理、OpenCV 图像处理、像素匹配、模板匹配和 OCR 通用流程，以及截图、前识别和后识别的唯一公共识别流程。

模块自己不做设备通信：需要新画面时，由 service 的公共识别入口通过调用方传入的
`ContextHandle` 取当前截图并登记截图事实。模块不持有设备对象、不管理模板缓存、不持有页面
状态，也不实现业务领域识别、导航或任务调度。模板缓存由 dispatch 持有，页面和舰船等业务
识别由 application 持有。

模块的静态参数和模板根路径由 `autowsgr.common.vision.config` 持有；FastOCR 模型文件由 `ocr_engine/model` 持有；OCR 执行器的运行时资源由 `ocr_engine.executor.OCRExecutor` 持有；组合操作的单例执行器由各自的 adapters 文件持有。

依赖关系是上层调用 `common.vision`，`service.py` 聚合 `adapters`，`adapters` 再调用 NumPy、OpenCV 和 FastOCR 执行器。common/vision 不依赖 application、business、server 或页面模块。

## 2. 模块架构

### 2.1 目录树

```text
autowsgr/common/vision/
├── __init__.py                         # 通用视觉公共门面
├── config.py                            # NumPy、OpenCV 和 OCR 静态配置
├── service.py                           # 七个公共识别功能：截图、前识别和后识别
├── numpy_engine/
│   ├── __init__.py                      # NumPy 执行器出口
│   └── executor.py                      # 数组校验、坐标、采样和裁切
├── opencv_engine/
│   ├── __init__.py                      # OpenCV 执行器出口
│   └── executor.py                      # 图片读取、变换和原子模板匹配
├── ocr_engine/
│   ├── __init__.py                      # FastOCR 执行器和结果类型出口
│   ├── executor.py                      # FastOCR 模型初始化和单次识别
│   └── model/
│       ├── det.onnx                     # 检测模型
│       ├── rec.onnx                     # 识别模型
│       ├── keys.txt                     # 识别字符表
│       ├── LICENSE                       # 模型许可文件
│       └── README.md                     # 模型资源说明
└── adapters/
    ├── __init__.py                      # 通用组合操作聚合出口
    ├── pixel_matching.py                # 像素规则、签名和 NumPy 匹配流程
    ├── template_matching.py             # ROI、模板模型和 OpenCV 匹配流程
    └── text_recognition.py              # OCR 预处理、识别和计数解析
```

### 2.2 文件职责

| 文件/目录 | 负责内容 | 不负责内容 |
| --- | --- | --- |
| `__init__.py` | 只导出七个识别入口、结果类型和识别数据模型 | 算法实现、隐式初始化和业务规则 |
| `service.py` | 七个公共识别功能（截图、前识别、后识别）和唯一一份识别循环 | 视觉算法、识别规则、页面语义和缓存管理 |
| `config.py` | 视觉静态参数、环境变量名称和模板根路径 | 运行时状态和模型初始化 |
| `numpy_engine/executor.py` | NumPy 数组原子操作 | 像素签名策略和页面判断 |
| `opencv_engine/executor.py` | OpenCV 图片读取、变换和原子匹配 | 模板目录业务语义和缓存 |
| `ocr_engine/executor.py` | FastOCR 模型加载和检测结果标准化 | 文本修正、候选业务规则和页面流程 |
| `ocr_engine/model/` | FastOCR 只读模型资源 | 用户运行数据和动态缓存 |
| `adapters/pixel_matching.py` | 像素规则模型和完整像素匹配 | 设备截图和页面识别 |
| `adapters/template_matching.py` | ROI、模板模型、模板加载和匹配组合 | dispatch 缓存和页面模板目录 |
| `adapters/text_recognition.py` | OCR 预处理、识别模式、候选约束和计数解析 | 领域词典和设备截图 |
| `adapters/__init__.py` | 聚合可复用组合函数 | 复制或重写组合实现 |

唯一的运行时状态由其使用者持有：`service.numpy` 和 `service.opencv` 持有基础执行器实例，`pixel_matching._MATCHER` 和 `template_matching._MATCHER` 持有组合器实例，`text_recognition._ocr_executor` 缓存 OCR 执行器。配置模块不持有这些状态。

### 2.3 依赖方向

```text
application / business / tools
              ↓
      autowsgr.common.vision
              ↓
           service
              ↓
          adapters
              ↓
   numpy / opencv / ocr executor
              ↓
    common.system.files / 第三方库
```

上层使用视觉能力只经 `service.py` 的公共识别入口（截图、前识别、后识别）：调用方提供
识别数据、识别规则和预期，具体由 service 的公共识别入口通过 dispatch 的
`ContextHandle` 取当前截图并记录截图事实。视觉层对 `dispatch.context` 只做类型注解引用，
运行时不导入 dispatch 模块。

当前还存在一条共享模型依赖：`pixel_matching` 使用 `template_matching.ROI` 作为通用裁切模型。该依赖只指向模型定义，不反向调用模板匹配流程。

禁止以下方向：

- `common/vision` 不依赖 application、business、server 或页面控制器；
- executor 不依赖 adapters、页面流程或业务识别；
- `config.py` 不持有运行时执行器、缓存或设备对象；
- OCR 不反向调用导航器、设备截图或领域词典；
- `__init__.py` 不复制或包装算法实现；
- dispatch 的模板缓存不回灌到 common/vision 的模块状态；
- 只有 service 的公共识别入口可以取图和记录截图事实，且必须经调用方传入的
  `ContextHandle`；其他模块不得自行截图或持有设备对象。

### 2.4 公开出口策略

`autowsgr.common.vision` 是稳定门面，`service.py` 是门面背后的识别入口实现。根门面只导出七个识别入口、返回类型 `RecognitionResult` 和识别数据模型；不导出 executor 实现类、适配层组合函数、模块缓存或私有辅助函数。

上层使用视觉能力只经 `service.py` 里的七个入口：`shot`、`expect_template`/`expect_ocr`/`expect_pixels`（识别存在）
和 `expect_template_absent`/`expect_ocr_absent`/`expect_pixels_absent`（识别不存在）；每个入口只接受对应识别类型的数据、
规则和预期，不做跨类型分发。历史上这两组入口叫"前识别/后识别"，现按语义命名。`expect_ocr` / `expect_ocr_absent`
的 `expect` 接受单条文本或候选集合：识别存在时命中任一条即满足，识别不存在时需要全部候选都不出现才满足。

门面另外导出调用方表达识别数据和判读结果所需的模型：`ROI`、`Template`、`Color`、`PixelRule`、`MatchStrategy`、`PixelSignature`、`CompositePixelSignature`、`RecognitionProfile`、`TemplateMatchResult`、`PixelMatchResult`、`PixelDetail`、`TextDetection`，以及返回类型 `RecognitionResult`。底层组合能力（模板匹配、OCR、像素匹配、文本预处理、计数解析）和两个基础执行器句柄不再从门面导出；需要它们时经七个识别入口使用。

图像变换（灰度、缩放等）目前只由 `opencv_engine` 提供，是否对上层开放尚未确定；读图统一走 `system.files`。

## 3. 能力总览

上层使用视觉能力的唯一入口是 `service.py` 的七个识别功能；下表是适配层与基础执行器提供的能力清单，供 service 和本层内部使用。

| 能力 | 对外入口 | 所在文件 | 输入 | 输出/副作用 | 负责内容 | 不负责内容 |
| --- | --- | --- | --- | --- | --- | --- |
| NumPy 基础数组 | `numpy_engine.NumpyExecutor` | `numpy_engine/executor.py` | 图片数组、相对坐标 | 数组、坐标或像素值；无外部副作用 | 校验、采样和裁切 | 像素规则和设备截图 |
| OpenCV 基础图像 | `opencv_engine.OpenCVExecutor` | `opencv_engine/executor.py` | 图片数组或模板相对路径 | 图片数组、匹配分数或文件读取 | 图像变换和原子匹配 | 页面模板业务规则和缓存 |
| OCR 识别 | `adapters.text_recognition.recognize_text` | `adapters/text_recognition.py` | 图片、ROI、allowlist、识别模式、候选 | `list[TextDetection]`；首次调用可能初始化模型 | 通用 OCR 识别和候选过滤 | 领域文本修正和设备截图 |
| 像素匹配 | `adapters.pixel_matching.match_pixels` | `adapters/pixel_matching.py` | 图片、像素签名、可选 ROI | `PixelMatchResult` | 采样、颜色距离和策略判定 | 页面状态所有权 |
| 模板匹配 | `adapters.template_matching.match_template` | `adapters/template_matching.py` | 图片、模板、可选 ROI、置信度 | `TemplateMatchResult` 或结果列表 | 缩放、裁切、匹配和坐标还原 | 模板缓存和页面流程 |
| OCR 预处理 | `adapters.text_recognition.prepare_text` | `adapters/text_recognition.py` | 图片和预处理参数 | RGB 图片数组 | 灰度、放大、模糊、归一化和二值化 | OCR 模型调用 |
| OCR 计数解析 | `adapters.text_recognition.parse_counter` | `adapters/text_recognition.py` | OCR 文本和分母 | 分子或 `None` | 解析明确或丢失分隔符的计数 | 业务计数状态更新 |

## 4. NumPy 基础数组

### 4.1 能力说明

`NumpyExecutor` 是 NumPy 数组操作的实例入口，处理 RGB 数组的尺寸校验、相对坐标转换、单点/多点采样和相对区域裁切。它不解释采样值代表什么业务状态。

### 4.2 稳定入口

```text
NumpyExecutor.validate_image(image) -> tuple[int, int]
NumpyExecutor.coordinate_index(image, x, y) -> tuple[int, int]
NumpyExecutor.sample_pixel(image, x, y) -> tuple[int, int, int]
NumpyExecutor.sample_pixels(image, positions) -> numpy.ndarray
NumpyExecutor.crop(image, x1, y1, x2, y2) -> numpy.ndarray
```

`image` 必须是非空的 `H x W x 3` RGB 数组；相对坐标和裁切边界均使用 `[0, 1]`。坐标单位是图片比例，不是绝对像素。

### 4.3 调用示例

```python
from autowsgr.common.vision.numpy_engine import NumpyExecutor

executor = NumpyExecutor()
height, width = executor.validate_image(screen)
pixel = executor.sample_pixel(screen, 0.5, 0.5)
```

### 4.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 图片为空或通道不足 | 拒绝采样 | `ValueError` | 调用方 |
| 坐标超出 `[0, 1]` | 拒绝转换 | `ValueError` | 调用方 |
| 坐标序列为空 | 返回空数组 | `shape=(0, 3)` | 调用方 |

该能力不写文件、不修改输入数组所有权以外的外部状态，也不记录业务日志。

### 4.5 维护规则

新的数组原子操作放在 `numpy_engine/executor.py`。需要解释像素规则或组合 ROI 流程时，放入 adapters，不在 executor 中增加业务判断。

## 5. OpenCV 基础图像

### 5.1 能力说明

`OpenCVExecutor` 是 OpenCV 图像操作的实例入口，负责图片读取、灰度转换、缩放、模糊、归一化、阈值化、旋转裁切和一次原子模板匹配。

### 5.2 稳定入口

```text
OpenCVExecutor.load_image(relative_path) -> numpy.ndarray
OpenCVExecutor.to_gray(image) -> numpy.ndarray
OpenCVExecutor.resize(image, width, height, *, interpolation='area') -> numpy.ndarray
OpenCVExecutor.blur(image, kernel_size) -> numpy.ndarray
OpenCVExecutor.normalize(image) -> numpy.ndarray
OpenCVExecutor.threshold(image) -> numpy.ndarray
OpenCVExecutor.gray_to_rgb(image) -> numpy.ndarray
OpenCVExecutor.rotate_crop(image, center, size, angle) -> numpy.ndarray
OpenCVExecutor.match_template(image, template) -> tuple[float, tuple[int, int]]
```

`load_image` 的路径会经过 `common.system.files` 的允许根目录校验；`relative_path` 是模板根目录下的相对路径。尺寸单位为像素，旋转角度单位为度。

### 5.3 调用示例

```python
from pathlib import Path

from autowsgr.common.vision.opencv_engine import OpenCVExecutor

executor = OpenCVExecutor()
template = executor.load_image(Path('backyard/main_page/backyard.png'))
gray = executor.to_gray(screen)
```

### 5.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 路径越出模板根目录 | 拒绝读取 | `ValueError` | 调用方 |
| 图片不存在 | 拒绝读取 | `FileNotFoundError` | 调用方 |
| 图片无法解码 | 拒绝读取 | `ValueError` | 调用方 |
| 尺寸或高斯核非法 | 拒绝变换 | `ValueError` | 调用方 |
| 模板大于搜索图片 | 返回未命中事实 | `(0.0, (0, 0))` | 组合操作 |

图片读取是唯一文件副作用；变换方法不修改输入数组。

### 5.5 维护规则

新的纯图像变换放入 `opencv_engine/executor.py`。需要 ROI、模板来源元数据或命中规则时，放入 `adapters/template_matching.py`，不把页面语义放回 executor。

## 6. OCR 文字识别

### 6.1 能力说明

`recognize_text` 是 OCR 组合入口，负责 ROI 裁切、识别模式选择和候选集合过滤。FastOCR 原子执行器负责模型调用并返回 `TextDetection`，组合操作不修改识别文本的业务含义。

### 6.2 稳定入口

```text
adapters.text_recognition.recognize_text(
    image,
    *,
    roi=None,
    allowlist='',
    recognition_profile='full',
    candidates=None,
) -> list[TextDetection]
adapters.text_recognition.recognize_text(...) -> list[TextDetection]
adapters.text_recognition.recognize_prepared_text(...) -> list[TextDetection]
```

`allowlist` 是允许识别的字符集合，不是期望答案；`recognition_profile` 当前支持 `full` 和 `single_line`；`candidates` 是完整文本候选集合，提供后只保留完全相等的识别文本。`TextDetection` 包含 `recognized_text`、`confidence_score` 和可选的 `text_region`。

第一次真正调用 OCR 时会创建并缓存 `OCRExecutor`，初始化 MaaFramework、模型资源和用户运行目录。单元测试使用替身执行器，未模拟真实模型初始化。

### 6.3 调用示例

```python
from autowsgr.common.vision import adapters

results = adapters.text_recognition.recognize_text(
    screen,
    allowlist='0123456789',
    recognition_profile='single_line',
    candidates=('3', '10'),
)
```

### 6.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| ROI 非法 | 拒绝裁切 | `ValueError` | 调用方 |
| 识别模式未知 | 拒绝选择 | `ValueError` | 调用方 |
| 模型文件缺失 | 停止初始化 | `RuntimeError` | 运行时启动层 |
| MaaFramework 或模型加载失败 | 停止识别 | `RuntimeError` | 运行时启动层 |
| 没有命中候选 | 返回空列表 | `[]` | 业务识别层 |

OCR 运行时可能创建用户目录并初始化模型资源；不会写入项目内模型目录，也不会记录原始截图或完整用户文本。

### 6.5 维护规则

新增 FastOCR 参数或模型生命周期行为放在 `ocr_engine/executor.py`，新增通用 ROI、预处理或候选组合放在 `adapters/text_recognition.py`。舰船名、页面字段和业务模糊匹配必须留在 application/vision。

## 7. 像素匹配

### 7.1 能力说明

`adapters.pixel_matching.match_pixels` 将图片采样、颜色距离和像素签名策略组合为一次完整判断。`PixelSignature` 可以使用 `ALL`、`ANY` 或 `COUNT` 策略，也可以通过 `CompositePixelSignature` 按顺序组合多个签名。

### 7.2 稳定入口

```text
adapters.pixel_matching.match_pixels(
    image,
    signature,
    *,
    roi=None,
    with_details=False,
) -> PixelMatchResult
```

`signature` 是从门面 `autowsgr.common.vision` 导入的 `PixelSignature` 或 `CompositePixelSignature`；`roi` 使用门面导出的 `ROI`。结果包含是否命中、签名名、命中数量、规则总数和可选详情。

### 7.3 调用示例

```python
from autowsgr.common.vision import adapters
from autowsgr.common.vision import Color, PixelRule, PixelSignature

signature = PixelSignature(
    name='home_ready',
    rules=(PixelRule(0.5, 0.5, Color(10, 20, 30)),),
)
result = adapters.pixel_matching.match_pixels(screen, signature)
```

### 7.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 图片或规则坐标非法 | 拒绝采样 | `ValueError` | 调用方 |
| 颜色容差为负数 | 拒绝创建规则 | `ValueError` | 调用方 |
| 规则未命中 | 返回事实结果 | `matched=False` | 业务识别层 |

像素匹配不操作设备、不写文件，也不改变输入数组。

### 7.5 维护规则

通用颜色距离和像素策略属于 adapters。页面或状态签名实例必须由 application 持有，不能把页面坐标和业务签名常量搬回 common/vision。

## 8. 模板匹配

### 8.1 能力说明

模板匹配组合 ROI 裁切、模板来源分辨率缩放、OpenCV 原子匹配和 ROI 坐标还原。当前入口接收已经加载的 `Template`；模板缓存由 dispatch 负责，common/vision 不持有缓存上下文。

### 8.2 稳定入口

```text
adapters.template_matching.match_template(
    image,
    template,
    *,
    roi=None,
    confidence=0.85,
) -> TemplateMatchResult
adapters.template_matching.match_templates(
    image,
    templates,
    *,
    roi=None,
    confidence=0.85,
) -> list[TemplateMatchResult]
```

`Template` 的 `source_resolution` 按 `(width, height)` 表示；`confidence` 范围为 `[0, 1]`；结果位置是原图绝对像素坐标。`load_template` 不属于公开出口：模板对象由上层资源模块组装，读图统一走 `system.files.load_image`，再交给门面导出的 `Template`。

### 8.3 调用示例

```python
from autowsgr.common.vision import adapters
from autowsgr.common.vision import Template

template = Template(
    name='backyard',
    relative_path='backyard/main_page/backyard.png',
    image=template_image,
    source_resolution=(1280, 720),
)
result = adapters.template_matching.match_template(screen, template, confidence=0.85)
```

### 8.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 模板路径不是相对路径 | 拒绝加载 | `ValueError` | 模板创建者 |
| 置信度不在 `[0, 1]` | 拒绝匹配 | `ValueError` | 调用方 |
| 模板尺寸大于搜索区域 | 返回未命中 | `matched=False` | 业务识别层 |
| ROI 存在 | 裁切后匹配并还原位置 | `TemplateMatchResult` | 调用方 |
| 模板命中 | 附带模板中心的归一化坐标 | `TemplateMatchResult.center` | 调用方（可直接用作点击落点） |
| 模板未命中 | 中心为空值 | `center=None` | 调用方 |

`center` 是**匹配到的模板实际中心**（按截图尺寸归一化、保留四位小数），不是搜索区域 `roi` 的中心：
调用方需要点击按钮时直接取它，不需要再用像素位置自行换算。模板未命中表示位置不可信，因此不给中心。

匹配流程不截图、不保存截图、不管理模板缓存；文件加载只通过 OpenCV executor 的 system.files 边界完成。

### 8.5 维护规则

新增通用模板匹配组合放在 `adapters/template_matching.py`。应用层模板目录、模板名称和页面识别规则必须留在 application/vision；dispatch 只维护跨流程缓存和懒加载上下文。

## 9. OCR 文本预处理

### 9.1 能力说明

`adapters.text_recognition.prepare_text` 将输入统一为适合 OCR 的 RGB 图片，顺序固定为灰度转换、放大、模糊、归一化、Otsu 二值化和灰度转 RGB。

### 9.2 稳定入口

```text
adapters.text_recognition.prepare_text(
    image,
    *,
    scale=4,
    blur_kernel=3,
) -> numpy.ndarray
```

空图片原样返回。`scale` 是放大倍数，`blur_kernel` 是像素边长并且必须为正奇数。

### 9.3 调用示例

```python
from autowsgr.common.vision import adapters

prepared = adapters.text_recognition.prepare_text(screen, scale=4, blur_kernel=3)
results = adapters.text_recognition.recognize_text(prepared)
```

### 9.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 图片为空 | 保持输入 | 原空数组 | 调用方 |
| 高斯核不是正奇数 | 拒绝处理 | `ValueError` | 调用方 |
| 图片格式不受 OpenCV 支持 | 由底层转换失败 | OpenCV 异常 | 调用方 |

预处理只产生新的图片数组，不调用 OCR 模型，不写文件。

### 9.5 维护规则

只把跨业务可复用的图像预处理放在这里。页面专属阈值、颜色校准和文本修正不得进入通用预处理。

## 10. OCR 计数解析

### 10.1 能力说明

`adapters.text_recognition.parse_counter` 从 OCR 文本中提取计数分子，支持明确的 `/` 或 `|` 分隔符，也尝试根据传入分母拆分丢失分隔符的文本。

### 10.2 稳定入口

```text
adapters.text_recognition.parse_counter(text, max_value) -> int | None
```

`max_value` 是识别上下文提供的分母，不由通用视觉模块猜测。无法从无分隔符文本确认分母时返回 `None`；没有数字或分隔符前没有数字时抛出 `ValueError`。

### 10.3 调用示例

```python
from autowsgr.common.vision import adapters

current = adapters.text_recognition.parse_counter('3/10', 10)
```

### 10.4 错误和副作用

| 场景 | 行为 | 异常/结果 | 处理者 |
| --- | --- | --- | --- |
| 文本含明确分隔符且分子有数字 | 返回分子 | `int` | 业务层 |
| 文本丢失分隔符但能确认分母 | 返回分子 | `int` | 业务层 |
| 无分隔符且无法确认分母 | 保留不确定性 | `None` | 业务层 |
| 文本没有数字 | 拒绝解析 | `ValueError` | 业务层 |

### 10.5 维护规则

这里只维护通用计数文本解析。任务次数、资源上限和页面 OCR 规则由业务模块提供 `max_value` 并负责解释结果。

## 11. 统一配置

配置文件：`autowsgr/common/vision/config.py`。

配置常量使用 `NUMPY_`、`OPENCV_` 和 `OCR_` 前缀。当前配置是模块级静态值，不是用户配置模型；OCR 模型目录、用户运行目录和阈值可以通过环境变量覆盖，并在 `OCRExecutor` 创建时生效。

| 字段 | 默认值 | 类型/单位 | 业务作用 | 是否可覆写 | 生效时机 |
| --- | --- | --- | --- | --- | --- |
| `NUMPY_DEFAULT_PIXEL_TOLERANCE` | `30.0` | `float`，颜色距离 | 默认像素颜色容差 | 否 | 模块导入 |
| `NUMPY_COORDINATE_MIN` | `0.0` | `float`，相对坐标 | 相对坐标下界 | 否 | 模块导入 |
| `NUMPY_COORDINATE_MAX` | `1.0` | `float`，相对坐标 | 相对坐标上界 | 否 | 模块导入 |
| `OPENCV_TEMPLATE_ROOT` | `resources/image` | `Path` | 模板文件根目录 | 否 | 模块导入 |
| `OPENCV_TEMPLATE_SOURCE_RESOLUTION` | `(1280, 720)` | `tuple[int, int]`，像素 | 模板默认来源分辨率 | 否 | 模块导入 |
| `OPENCV_TEMPLATE_CONFIDENCE` | `0.85` | `float`，`[0, 1]` | 模板匹配默认阈值 | 否 | 调用入口取默认值 |
| `OPENCV_TEXT_SCALE` | `4` | `int`，倍数 | OCR 文本默认放大倍数 | 否 | 调用入口取默认值 |
| `OPENCV_TEXT_BLUR_KERNEL` | `3` | `int`，像素边长 | OCR 文本默认高斯核 | 否 | 调用入口取默认值 |
| `OCR_MODEL_FILES` | `det.onnx`、`rec.onnx`、`keys.txt` | 文件名元组 | 模型完整性检查 | 否 | OCR 执行器创建 |
| `OCR_MODEL_DIR_ENV` | `AUTOWSGR_FASTOCR_MODEL_DIR` | 环境变量名 | 覆写模型目录 | 是 | OCR 执行器创建 |
| `OCR_USER_DIR_ENV` | `AUTOWSGR_FASTOCR_USER_DIR` | 环境变量名 | 覆写 Maa 用户目录 | 是 | OCR 执行器创建 |
| `OCR_THRESHOLD_ENV` | `AUTOWSGR_FASTOCR_THRESHOLD` | 环境变量名 | 覆写 OCR 阈值 | 是 | OCR 执行器创建 |
| `OCR_DEFAULT_THRESHOLD` | `0.3` | `float` | OCR 默认阈值 | 通过环境变量 | OCR 执行器创建 |

配置不负责创建目录、加载模型、持有图片缓存或决定业务恢复策略。

## 12. 错误约定

本模块没有自定义错误基类。输入校验使用 `ValueError`，文件边界保留 `system.files` 的 `FileNotFoundError` 和图片解码 `ValueError`，FastOCR 初始化和识别失败使用 `RuntimeError`。

```text
ValueError / FileNotFoundError / RuntimeError
            ↓
      common.vision
            ↓
      上层业务处理者
```

通用视觉层不捕获后重试、不静默降级、不替调用方决定页面恢复。调用方可以把 `TemplateMatchResult.matched=False`、空 OCR 列表或 `parse_counter` 的 `None` 作为正常识别事实处理；异常则继续向拥有恢复策略的上层抛出。

## 13. 日志约定

日志通过 `autowsgr.common.system.logger.get_logger` 获取，当前 channel 为：

- `adapters.pixel_matching.match_pixels`：像素匹配结果；
- `adapters.template_matching.match_template`：模板路径、分数和命中结果；
- `adapters.text_recognition.recognize_text`：识别模式、结果数量和候选约束数量。

组合操作只记录有界的 `DEBUG` 诊断事实，使用 `[VISION]` 前缀和占位符，不记录原始截图、完整 OCR 文本、用户配置或绝对资源路径。NumPy、OpenCV 和 FastOCR 原子执行器不重复记录高频底层调用。

本模块不记录 `INFO` 页面动作，因为视觉层不拥有页面状态转换；不记录 `WARNING` 或 `ERROR`，因为异常最终处理者是上层恢复或终止流程。若未来增加业务流程日志，必须由拥有流程结果的上层模块记录，不能把页面成功写入 common/vision。

## 14. 公开出口和调用边界

### 14.1 稳定出口

| 出口 | 来源 | 调用者可以做什么 | 调用者不能做什么 |
| --- | --- | --- | --- |
| `NumpyExecutor`（`numpy_engine`） | 本层实例 | 执行 NumPy 数组操作 | 读取或修改内部执行器状态 |
| `OpenCVExecutor`（`opencv_engine`） | 本层实例 | 执行 OpenCV 图片操作 | 绕过 system.files 的路径边界 |
| `adapters.text_recognition.recognize_text` | 适配层 | 执行通用 OCR 识别 | 把候选约束当作领域模糊匹配 |
| `adapters.pixel_matching.match_pixels` | 适配层 | 执行像素签名匹配 | 在 common 层持有页面签名 |
| `adapters.template_matching.match_template` | 适配层 | 执行单模板匹配 | 让 common 层截图或管理模板缓存 |
| `adapters.template_matching.match_templates` | 适配层 | 按顺序执行多模板匹配 | 解释模板对应的页面业务 |
| `adapters.text_recognition.prepare_text` | 适配层 | 执行通用 OCR 预处理 | 写入页面专属校准规则 |
| `adapters.text_recognition.recognize_text` | 适配层 | 执行 OCR 识别和候选过滤 | 直接决定业务状态或导航 |
| `adapters.text_recognition.recognize_prepared_text` | 适配层 | 预处理后执行 OCR | 重复实现 OCR 预处理链 |
| `adapters.text_recognition.parse_counter` | 适配层 | 解析通用计数文本 | 更新任务或资源状态 |

### 14.2 内部内容

`_MATCHER`、`_ocr_executor`、`TemplateMatcher._relative_path`、`OCRExecutor._recognize`、模型句柄、MaaFramework 绑定、模板根路径拼接和模块缓存均属于实现细节。`numpy_engine`、`opencv_engine` 和 `ocr_engine` 的执行器类用于 adapters 组合，不应被上层绕过 service 形成第二套调用契约。

当前 `Template`、`ROI`、像素签名模型仍从其定义模块提供输入；根门面没有复制这些类型，也没有为旧接口提供兼容别名。

## 15. 模块维护方法

### 15.1 添加能力

1. 先确认能力是通用视觉能力，不是页面、舰船、战斗或设备流程。
2. 原子数组、OpenCV 或 FastOCR 调用放入对应 executor；多个基础能力的完整组合放入 adapters。
3. 先复用现有 ROI、结果模型和配置前缀，不新增重复模型或 engine 包装层。
4. 确认稳定入口、输入输出、异常和日志所有权。
5. 同步更新本架构文档、`service.py`、根 `__all__` 和 `testing/common/vision` 测试。
6. 执行本模块验收门禁后再让上层适配。

### 15.2 添加资源或子模块

模型等只读资源放在对应 executor 的资源目录；用户运行数据放在用户目录；模板缓存放在 dispatch。新增资源必须有路径安全边界和缺失资源测试，不得把运行时缓存放入源码资源目录。

### 15.3 修改配置

配置修改必须保持 `NUMPY_`、`OPENCV_`、`OCR_` 前缀，记录默认值、单位、覆写入口和生效时机，并同步非法值测试及本文件配置表。

### 15.4 修改公开契约

新增或删除门面入口前，必须同步修改 service、适配层、根门面、架构文档、专属测试和所有已迁移调用者。旧上层尚未迁移时不得通过别名隐藏契约差异。

## 16. 验收门禁

本轮已完成的检查：

1. 公共入口导入和 5 项新视觉流程测试：通过，`5 passed`；
2. `uv run python -m compileall -q autowsgr/common/vision`：通过；
3. `uv run --with ruff ruff check autowsgr/common/vision testing/common/vision`：通过；
4. `uv run --with ruff ruff format --check autowsgr/common/vision testing/common/vision`：通过；
5. `git diff --check`：源码范围通过；
6. NumPy、OpenCV、ROI、像素匹配、OCR 预处理和 OCR 候选编排边界：由新测试覆盖。

以下内容不在本轮单元测试承诺内：

- 真实 FastOCR 模型加载、MaaFramework 资源绑定和设备截图；
- 旧 `testing/vision` 对已删除历史 API 的兼容性；
- application、business、server 对新 service 入口的全量迁移；
- dispatch/template cache 与所有上层资源的实机联调。

在上述范围完成并重新验证前，文档保持“草案”，不得作为全仓兼容契约使用。
