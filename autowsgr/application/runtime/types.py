"""运行时和应用配置类型。"""

from __future__ import annotations

from autowsgr.common.system.enums import StrEnum


class LoginServer(StrEnum):
    """登录时可选择的区服。

    'default' 表示不处理换区；其余取值与游戏内区服名一致，用于 OCR 定位。
    """

    default = '默认'
    hood = '胡德'
    bismarck = '俾斯麦'
    quincy = '昆西'
    changchun = '长春'


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
