"""模块功能：维护决战页面组的私有坐标、视觉阈值和 OCR 区域校准。

上层调用：
- application.ui.controller.operations.sortie_page.decisive_page.page：读取总览页校准。
- application.ui.controller.operations.sortie_page.decisive_page.map_page：读取地图页和浮层操作校准。
- application.ui.controller.operations.sortie_page.decisive_page.recognition：读取 OCR 区域和节点识别校准。
- application.ui.controller.operations.sortie_page.decisive_page.overlay：读取浮层视觉签名。

下层依赖：
- common.vision：提供颜色、像素规则和像素签名数据类型。

本模块只保存决战页面的静态物理校准，不保存上下文、运行状态、业务策略或重试流程。
"""

from __future__ import annotations

from autowsgr.common.vision import Color, MatchStrategy, PixelRule, PixelSignature


# 总览页点击坐标。
CLICK_BACK = (0.0219, 0.0584)  # 总览页返回按钮，用于回到母港主页。
CLICK_PREV_CHAPTER = (0.8209, 0.9389)  # 前一章节按钮，用于查看上一决战章节。
CLICK_NEXT_CHAPTER = (0.9375, 0.9389)  # 后一章节按钮，用于查看下一决战章节。
CLICK_ENTER_MAP = (0.5209, 0.9259)  # 进入地图按钮，用于进入当前章节地图。
CLICK_RESET_CHAPTER = (0.5000, 0.9250)  # 重置关卡按钮，用于清空当前章节进度。
CLICK_BUY_TICKET_OPEN = (0.3579, 0.9237)  # 磁盘购买入口，用于打开资源购买浮层。
CLICK_BUY_RESOURCE = {
    'oil': (0.6646, 0.3408),  # 石油购买按钮，用于消耗石油购买磁盘。
    'ammo': (0.6646, 0.4352),  # 弹药购买按钮，用于消耗弹药购买磁盘。
    'steel': (0.6646, 0.5167),  # 钢材购买按钮，用于消耗钢材购买磁盘。
    'aluminum': (0.6646, 0.5945),  # 铝材购买按钮，用于消耗铝材购买磁盘。
}  # 资源类型到购买按钮坐标的映射，用于选择磁盘支付资源。
CLICK_BUY_CONFIRM = (0.5084, 0.7500)  # 购买确认按钮，用于提交磁盘购买。


# 决战地图页和浮层点击坐标。
CLICK_MAP_BACK = (0.0297, 0.0598)  # 决战地图返回按钮，用于回到决战总览页。
CLICK_CHOOSE_SHIP_BACK = (0.0500, 0.0500)  # 选船浮层返回按钮，用于回到出征准备页。
CLICK_RETREAT_BUTTON = (0.0375, 0.0612)  # 撤退按钮，用于打开退出确认浮层。
CLICK_SORTIE = (0.9375, 0.9264)  # 出征按钮，用于从地图进入决战战斗。
CLICK_FORMATION = (0.7292, 0.9264)  # 编队按钮，用于打开决战出征准备页。
CLICK_FLEET_REFRESH = (0.3959, 0.9264)  # 刷新按钮，用于刷新战备舰队选项。
CLICK_FLEET_CLOSE = (0.6042, 0.9264)  # 关闭按钮，用于退出战备舰队浮层。
CLICK_LEAVE = (0.3719, 0.5834)  # 暂离按钮，用于保存进度并离开决战。
CLICK_RETREAT_CONFIRM = (0.6250, 0.5556)  # 撤退确认按钮，用于清空决战进度。
CLICK_ADVANCE_CONFIRM = (0.5000, 0.8556)  # 前进确认按钮，用于提交路线选择。
CLICK_USE_LAST_FLEET_CONFIRM = (0.9094, 0.9264)  # 复用舰队确认按钮，用于恢复上次编队。
CLICK_REWARD_ACK = (0.9532, 0.9542)  # 奖励确认按钮，用于关闭结算奖励页面。
CLICK_SKILL = (0.2143, 0.8940)  # 副官技能按钮，用于打开技能获取舰船流程。
ADVANCE_CARD_POSITIONS = (
    (0.3000, 0.5000),  # 第一张前进卡片，用于选择左侧路线。
    (0.6500, 0.5000),  # 第二张前进卡片，用于选择右侧路线。
    (0.5000, 0.5000),  # 第三张前进卡片，用于选择中间路线。
)  # 前进卡片坐标，按界面显示顺序选择决战路线。


