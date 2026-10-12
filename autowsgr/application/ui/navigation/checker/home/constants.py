"""模块功能：维护主页检查器的识别模板路径与识别区域。

上层调用：
- application.ui.navigation.checker.home：读取本模块识别数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存识别模板路径与识别区域，不保存识别阈值、判定规则或点击坐标。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 本模块在模板根下的命名空间，完整路径由公共校准模块拼接。
TEMPLATE_NAMESPACE = 'home'

# 本模块的模板文件名；目录小写、文件名全大写。
HOME_MAIN_TEMPLATE = 'HOME_MAIN_720P.png'
NEWS_TEXT_TEMPLATE = 'HOME_NEWS_TEXT_720P.png'
NEWS_CHECKED_TEMPLATE = 'HOME_NEWS_CHECKBOX_CHECKED_720P.png'
NEWS_UNCHECKED_TEMPLATE = 'HOME_NEWS_CHECKBOX_UNCHECKED_720P.png'
REWARD_TEXT_TEMPLATE = 'HOME_REWARD_TEXT_720P.png'
REWARD_CLAIM_TEMPLATE = 'HOME_REWARD_CLAIM_BUTTON_720P.png'
REWARD_CONFIRM_TEMPLATE = 'HOME_REWARD_CONFIRM_BUTTON_720P.png'


# ── 主页识别区域 ────────────────────────────────────────────────────────────────────

# 主页入口图标的归一化区域，校准基准为 1280x720 截图。
HOME_MAIN_ROI = ROI(0.9109, 0.8681, 0.9758, 0.9139)


# ── 每日浮窗识别区域 ──────────────────────────────────────────────────────────────────

# 公告浮窗文字区域与勾选框区域。
NEWS_TEXT_ROI = ROI(0.0867, 0.8763, 0.2125, 0.9403)
NEWS_CHECKBOX_ROI = ROI(0.0382, 0.8652, 0.0875, 0.9459)
# 每日奖励浮窗的文字区域与领取按钮区域。
REWARD_TEXT_ROI = ROI(0.1015, 0.268, 0.3313, 0.3362)
REWARD_CLAIM_BUTTON_ROI = ROI(0.4406, 0.6291, 0.5594, 0.7028)
# 每日奖励确认浮窗的确认按钮区域。
REWARD_CONFIRM_BUTTON_ROI = ROI(0.4351, 0.5194, 0.5696, 0.6209)
