"""演习准备页导航节点的无设备回归。"""

from autowsgr.infra.ui.navigation.graph import find_path
from autowsgr.infra.ui.navigation.registry import get_registered_pages, register_default_pages
from autowsgr.types import PageName


def test_battle_preparation_is_registered_and_returns_via_map() -> None:
    register_default_pages()
    assert PageName.BATTLE_PREP.value in get_registered_pages()

    path = find_path(PageName.BATTLE_PREP.value, PageName.MAIN.value)

    assert path is not None
    assert [edge.target for edge in path] == [PageName.MAP, PageName.MAIN]
