"""页面操作库 — 游戏各页面的识别与页内操作 (导航图的节点)。

每个页面包 = 识别签名 + 页内点击操作,
被 business/ 各链路经 goto_page 调用, 不直接对 dispatch 暴露:

    main_page/      主页面 (母港): 识别 + 浮层 + 页内导航
    start_screen.py 启动画面: 识别 + 点击进入

坐标数据源: infra/base/constants/coordinates/ (YAML 单一来源),
本包内不再硬编码坐标值。
"""
