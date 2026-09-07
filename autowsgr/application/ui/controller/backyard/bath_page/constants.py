"""模块功能：维护浴室页面的点击、滑动、颜色和卡片 OCR 校准参数。

上层调用：
- application.ui.controller.backyard.bath_page.page：读取页面动作和按钮状态校准。
- application.ui.controller.backyard.bath_page.recognition：读取卡片几何和 OCR 校准。

下层依赖：
- 无。参数属于浴室页面专用校准数据，由页面 Controller 和识别模块直接读取。

本模块不保存页面状态、业务规则或设备对象；页面等待策略和修理流程仍由
``page.py`` 负责。
"""

# ── 页面点击坐标 (归一化相对坐标) ─────────────────────────────────────────────

CLICK_BACK = (0.0219, 0.0583)  # 浴室页面左上角返回按钮。
CLICK_REPAIR_ALL = (0.6805, 0.1708)  # 选择修理浮层的全部修理按钮。
CLICK_CHOOSE_REPAIR = (0.9375, 0.0556)  # 浴室页面的选择修理入口。
CLICK_CLOSE_OVERLAY = (0.9563, 0.0903)  # 选择修理浮层的关闭按钮。
CLICK_FIRST_REPAIR_SHIP = (0.1195, 0.4319)  # 修理列表第一张舰船卡片。

# ── 修理列表滑动参数 ──────────────────────────────────────────────────────────

SWIPE_START = (0.6602, 0.5000)  # 从修理列表右侧开始滑动。
SWIPE_END = (0.3297, 0.5000)  # 向左滑到修理列表左侧。
SWIPE_DURATION = 0.5  # 单次列表滑动持续时间 (秒)。
SWIPE_DELAY = 1.0  # 滑动后等待页面稳定的时间 (秒)。

# ── 卡片轮廓检测参数 (像素) ───────────────────────────────────────────────────

BORDER_THRESHOLD = 220  # 明亮卡片边框的灰度二值化阈值。
CARD_WIDTH_RANGE = (150, 250)  # 候选卡片矩形的允许宽度范围。
CARD_HEIGHT_RANGE = (400, 600)  # 候选卡片矩形的允许高度范围。
FULL_CARD_WIDTH = 174  # 完整舰船卡片的参考宽度。
FULL_CARD_WIDTH_RATIO = 0.9  # 实际宽度达到参考宽度的比例才算完整。
EDGE_MARGIN = 5  # 卡片距离截图左右边缘的最小像素距离。

# ── 舰船名称与修理时间 OCR 参数 ─────────────────────────────────────────────

NAME_Y_RANGE = (118, 150)  # 卡片下半部分中舰船名称的 y 坐标范围。
NAME_CONFIDENCE_MIN = 0.1  # 舰船名称 OCR 结果的最低置信度。
TIME_CROP_Y = 195  # 从卡片下半部分第几行开始裁剪修理时间。
TIME_SCALE = 2  # 修理时间 OCR 前的图像放大倍数。

# ── 浮层按钮颜色 ─────────────────────────────────────────────────────────────

REPAIR_ALL_BUTTON_COLOR = ((17, 119, 216), 30.0)  # (RGB, 容差): 全部修理按钮。
CLOSE_OVERLAY_BUTTON_COLOR = ((197, 199, 194), 30.0)  # (RGB, 容差): 浮层关闭按钮。


__all__ = [
    'BORDER_THRESHOLD',
    'CARD_HEIGHT_RANGE',
    'CARD_WIDTH_RANGE',
    'CLICK_BACK',
    'CLICK_CHOOSE_REPAIR',
    'CLICK_CLOSE_OVERLAY',
    'CLICK_FIRST_REPAIR_SHIP',
    'CLICK_REPAIR_ALL',
    'CLOSE_OVERLAY_BUTTON_COLOR',
    'EDGE_MARGIN',
    'FULL_CARD_WIDTH',
    'FULL_CARD_WIDTH_RATIO',
    'NAME_CONFIDENCE_MIN',
    'NAME_Y_RANGE',
    'REPAIR_ALL_BUTTON_COLOR',
    'SWIPE_DELAY',
    'SWIPE_DURATION',
    'SWIPE_END',
    'SWIPE_START',
    'TIME_CROP_Y',
    'TIME_SCALE',
]
