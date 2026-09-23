"""验证活动地图页面控制器的无设备单元测试。

上层调用：
- pytest：执行活动地图页面识别、操作和返回测试。

下层依赖：
- application.ui.controller.home.event_page：提供活动地图页面控制器。
- common.vision：提供测试用的图像匹配结果类型。

本模块只使用 mock 验证页面行为，不连接真实设备或修改运行时数据。
"""

from __future__ import annotations

from itertools import count
from unittest.mock import MagicMock, call

import numpy
import pytest

from autowsgr.application.ui.controller.home.event_page import (
    BaseEventPage,
    constants,
    recognition,
)
from autowsgr.common.system.exceptions import ActionFailedError
from autowsgr.common.types import PageName
from autowsgr.common.device.interaction import NavigationError
from autowsgr.common.vision import ImageMatchDetail
from autowsgr.common.vision.resources.pages import event


def _gradient_screen(lo: int = 80, hi: int = 180) -> numpy.ndarray:
    """连续渐变图 (模拟真实 UI 背景)。"""
    xs = numpy.tile(numpy.linspace(0, 1, 960), (540, 1))
    return ((lo + xs * (hi - lo))[:, :, None].repeat(3, 2)).astype(numpy.uint8)


def _button_detail(confidence: float = 0.9) -> ImageMatchDetail:
    """构造出击按钮匹配结果。"""
    return ImageMatchDetail(
        template_name='fight_button',
        confidence=confidence,
        center=(0.83, 0.84),
        top_left=(0.78, 0.80),
        bottom_right=(0.88, 0.88),
    )


def _make_page() -> tuple[BaseEventPage, MagicMock]:
    """构造一个绑定 mock 控制器的 BaseEventPage。"""
    ctx = MagicMock()
    page = BaseEventPage(ctx, event_name='20260730')
    return page, ctx.ctrl


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """屏蔽真实 sleep, 加速 _select_node/go_back 的等待循环。"""
    monkeypatch.setattr(
        'autowsgr.application.ui.controller.home.event_page.page.time.sleep', lambda *_: None
    )


def _mock_fight_button(
    monkeypatch: pytest.MonkeyPatch, details: list[ImageMatchDetail | None]
) -> None:
    """按帧序列 mock 出击按钮匹配 (None = 按钮不可见/浮层未开)。"""
    monkeypatch.setattr(
        recognition,
        'read_fight_button_detail',
        MagicMock(side_effect=details),
    )


# ── 页面识别锚点 ─────────────────────────────────────────────────────────────


