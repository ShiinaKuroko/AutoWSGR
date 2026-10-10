"""模块功能：维护登录流程各画面的识别区域、模板与期望文本。

上层调用：
- application.ui.navigation.page_checker.login_checker.recognition：读取识别区域与期望文本。

下层依赖：
- common.vision：提供归一化识别区域类型。

边界：只保存静态识别数据，不识别画面、不点击、不持有运行状态。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# ── 模板 ────────────────────────────────────────────────────────────────────

# 模板目录名，对应 resources/image/application/ui/navigation/page_checker/login/。
TEMPLATE_NAMESPACE = 'login'

# 健康游戏提示的黑屏画面，全屏模板。
BLACK_SCREEN_TEMPLATE = 'LOGIN_BLACK_SCREEN_720P.png'

# 登录页的进入游戏按钮。
ENTER_BUTTON_TEMPLATE = 'LOGIN_ENTER_BUTTON_720P.png'

# 登录页的点击换区文字。
SWITCH_ENTRY_TEMPLATE = 'SERVER_SWITCH_ENTRY_720P.png'

# 区服选择页的切换大区按钮。
SWITCH_SERVER_TEMPLATE = 'SERVER_SWITCH_BUTTON_720P.png'


# ── 识别区域 ────────────────────────────────────────────────────────────────

# 更新提示文字区域。
UPDATE_PROMPT_ROI = ROI(0.3211, 0.3681, 0.4859, 0.4222)

# 更新中与加载中的进度文字区域，两个画面共用同一条横幅。
PROGRESS_TEXT_ROI = ROI(0.3867, 0.8389, 0.6125, 0.8986)

# 进入游戏按钮区域。
ENTER_BUTTON_ROI = ROI(0.8195, 0.8236, 0.9531, 0.9097)

# 点击换区文字区域。
SWITCH_ENTRY_ROI = ROI(0.6820, 0.6958, 0.7844, 0.7653)

# 切换大区按钮区域。
SWITCH_SERVER_ROI = ROI(0.8133, 0.8792, 0.9398, 0.9653)

# 四个区服条目区域，顺序与区服列表从上到下一致。
SERVER_NAME_ROIS = (
    ROI(0.7836, 0.0389, 0.8984, 0.1194),
    ROI(0.7852, 0.1972, 0.8961, 0.2708),
    ROI(0.7883, 0.3583, 0.8977, 0.4292),
    ROI(0.7867, 0.5097, 0.9000, 0.5847),
)


# ── OCR 期望文本 ────────────────────────────────────────────────────────────

UPDATE_PROMPT_TEXT = '有新的内容需要更新'
LOADING_TEXT = '正在进入港区'
SERVER_NAMES = ('胡德', '俾斯麦', '昆西', '长春')


__all__ = [
    'BLACK_SCREEN_TEMPLATE',
    'ENTER_BUTTON_ROI',
    'ENTER_BUTTON_TEMPLATE',
    'LOADING_TEXT',
    'PROGRESS_TEXT_ROI',
    'SERVER_NAMES',
    'SERVER_NAME_ROIS',
    'SWITCH_ENTRY_ROI',
    'SWITCH_ENTRY_TEMPLATE',
    'SWITCH_SERVER_ROI',
    'SWITCH_SERVER_TEMPLATE',
    'TEMPLATE_NAMESPACE',
    'UPDATE_PROMPT_ROI',
    'UPDATE_PROMPT_TEXT',
]
