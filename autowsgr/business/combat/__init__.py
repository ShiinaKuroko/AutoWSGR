"""业务实现 · 战斗领域 — 与战斗相关的业务定义。

# TODO: 兼容期入口，旧战斗子系统迁移完成后按新结构重写本文件。
# 保留原因：原聚合重导出链（application.combat / business.combat.runner）依赖已删除的旧 vision API，
#   迁移前无法导入；E2E 联调只需要 business.combat.types，不能让包入口把它一起拖垮。
# 影响范围：from autowsgr.business.combat import X 的 19 处调用方会 ImportError，
#   迁移时改为从各自子模块直接导入。
# 删除条件：旧战斗子系统迁移完成、调用方全部改到新入口后，删除本 TODO 并按新结构重写。

当前成员:
    campaign/      战役链路 (固定槽位编队)
    decisive/      决战链路 (独立阶段状态机)
    exercise/      演习链路
    bettle/        普通出征 + 活动战 (多节点地图)
    types.py       战斗与舰队领域类型
    plan.py        战斗计划与节点决策
    rules.py       规则引擎
    runner.py      战斗业务运行入口
"""

from __future__ import annotations