# 总览页和地图页视觉状态校准。
CHAPTER_NUM_AREA = (0.8180, 0.8100, 0.8750, 0.8670)  # 章节编号 OCR 区域，用于读取 Ex-N。
STAGE_CHECK_POINTS = {
    1: ((0.4115, 0.4019), (0.6604, 0.4630), (0.8396, 0.7093)),  # Ex-1 小关通过状态采样点。
    2: ((0.4354, 0.3852), (0.5792, 0.6648), (0.8187, 0.5889)),  # Ex-2 小关通过状态采样点。
    3: ((0.4219, 0.6648), (0.6531, 0.3944), (0.8042, 0.7444)),  # Ex-3 小关通过状态采样点。
    4: ((0.3810, 0.4360), (0.5960, 0.6360), (0.7780, 0.5210)),  # Ex-4 小关通过状态采样点。
    5: ((0.4180, 0.3780), (0.7600, 0.4770), (0.5500, 0.7500)),  # Ex-5 小关通过状态采样点。
    6: ((0.6060, 0.3750), (0.5320, 0.7030), (0.8620, 0.6440)),  # Ex-6 小关通过状态采样点。
}  # 章节到小关通过像素点的映射，用于读取当前小关进度。
STAGE_CHECK_COLOR = Color.of(250, 244, 253)  # 小关已通过颜色，用于识别章节进度。
STAGE_CHECK_TOLERANCE = 30.0  # 小关颜色容差，用于兼容截图渲染差异。


# 战备舰队 OCR 区域和点击坐标。
FLEET_CARD_X_POSITIONS = (
    0.2500,
    0.3750,
    0.5000,
    0.6250,
    0.7500,
)  # 战备舰队卡片横坐标，用于定位可购买项。
FLEET_CARD_CLICK_Y = 0.5000  # 战备舰队卡片点击纵坐标，用于购买选中的舰船卡片。
SHIP_NAME_X_RANGES = (
    (0.1950, 0.3050),  # 第一张舰船卡片名称 OCR 横向区域。
    (0.3180, 0.4290),  # 第二张舰船卡片名称 OCR 横向区域。
    (0.4450, 0.5550),  # 第三张舰船卡片名称 OCR 横向区域。
    (0.5710, 0.6770),  # 第四张舰船卡片名称 OCR 横向区域。
    (0.6950, 0.8050),  # 第五张舰船卡片名称 OCR 横向区域。
)  # 舰船卡片名称 OCR 横向区域，用于按卡片顺序读取舰船名称。
SHIP_NAME_Y_RANGE = (0.6850, 0.7150)  # 舰船名称 OCR 纵向区域，用于裁剪卡片名称。
COST_AREA = ((0.1950, 0.8080), (0.8050, 0.7640))  # 战备舰队费用 OCR 区域，用于读取卡片消耗。
RESOURCE_AREA = ((0.9110, 0.0820), (0.9740, 0.0370))  # 决战资源 OCR 区域，用于读取可用分数。
SKILL_SHIP_AREA = (0.2600, 0.6850, 0.7400, 0.7150)  # 技能获得舰船 OCR 区域，用于读取技能结果。


# 决战地图节点识别校准。
SHIP_HSV_LO = (18, 100, 200)  # 舰船图标 HSV 下界，用于定位地图上的舰船指示器。
SHIP_HSV_HI = (32, 180, 255)  # 舰船图标 HSV 上界，用于定位地图上的舰船指示器。
SHIP_MIN_AREA = 500  # 舰船图标最小连通区域，用于过滤地图背景噪声。
NODE_CROP_OFFSET = (-0.0300, 0.0120)  # 节点标题裁剪偏移，用于截取地图节点字母。


