"""UI 域 — 游戏界面操作与导航的基础能力。

完整导航图的三零件 (节点 + 边 + 总目录):

    pages/          各页面: 识别签名 + 页内操作 (节点)
    navigation.py   导航图 find_path (边, 未来从 ui/navigation.py 迁入)
    registry.py     页面注册中心 (总目录, 未来从 ui/page.py 迁入)

分层关系:
    business/ 各链路 → goto_page (导航入口, 在 business/system/navigate)
    → 本域查图找路 → pages/ 各页面控制器执行点击

坐标数据源: infra/base/constants/coordinates/ (YAML 单一来源)。
"""
