"""infra.base.constants.coordinates 坐标加载器的无设备单元测试。

硬约束: YAML 文件格式不可变 (键 + [x, y] 绝对像素 + 注释),
加载器只负责读取与归一化 (1280x720 → 0-1 相对坐标)。
"""

from __future__ import annotations

import pytest

from autowsgr.infra.base.constants import coordinates


class TestPoint:
    """point() 归一化坐标获取。"""

    def test_login_enter_game_normalizes(self) -> None:
        """login.enter_game [1141, 618] → 归一化相对坐标。"""
        x, y = coordinates.point('login', 'enter_game')
        assert abs(x - 1141 / 1280) < 1e-9
        assert abs(y - 618 / 720) < 1e-9

    def test_common_back(self) -> None:
        """main.backyard.back [64, 47] (原 common.back 并入) → 归一化。"""
        x, y = coordinates.point('main', 'backyard.back')
        assert abs(x - 64 / 1280) < 1e-9
        assert abs(y - 47 / 720) < 1e-9

    def test_main_backyard_back_home(self) -> None:
        """main.backyard.back_home [168, 49] 返回首页 (仅后院二级页面)。"""
        x, y = coordinates.point('main', 'backyard.back_home')
        assert abs(x - 168 / 1280) < 1e-9
        assert abs(y - 49 / 720) < 1e-9

    def test_nested_key_servers(self) -> None:
        """嵌套键 servers.hood 可通过点号路径访问。"""
        x, y = coordinates.point('login', 'servers.hood')
        assert abs(x - 1056 / 1280) < 1e-9
        assert abs(y - 58 / 720) < 1e-9

    def test_main_backyard_nested(self) -> None:
        """main.backyard 树: 后院建筑用嵌套路径访问 (如 backyard.dormitory)。"""
        x, y = coordinates.point('main', 'backyard.dormitory')
        assert abs(x - 148 / 1280) < 1e-9
        assert abs(y - 447 / 720) < 1e-9

    def test_main_backyard_enter(self) -> None:
        """main.backyard.enter = 首页 → 后院入口按钮。"""
        x, y = coordinates.point('main', 'backyard.enter')
        assert abs(x - 62 / 1280) < 1e-9
        assert abs(y - 112 / 720) < 1e-9

    def test_main_menu_nested(self) -> None:
        """main.menu 树: 侧边栏展开后的菜单项。"""
        x, y = coordinates.point('main', 'menu.build')
        assert abs(x - 200 / 1280) < 1e-9
        assert abs(y - 267 / 720) < 1e-9

    def test_missing_page_raises(self) -> None:
        """页面文件不存在 → KeyError。"""
        with pytest.raises(KeyError, match='坐标文件不存在'):
            coordinates.point('nope', 'back')

    def test_missing_key_raises(self) -> None:
        """坐标键不存在 → KeyError。"""
        with pytest.raises(KeyError, match='坐标键不存在'):
            coordinates.point('login', 'no_such_key')