# 页面和浮层视觉签名。
SIG_FLEET_ACQUISITION = PixelSignature(
    name='decisive_fleet_acquisition',
    rules=(
        PixelRule.of(0.5305, 0.1014, (254, 254, 254)),  # 浮层标题左侧白色像素。
        PixelRule.of(0.4031, 0.1028, (255, 252, 255)),  # 浮层标题中部白色像素。
        PixelRule.of(0.4492, 0.1181, (254, 254, 254)),  # 浮层标题下方白色像素。
    ),
    strategy=MatchStrategy.ALL,
)  # 战备舰队获取浮层签名，用于确认购买页面。
SIG_CONFIRM_EXIT = PixelSignature(
    name='decisive_confirm_exit',
    rules=(
        PixelRule.of(0.3430, 0.5667, (29, 124, 214)),  # 暂离按钮左侧蓝色像素。
        PixelRule.of(0.4180, 0.5694, (29, 124, 214)),  # 暂离按钮右侧蓝色像素。
        PixelRule.of(0.5813, 0.5667, (152, 36, 36)),  # 撤退按钮左侧红色像素。
        PixelRule.of(0.6578, 0.5639, (156, 38, 38)),  # 撤退按钮右侧红色像素。
        PixelRule.of(0.4953, 0.4875, (225, 225, 225)),  # 退出对话框灰色背景像素。
        PixelRule.of(0.5023, 0.2819, (7, 117, 194)),  # 退出对话框标题蓝色像素。
    ),
    strategy=MatchStrategy.ALL,
)  # 退出确认浮层签名，用于区分暂离和撤退操作。
SIG_ADVANCE_CHOICE = PixelSignature(
    name='decisive_advance_choice',
    rules=(
        PixelRule.of(0.4484, 0.8333, (37, 146, 249)),  # 前进确认按钮左上像素。
        PixelRule.of(0.4484, 0.8833, (28, 136, 237)),  # 前进确认按钮左下像素。
        PixelRule.of(0.5492, 0.8306, (38, 147, 250)),  # 前进确认按钮右上像素。
        PixelRule.of(0.5516, 0.8833, (28, 136, 237)),  # 前进确认按钮右下像素。
        PixelRule.of(0.7008, 0.9028, (13, 49, 85)),  # 右侧编队按钮遮挡背景上方像素。
        PixelRule.of(0.7031, 0.9514, (9, 45, 79)),  # 右侧编队按钮遮挡背景下方像素。
        PixelRule.of(0.8695, 0.9042, (13, 49, 85)),  # 右侧出征按钮遮挡背景上方像素。
        PixelRule.of(0.8727, 0.9514, (9, 45, 79)),  # 右侧出征按钮遮挡背景下方像素。
    ),
    strategy=MatchStrategy.ALL,
)  # 前进路线选择浮层签名，用于确认路线选择页面。
SIG_MAP_PAGE = PixelSignature(
    name='decisive_map_page',
    rules=(
        PixelRule.of(0.0641, 0.0667, (218, 130, 20)),  # 地图左上撤退按钮橙色像素。
        PixelRule.of(0.7969, 0.9194, (34, 143, 246)),  # 地图编队按钮蓝色像素。
        PixelRule.of(0.9555, 0.9208, (34, 143, 246)),  # 地图出征按钮蓝色像素。
        PixelRule.of(0.7055, 0.9236, (34, 143, 246)),  # 地图技能按钮蓝色像素。
        PixelRule.of(0.1227, 0.0750, (215, 142, 14)),  # 地图左上撤退按钮右侧像素。
    ),
    strategy=MatchStrategy.ALL,
)  # 决战地图基础签名，用于确认无浮层地图状态。
SKILL_USED = PixelSignature(
    name='decisive_skill_used',
    rules=(
        PixelRule.of(0.1977, 0.9361, (245, 245, 245)),  # 技能按钮状态像素。
    ),
    strategy=MatchStrategy.ALL,
)  # 技能已使用签名，用于避免重复使用副官技能。


__all__ = [
    'ADVANCE_CARD_POSITIONS',
    'CHAPTER_NUM_AREA',
    'CLICK_ADVANCE_CONFIRM',
    'CLICK_BACK',
    'CLICK_BUY_CONFIRM',
    'CLICK_BUY_RESOURCE',
    'CLICK_BUY_TICKET_OPEN',
    'CLICK_CHOOSE_SHIP_BACK',
    'CLICK_ENTER_MAP',
    'CLICK_FLEET_CLOSE',
    'CLICK_FLEET_REFRESH',
    'CLICK_FORMATION',
    'CLICK_LEAVE',
    'CLICK_MAP_BACK',
    'CLICK_NEXT_CHAPTER',
    'CLICK_PREV_CHAPTER',
    'CLICK_RESET_CHAPTER',
    'CLICK_RETREAT_BUTTON',
    'CLICK_RETREAT_CONFIRM',
    'CLICK_REWARD_ACK',
    'CLICK_SKILL',
    'CLICK_SORTIE',
    'CLICK_USE_LAST_FLEET_CONFIRM',
    'COST_AREA',
    'FLEET_CARD_CLICK_Y',
    'FLEET_CARD_X_POSITIONS',
    'NODE_CROP_OFFSET',
    'RESOURCE_AREA',
    'SHIP_HSV_HI',
    'SHIP_HSV_LO',
    'SHIP_MIN_AREA',
    'SHIP_NAME_X_RANGES',
    'SHIP_NAME_Y_RANGE',
    'SIG_ADVANCE_CHOICE',
    'SIG_CONFIRM_EXIT',
    'SIG_FLEET_ACQUISITION',
    'SIG_MAP_PAGE',
    'SKILL_SHIP_AREA',
    'SKILL_USED',
    'STAGE_CHECK_COLOR',
    'STAGE_CHECK_POINTS',
    'STAGE_CHECK_TOLERANCE',
]
