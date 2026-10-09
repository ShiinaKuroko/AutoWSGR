"""模块功能：维护普通推图活动的页面坐标与模板路径。

上层调用：
- application.ui.navigation.page_checker.event_checker.stage_push：读取本活动的校准数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存静态校准数据，不保存识别阈值、OCR 规则或页面状态。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 活动标识与本期期号；换期只改期号，并补 resources/data/map/event 下的数据文件。
ACTIVITY = 'stage_push'
PERIOD = '20260930'

# 本活动在模板根下的命名空间，完整路径由公共校准模块拼接。
TEMPLATE_NAMESPACE = 'event_checker/stage_push'

# 本活动的模板文件名。
HOME_ENTRY_TEMPLATE = 'EVENT_HOME_ENTRY_720P.png'
MODE_NORMAL_TEMPLATE = 'EVENT_MODE_NORMAL_720P.png'
MODE_HARD_TEMPLATE = 'EVENT_MODE_HARD_720P.png'
SORTIE_PREPARE_TEMPLATE = 'EVENT_SORTIE_PREPARE_720P.png'


# ── 活动识别区域 ────────────────────────────────────────────────────────────────────

# 校准值以 1280x720 截图为基准换算为归一化区域。
HOME_ENTRY_ROI = ROI(0.8546, 0.3222, 0.9883, 0.6834)
# 地图页左下角模式按钮；按钮文字表示"要切换到的"模式，命中它说明当前在另一种难度。
MODE_ROI = ROI(0.0101, 0.9, 0.1118, 0.932)
# 地图标题区域，普通地图与困难地图的名称不同。
MAP_NAME_ROI = ROI(0.4023, 0.0291, 0.5954, 0.0723)
# 节点浮窗内的出击准备按钮，命中即说明节点浮窗已经打开。
SORTIE_PREPARE_ROI = ROI(0.7882, 0.8166, 0.925, 0.882)
# 节点浮窗左上角的关卡标题，干净地图页该区域没有文字。
STAGE_TITLE_ROI = ROI(0.0273, 0.0625, 0.2079, 0.1084)
