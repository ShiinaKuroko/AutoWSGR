"""运行时和应用配置类型。"""

from __future__ import annotations

from autowsgr.common.system.enums import StrEnum


class GameAPP(StrEnum):
    """游戏渠道服。"""

    official = '官服'
    xiaomi = '小米'
    tencent = '应用宝'

    @property
    def package_name(self) -> str:
        """返回 Android 包名。"""
        match self:
            case GameAPP.official:
                return 'com.huanmeng.zhanjian2'
            case GameAPP.xiaomi:
                return 'com.hoolai.zjsnr.mi'
            case GameAPP.tencent:
                return 'com.tencent.tmgp.zhanjian2'
            case _:
                raise ValueError(f'没有为 {self} 设置包名，请手动指定')
