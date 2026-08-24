"""初始化链路 — 执行器的永远第一步。

终态契约: 任意状态 → [首页 + 浮层已清 + 待机]。

    initialize.py  主链路: 三分支判定 + SL 兜底
    overlays.py    每日浮层 (日期门控, 任务级状态)
    updater.py     游戏更新检测 (空实现占位)

入口调用::

    from autowsgr.business.system.initialize.initialize import initialize

    initialize(ctx)
"""
