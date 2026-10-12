"""模块功能：维护后院主页检查器的识别模板路径与识别区域。

上层调用：
- application.ui.navigation.checker.backyard：读取本模块识别数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存识别模板路径与识别区域，不保存识别阈值、判定规则或点击坐标。
四个二级页各有自己的子包与校准数据，不放这里。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 本模块在模板根下的命名空间；四个入口模板都放在这个根目录下。
TEMPLATE_NAMESPACE = 'backyard'


# ── 后院主页身份 ────────────────────────────────────────────────────────────

# 后院主页没有专属模板：四个入口同一时刻出现，任选其一当身份即可，这里取浴室入口。
BACKYARD_TEMPLATE = 'BACKYARD_BATH_ENTRY_720P.png'
BACKYARD_ROI = ROI(0.2446, 0.3, 0.3524, 0.4167)


# ── 四个入口（点击落点用） ──────────────────────────────────────────────────

CANTEEN_ENTRY_TEMPLATE = 'BACKYARD_CANTEEN_ENTRY_720P.png'
ACADEMY_ENTRY_TEMPLATE = 'BACKYARD_ACADEMY_ENTRY_720P.png'
RANK_ROOM_ENTRY_TEMPLATE = 'BACKYARD_RANK_ROOM_ENTRY_720P.png'
BATH_ENTRY_TEMPLATE = 'BACKYARD_BATH_ENTRY_720P.png'

CANTEEN_ENTRY_ROI = ROI(0.7485, 0.5764, 0.8758, 0.7487)
ACADEMY_ENTRY_ROI = ROI(0.8641, 0.3473, 0.9696, 0.4695)
RANK_ROOM_ENTRY_ROI = ROI(0.6493, 0.1514, 0.7532, 0.2362)
BATH_ENTRY_ROI = ROI(0.2446, 0.3, 0.3524, 0.4167)
