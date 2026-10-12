"""模块功能：维护出征页检查器的识别模板路径与识别区域。

上层调用：
- application.ui.navigation.checker.sortie：读取本模块识别数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存识别模板路径与识别区域，不保存识别阈值、判定规则或点击坐标。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 本模块在模板根下的命名空间，完整路径由公共校准模块拼接。
TEMPLATE_NAMESPACE = 'sortie'

# 五个标签的激活态与未激活态模板；目录小写、文件名全大写。
# 只保留激活态模板：前识别命中即激活，后识别（absent）命中即未激活，不必再存一套未激活模板。
SORTIE_TAB_TEMPLATE = 'SORTIE_SORTIE_TAB_720P.png'
EXERCISE_TAB_TEMPLATE = 'SORTIE_EXERCISE_TAB_720P.png'
EXPEDITION_TAB_TEMPLATE = 'SORTIE_EXPEDITION_TAB_720P.png'
CAMPAIGN_TAB_TEMPLATE = 'SORTIE_CAMPAIGN_TAB_720P.png'
DECISIVE_TAB_TEMPLATE = 'SORTIE_DECISIVE_TAB_720P.png'


# ── 标签栏识别区域 ──────────────────────────────────────────────────────────

# 校准基准 1280x720；区域由 SORTIE_TAB_ROI_REPORT.json 的像素框换算为四位小数，
# 并按 [规范]python-code-style.md §6.5 外扩，保证区域大于对应模板。
SORTIE_TAB_ROI = ROI(0.1539, 0.0166, 0.2149, 0.0723)
EXERCISE_TAB_ROI = ROI(0.2796, 0.0152, 0.3438, 0.075)
EXPEDITION_TAB_ROI = ROI(0.4078, 0.0138, 0.4735, 0.0764)
CAMPAIGN_TAB_ROI = ROI(0.5367, 0.0138, 0.6008, 0.0764)
DECISIVE_TAB_ROI = ROI(0.6656, 0.0166, 0.7336, 0.075)
