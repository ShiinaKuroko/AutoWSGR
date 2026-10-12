"""模块功能：维护后院检查器的识别模板路径与识别区域。

上层调用：
- application.ui.navigation.checker.backyard：读取本模块识别数据。

下层依赖：
- common.vision：提供 ROI 模型。

边界：只保存识别模板路径与识别区域，不保存识别阈值、判定规则或点击坐标。
"""

from __future__ import annotations

from autowsgr.common.vision import ROI


# 模板根下的命名空间：一级模板（四个入口）放 backyard 根，二级页模板各自放子目录。
TEMPLATE_NAMESPACE = 'backyard'


# ── 后院主页身份 ────────────────────────────────────────────────────────────

# 后院主页没有专属模板：四个入口同一时刻出现，任选其一当身份即可，这里取浴室入口。
BACKYARD_TEMPLATE = 'BACKYARD_BATH_ENTRY_720P.png'
BACKYARD_ROI = ROI(0.2446, 0.3, 0.3524, 0.4167)


# ── 四个入口（点击落点用） ──────────────────────────────────────────────────

# 入口模板目录小写、文件名全大写；名称与上面的身份模板同源。
CANTEEN_ENTRY_TEMPLATE = 'BACKYARD_CANTEEN_ENTRY_720P.png'
ACADEMY_ENTRY_TEMPLATE = 'BACKYARD_ACADEMY_ENTRY_720P.png'
RANK_ROOM_ENTRY_TEMPLATE = 'BACKYARD_RANK_ROOM_ENTRY_720P.png'
BATH_ENTRY_TEMPLATE = 'BACKYARD_BATH_ENTRY_720P.png'

CANTEEN_ENTRY_ROI = ROI(0.7485, 0.5764, 0.8758, 0.7487)
ACADEMY_ENTRY_ROI = ROI(0.8641, 0.3473, 0.9696, 0.4695)
RANK_ROOM_ENTRY_ROI = ROI(0.6493, 0.1514, 0.7532, 0.2362)
BATH_ENTRY_ROI = ROI(0.2446, 0.3, 0.3524, 0.4167)


# ── 四个二级页 ──────────────────────────────────────────────────────────────

# 二级页模板放在以页面命名的子目录里，命名空间随之下沉一层；文件名不再重复域前缀。
CANTEEN_PAGE_NAMESPACE = 'backyard/canteen'
CANTEEN_PAGE_TEMPLATE = 'CANTEEN_PAGE_720P.png'
CANTEEN_PAGE_ROI = ROI(0.879, 0.1375, 0.9672, 0.1917)

ACADEMY_PAGE_NAMESPACE = 'backyard/academy'
ACADEMY_PAGE_TEMPLATE = 'ACADEMY_PAGE_720P.png'
ACADEMY_PAGE_ROI = ROI(0.8508, 0.0181, 0.9969, 0.1028)

RANK_ROOM_PAGE_NAMESPACE = 'backyard/rank_room'
RANK_ROOM_PAGE_TEMPLATE = 'RANK_ROOM_PAGE_720P.png'
RANK_ROOM_PAGE_ROI = ROI(0.1571, 0.5, 0.3047, 0.5959)

BATH_PAGE_NAMESPACE = 'backyard/bath'
BATH_PAGE_TEMPLATE = 'BATH_PAGE_720P.png'
BATH_PAGE_ROI = ROI(0.8336, 0.0292, 1.0, 0.1209)