class TestCheckCurrentPage:
    """验证活动地图页面的多层页面锚点。"""

    def test_fight_button_means_overlay_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """出击按钮可见 → 浮层态也算活动页 (战后 goto_page(EVENT_MAP) 不失败)。"""
        _mock_fight_button(monkeypatch, [_button_detail()])
        result = BaseEventPage.check_current_page(_gradient_screen())
        assert result.matched
        assert result.score == pytest.approx(0.9)

    def test_difficulty_icon_means_clean_page(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """难度图标可见 (无出击按钮) → 干净活动页。"""
        _mock_fight_button(monkeypatch, [None])
        monkeypatch.setattr(
            recognition,
            'read_difficulty_icon_state',
            MagicMock(return_value='H'),
        )
        result = BaseEventPage.check_current_page(_gradient_screen())
        assert result.matched

    def test_title_fallback_below_anchors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """按钮/图标都不可见, 标题命中 → 兜底 matched, 但 score 低于锚点层。"""
        _mock_fight_button(monkeypatch, [None])
        monkeypatch.setattr(
            recognition,
            'read_difficulty_icon_state',
            MagicMock(return_value=None),
        )

        monkeypatch.setattr(
            recognition,
            'read_event_title_match',
            MagicMock(return_value=None),
        )
        # 标题模板为空 → find_any 返回 None → 不匹配（新活动未截标题图的场景）。
        result = BaseEventPage.check_current_page(_gradient_screen())
        assert not result.matched

    def test_no_anchor_no_match(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """三层锚点全不命中 → 不是活动页。"""
        _mock_fight_button(monkeypatch, [None])
        monkeypatch.setattr(
            recognition,
            'read_difficulty_icon_state',
            MagicMock(return_value=None),
        )
        result = BaseEventPage.check_current_page(_gradient_screen())
        assert not result.matched
        assert result.name == str(PageName.EVENT_MAP)

    def test_fight_button_template_ignores_preparation_title_position(self) -> None:
        """准备页标题不得被当作活动浮层按钮。"""
        template = event.event_fight_button_templates()[0].image
        screen = numpy.zeros((540, 960, 3), dtype=numpy.uint8)
        screen[12 : 12 + template.shape[0], 12 : 12 + template.shape[1]] = template
        assert recognition.read_fight_button_detail(screen) is None

        screen[430 : 430 + template.shape[0], 720 : 720 + template.shape[1]] = template
        detail = recognition.read_fight_button_detail(screen)
        assert detail is not None
        assert detail.center[0] > 0.7
        assert detail.center[1] > 0.7


# ── 难度切换流程 ─────────────────────────────────────────────────────────────


class TestSelectDifficulty:
    def test_retry_failure_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """两次点击后仍未进入目标难度 → 明确报告切换失败。"""
        page, ctrl = _make_page()
        monkeypatch.setattr(
            page,
            '_read_difficulty',
            MagicMock(side_effect=['H', 'H', 'H']),
        )

        with pytest.raises(ActionFailedError):
            page._select_difficulty('E')

        assert ctrl.click.call_count == 2


# ── 节点选择流程 ─────────────────────────────────────────────────────────────


class TestSelectNode:
    def test_invalid_node_rejected_before_click(self) -> None:
        """节点编号不在当前布局中 → 直接拒绝，不触碰设备。"""
        page, ctrl = _make_page()

        with pytest.raises(ValueError, match='无效的活动地图节点'):
            page._select_node(99)

        ctrl.click.assert_not_called()

    def test_success_detects_fight_button(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """点击节点后出击按钮出现 → 选择成功, 第 1 次复查即停。"""
        page, ctrl = _make_page()
        _mock_fight_button(monkeypatch, [_button_detail()])

        page._select_node(1)

        x, y = constants.NODE_POSITIONS_BY_EVENT['20260730'][1]
        ctrl.click.assert_called_once_with(x, y)
        assert ctrl.screenshot.call_count == 1

    def test_failure_raises_when_button_never_appears(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """按钮始终不出现 (浮层未弹出) → 循环耗尽 → ActionFailedError。"""
        page, ctrl = _make_page()
        _mock_fight_button(monkeypatch, [None] * 10)

        with pytest.raises(ActionFailedError):
            page._select_node(1)
        assert ctrl.screenshot.call_count == 10


# ── 入口切换流程 ─────────────────────────────────────────────────────────────


class TestSelectEntrance:
    def test_success_confirms_target_entrance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """点击入口后确认目标入口状态。"""
        page, ctrl = _make_page()
        monkeypatch.setattr(
            recognition,
            'read_alpha_entrance_state',
            MagicMock(side_effect=[False, True]),
        )

        page._select_entrance('alpha')

        ctrl.click.assert_called_once_with(*constants.CLICK_ENTRANCE_ALPHA)

    def test_failure_raises_when_target_entrance_is_not_visible(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """点击入口后未确认目标状态时抛出异常。"""
        page, ctrl = _make_page()
        monkeypatch.setattr(
            recognition,
            'read_alpha_entrance_state',
            MagicMock(side_effect=[True, True]),
        )

        with pytest.raises(ActionFailedError):
            page._select_entrance('beta')

        ctrl.click.assert_called_once_with(*constants.CLICK_ENTRANCE_BETA)


# ── 页面返回流程 ─────────────────────────────────────────────────────────────


class TestGoBack:
    def test_already_at_main_returns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """已在主页面 → 直接返回, 不点击。"""
        page, ctrl = _make_page()
        monkeypatch.setattr(
            'autowsgr.application.ui.controller.home.main_page.HomePage.check_current_page',
            MagicMock(return_value=True),
        )

        page.go_back()

        ctrl.click.assert_not_called()

    def test_overlay_visible_closes_first(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """出击按钮可见 (关卡浮层在) → 点红色 X 而非点返回, 下轮到达主页。"""
        page, ctrl = _make_page()
        frame = _gradient_screen()
        main_frame = _gradient_screen(lo=200, hi=210)
        # 第一帧按钮可见 (浮层在) → 点 X; 第二帧干净 → 点返回; 轮询帧到主页
        ctrl.screenshot.side_effect = [frame, frame, main_frame]
        _mock_fight_button(monkeypatch, [_button_detail(), None])
        monkeypatch.setattr(
            'autowsgr.application.ui.controller.home.main_page.HomePage.check_current_page',
            MagicMock(side_effect=[False, False, True]),
        )

        page.go_back()

        assert ctrl.click.call_args_list == [
            call(*constants.CLICK_CLOSE_NODE_OVERLAY),
            call(*constants.CLICK_BACK),
        ]

    def test_back_effective_single_click(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """干净页点返回生效, 轮询窗口内到主页 → 只点一次返回 (防连点过冲)。"""
        page, ctrl = _make_page()
        frame = _gradient_screen()
        main_frame = _gradient_screen(lo=200, hi=210)
        # 第一帧干净 → 点返回; 轮询帧到主页 → 返回
        ctrl.screenshot.side_effect = [frame, main_frame]
        _mock_fight_button(monkeypatch, [None])
        monkeypatch.setattr(
            'autowsgr.application.ui.controller.home.main_page.HomePage.check_current_page',
            MagicMock(side_effect=[False, True]),
        )

        page.go_back()

        assert ctrl.click.call_args_list == [call(*constants.CLICK_BACK)]

    def test_timeout_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """始终不在主页且无浮层 → 15s 超时 → NavigationError。"""
        page, ctrl = _make_page()
        ctrl.screenshot.return_value = _gradient_screen()
        monkeypatch.setattr(
            'autowsgr.application.ui.controller.home.main_page.HomePage.check_current_page',
            MagicMock(return_value=False),
        )
        monkeypatch.setattr(
            recognition,
            'read_fight_button_detail',
            MagicMock(return_value=None),
        )
        # time.sleep 已被 _no_sleep 屏蔽; mock monotonic 递增驱动超时
        monkeypatch.setattr(
            'autowsgr.application.ui.controller.home.event_page.page.time.monotonic',
            MagicMock(side_effect=count(0, 1)),
        )

        with pytest.raises(NavigationError):
            page.go_back()


# ── 节点详情浮层 ─────────────────────────────────────────────────────────────


class TestCloseNodeOverlay:
    """验证节点详情浮层的关闭流程。"""

    def test_clean_page_noop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """出击按钮不可见 → 已是干净页, 不点击。"""
        page, ctrl = _make_page()
        ctrl.screenshot.return_value = _gradient_screen()
        _mock_fight_button(monkeypatch, [None])

        page._close_node_overlay()

        ctrl.click.assert_not_called()

    def test_overlay_closed_then_button_gone(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """按钮可见 (浮层在) → 点 X 后按钮消失 → 关闭成功, 只点一次。"""
        page, ctrl = _make_page()
        _mock_fight_button(monkeypatch, [_button_detail(), None])

        page._close_node_overlay()

        assert ctrl.click.call_args_list == [call(*constants.CLICK_CLOSE_NODE_OVERLAY)]

    def test_gives_up_after_three_rounds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """按钮一直可见 (点 X 无效) → 3 轮后放弃。"""
        page, ctrl = _make_page()
        _mock_fight_button(monkeypatch, [_button_detail()] * 4)

        with pytest.raises(ActionFailedError):
            page._close_node_overlay()

        assert ctrl.click.call_count == 3
