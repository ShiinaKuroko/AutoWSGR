from autowsgr.application.ui.navigation.route_manage import RouteManage
from autowsgr.application.ui.navigation.page_checker.home_checker import check_home_page
from autowsgr.application.ui.navigation.page_checker.sortie_checker import check_sortie_page
from autowsgr.application.ui.navigation.types import PageName


def test_registered_paths_and_route_methods() -> None:
    assert RouteManage.get_paths() == (
        ('主页 → 出征页', (PageName.HOME, PageName.SORTIE_MAP)),
        ('出征页 → 主页', (PageName.SORTIE_MAP, PageName.HOME)),
    )
    assert RouteManage.get_route_methods((PageName.HOME, PageName.SORTIE_MAP, PageName.HOME)) == (
        ('主页 → 出征页', PageName.HOME, PageName.SORTIE_MAP, 'navigate_to', check_sortie_page),
        ('出征页 → 主页', PageName.SORTIE_MAP, PageName.HOME, 'go_back', check_home_page),
    )
    assert RouteManage.get_route_methods((PageName.HOME, PageName.BATH)) == ()
