"""模块功能：维护登录前启动画面的页面坐标和像素签名。

上层调用：
- application.ui.controller.login.page：检查启动画面并执行进入游戏点击。

下层依赖：
- common.vision：提供像素规则和像素签名数据类型。

本模块只保存启动画面的静态页面校准，不保存设备对象、上下文或运行状态。
"""

from autowsgr.common.vision import PixelRule, PixelSignature


CLICK_ENTER = (0.8915, 0.8584)  # 启动画面右下角进入按钮，用于进入游戏主流程。

PAGE_SIGNATURE = PixelSignature(
    name='启动画面',
    rules=(
        PixelRule.of(0.0508, 0.8722, (204, 210, 208), tolerance=30.0),  # 底部横幅左侧灰色锚点。
        PixelRule.of(0.8125, 0.8569, (224, 183, 41), tolerance=30.0),  # 底部横幅黄色锚点。
        PixelRule.of(0.8695, 0.9028, (222, 198, 40), tolerance=30.0),  # 底部横幅中部黄色锚点。
        PixelRule.of(0.9641, 0.8681, (222, 197, 43), tolerance=30.0),  # 底部横幅右侧黄色锚点。
        PixelRule.of(0.7914, 0.7333, (237, 237, 237), tolerance=30.0),  # 启动画面内容区浅色锚点。
    ),
)  # 启动画面像素签名，用于点击进入前确认页面状态。


__all__ = ['CLICK_ENTER', 'PAGE_SIGNATURE']
