"""模块功能：维护任务页面的坐标、颜色、扫描和滚动校准常量。

上层调用：
- application.ui.controller.operations.mission_page.page：读取返回、面板切换和滚动参数。
- application.ui.controller.operations.mission_page.recognition：读取按钮扫描、颜色和 OCR 裁剪参数。

下层依赖：
- 无。

本模块只保存任务页面的物理校准和时序参数，不加载通用校准、不保存页面状态、
设备对象或任务结果。
"""

from __future__ import annotations


# ── 页面动作与滚动参数 ──────────────────────────────────────────────────────

CLICK_BACK = (0.0219, 0.0584)  # 任务页面左上角返回按钮，用于回到母港主页。
PANEL_POSITIONS = {
    'all': (0.1540, 0.0667),  # 全部面板入口，用于查看所有任务。
    'main': (0.2797, 0.0680),  # 主线面板入口，用于查看主线任务。
    'daily': (0.4047, 0.0612),  # 日常面板入口，用于查看日常任务。
    'weekly': (0.5407, 0.0584),  # 周常面板入口，用于查看周常任务。
    'timed': (0.6672, 0.0570),  # 限时面板入口，用于查看限时任务。
}
PANEL_SWITCH_DELAY: float = 0.5  # 任务子标签切换等待时间，用于等待列表内容稳定。
SCROLL = (0.5000, 0.7000, 0.5000, 0.4500)  # 任务列表滑动坐标，用于显示后续任务。
SCROLL_DURATION: float = 0.75  # 任务列表滑动时长，用于控制滚动动画。
SCROLL_DELAY: float = 0.5  # 任务列表滑动等待时间，用于等待滚动结果稳定。


# ── 按钮扫描颜色 ────────────────────────────────────────────────────────────

GOTO_COLOR = (15, 132, 228)  # “前往”按钮 RGB 颜色，用于识别未完成任务。
GOTO_TOLERANCE: float = 40.0  # “前往”颜色容差，用于兼容截图渲染差异。
CLAIM_R_MIN: int = 180  # “领取”按钮红色下限，用于识别可领取任务。
CLAIM_G_MIN: int = 120  # “领取”按钮绿色下限，用于识别可领取任务。
CLAIM_B_MAX: int = 80  # “领取”按钮蓝色上限，用于排除非橙色按钮。


# ── 按钮扫描与 OCR 裁剪 ─────────────────────────────────────────────────────

BUTTON_SCAN_ROI = (0.8600, 0.1700, 0.9600, 0.8500)  # 任务按钮扫描区域，用于定位右侧操作按钮。
SCAN_X: float = 0.9100  # 按钮扫描横坐标，用于采样按钮颜色。
SCAN_Y_STEP: float = 0.0050  # 按钮扫描纵向步长，用于平衡精度和采样次数。
CLUSTER_GAP: float = 0.0600  # 按钮颜色聚类间隔，用于合并同一任务按钮的采样点。
MIN_CLUSTER_SIZE: int = 3  # 按钮最小聚类大小，用于过滤颜色噪点。
WIDE_BTN_CHECK_X: float = 0.8000  # 一键领取检测横坐标，用于排除底部宽按钮。
NAME_CROP_MIN_Y: float = 0.1200  # 任务名称裁剪上限，用于过滤被标题栏遮挡的任务行。
OCR_CONFIDENCE_MIN: float = 0.10  # 任务名称最低置信度，用于拒绝无效 OCR 结果。
NAME_ROI_X1: float = 0.2200  # 任务名称裁剪左边界，用于提取任务名称。
NAME_ROI_X2: float = 0.6000  # 任务名称裁剪右边界，用于提取任务名称。
NAME_Y_OFFSET: float = -0.1450  # 任务名称相对按钮纵向偏移，用于定位名称区域。
NAME_ROI_Y_PAD: float = 0.0350  # 任务名称裁剪半高，用于限定 OCR 区域。
PROGRESS_ROI_X1: float = 0.7500  # 任务进度裁剪左边界，用于提取完成百分比。
PROGRESS_ROI_X2: float = 0.8700  # 任务进度裁剪右边界，用于提取完成百分比。
PROGRESS_Y_OFFSET: float = 0.1050  # 任务进度相对按钮纵向偏移，用于定位进度区域。
PROGRESS_ROI_Y_PAD: float = 0.0350  # 任务进度裁剪半高，用于限定 OCR 区域。


__all__ = [
    'BUTTON_SCAN_ROI',
    'CLAIM_B_MAX',
    'CLAIM_G_MIN',
    'CLAIM_R_MIN',
    'CLICK_BACK',
    'CLUSTER_GAP',
    'GOTO_COLOR',
    'GOTO_TOLERANCE',
    'MIN_CLUSTER_SIZE',
    'NAME_CROP_MIN_Y',
    'NAME_ROI_X1',
    'NAME_ROI_X2',
    'NAME_ROI_Y_PAD',
    'NAME_Y_OFFSET',
    'OCR_CONFIDENCE_MIN',
    'PANEL_POSITIONS',
    'PANEL_SWITCH_DELAY',
    'PROGRESS_ROI_X1',
    'PROGRESS_ROI_X2',
    'PROGRESS_ROI_Y_PAD',
    'PROGRESS_Y_OFFSET',
    'SCAN_X',
    'SCAN_Y_STEP',
    'SCROLL',
    'SCROLL_DELAY',
    'SCROLL_DURATION',
    'WIDE_BTN_CHECK_X',
]
