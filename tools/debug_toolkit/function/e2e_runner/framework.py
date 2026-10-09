"""E2E 快速实机验证框架 — 基座 (E2ERunner)。

算法说明:
1. 目标: 把 "连接设备 → 准备任务上下文 → 执行操作 → 判定结果" 的重复劳动收敛成
   一个基座, 验证脚本 (case) 只写业务步骤本身, 实现 "加一个文件 = 多一个可跑的
   实机验证"。
2. 初始化: `--no-launch` 用 common.device 的 DeviceService 连接设备, 并绑定
   dispatch ContextHandle 交给 case (rt.ctx); 完整模式 (启动游戏并回到首页) 依赖
   navigation.goto_page 和 application.runtime.initialize 迁移到新栈, 尚未接通。
3. 步骤执行: rt.action(label, fn) 执行任意函数并计时; 正常时原样返回 fn 的返回
   值, 抛异常时记为失败、自动截图存证并返回 FAILED 哨兵, case 据此短路退出。
4. 断言: rt.check(label, fn) 把返回值当 bool 判定, 用于次数 / 状态核对。
5. 汇总: finalize(overall) 汇总所有步骤的通过 / 失败, 结合 case 整体返回值
   给出进程退出码 (0 = 全部通过), 供终端与 CI 直接判断。
"""

from __future__ import annotations

# 处理 Windows GBK 编码兼容性 (中文输出在默认代码页下可能乱码)
import sys
import time
from contextlib import ExitStack
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # noqa: S110
    pass  # reconfigure 不可用时继续使用默认编码


# ═══════════════════════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════════════════════


class _StaticFrameDevice:
    """静态截图设备替身：按调用方选定的截图返回画面。"""

    def __init__(self) -> None:
        self._frame: Any = None

    def use_frame(self, path: str | Path) -> None:
        """切换当前帧。

        Args:
            path: 外挂截图路径，允许位于仓库之外。

        Raises:
            FileNotFoundError: 截图无法读取或解码。
        """
        # 外挂截图必须用 cv2 直接读；仓库的文件读取接口只允许仓库内路径。
        import cv2
        import numpy

        frame = cv2.imdecode(numpy.fromfile(str(path), dtype=numpy.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            raise FileNotFoundError(f'静态截图无法读取: {path}')
        self._frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def screenshot(self) -> Any:
        """返回当前帧。

        Raises:
            RuntimeError: 尚未选定任何截图。
        """
        if self._frame is None:
            raise RuntimeError('静态帧尚未设置')
        return self._frame

    def disconnect(self) -> None:
        """静态替身不持有设备资源。"""


@dataclass
class StepRec:
    """单条步骤记录 (action / check 各记一条)。"""

    label: str  # 步骤描述 (中文, 显示给用户)
    ok: bool  # 是否通过 (action: 是否抛异常; check: 断言结果)
    duration_ms: int = 0  # 耗时 (毫秒)
    error: str | None = None  # 异常信息 (失败时)


@dataclass
class RunnerState:
    """E2ERunner 的步骤累计状态。"""

    steps: list[StepRec] = field(default_factory=list)

    @property
    def failed(self) -> int:
        """失败步骤数。"""
        return sum(1 for s in self.steps if not s.ok)


# ═══════════════════════════════════════════════════════════════════════════════
# 基座
# ═══════════════════════════════════════════════════════════════════════════════


class E2ERunner:
    """单个 E2E case 的执行基座。

    职责: 设备连接、任务上下文、步骤计时与记录、失败截图、汇总与退出码。
    case 只需调用 :meth:`action` / :meth:`check` / :meth:`note` 组织自己的步骤,
    并从 rt.ctx 拿到已绑定 runtime 的 dispatch ContextHandle。
    """

    # 失败哨兵: action 抛异常时返回它 (区别于业务返回值 None/False/空列表)
    FAILED = object()

    def __init__(
        self,
        case_name: str,
        case_args: Any,
        *,
        serial: str | None = None,
        config_path: str | None = None,
        debug: bool = False,
        no_launch: bool = False,
        static_frames: bool = False,
        with_ocr: bool = False,
    ) -> None:
        self.case_name = case_name
        self.args = case_args  # case 自己的参数 namespace (run.py 解析后传入)
        self.serial = serial  # ADB 序列号; None 时用 usersettings.yaml 配置
        self.config_path = config_path  # 配置文件路径; None 时自动检测
        self.debug = debug  # True 时日志级别 DEBUG
        self.no_launch = no_launch  # True 时跳过游戏就绪 (纯只读验证)
        self.static_frames = static_frames  # True 时用外挂截图离线验证 (不连接设备)
        self.with_ocr = with_ocr  # True 时初始化 OCR 引擎 (编队识别等需要)
        self.state = RunnerState()
        self.ctx: Any = None  # 已绑定的 dispatch ContextHandle (prepare() 成功后可用)
        self._runtime: Any = None  # RuntimeBindings: 设备、配置和 OCR 服务引用
        self._scope_stack: Any = None  # ExitStack: 持有本次运行的任务上下文作用域
        self._launcher: Any = None  # 已连接的设备服务
        self._cleanup_done = False
        # 每次运行独立目录: logs/e2e_tools/<case>/<时间戳>
        stamp = datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')
        self.log_dir = Path('logs/e2e_tools') / case_name / stamp

    # ── 初始化 ─────────────────────────────────────────────────────

    def prepare(self) -> bool:
        """连接设备并准备本次运行的任务上下文。

        ``no_launch=True`` 只连接设备并绑定 dispatch Context, 供截图、页面识别和
        checker 验证使用。完整模式需要启动游戏并回到首页, 依赖尚未迁移完成的
        ``navigation.goto_page`` 和 ``application.runtime.initialize``。
        """
        if self.static_frames:
            return self._prepare_static_frames()
        if self.no_launch:
            return self._prepare_readonly()

        # TODO: 完整实机链路 (启动游戏 → 回到首页 → 执行 case) 依赖
        # navigation.goto_page 与 application.runtime.initialize 迁移到新栈。
        # 影响范围: 所有不使用 --no-launch 的 case。删除条件: 上述两个入口在新栈
        # 可用后, 按 _prepare_readonly 的方式组装 runtime 并在本分支续接游戏就绪。
        error = '完整实机链路未接通: 依赖 navigation.goto_page (导航器重写第 2 步)'
        self._record('准备运行环境', ok=False, error=error)
        print(f'  [FAIL] {error}; 只读验证请加 --no-launch')
        return False

    def _prepare_readonly(self) -> bool:
        """连接设备并绑定 dispatch 任务上下文 (不启动游戏、不执行页面操作)。"""
        from autowsgr.common.device.config import DeviceConfig
        from autowsgr.common.device.service import DeviceService
        from autowsgr.dispatch.context import ContextTemplate, RuntimeBindings, context

        self._launcher = DeviceService(
            DeviceConfig(ADB_CONNECTION=self.serial) if self.serial else DeviceConfig(),
        )
        try:
            info = self._launcher.connect()
        except Exception as exc:
            self._record('连接设备', ok=False, error=str(exc))
            print(f'  [FAIL] 设备连接失败: {exc}')
            return False

        # 只读模式没有可用的生产配置和 OCR 引擎 (autowsgr.config 与 OCREngine 仍在
        # 迁移中), 只读 case 只消费设备服务; 需要配置或 OCR 的 case 等其链路迁移后再接。
        self._bind_task_context(self._launcher)
        if self.with_ocr:
            self.note('只读模式不初始化 OCR: 新栈 OCR 入口迁移中, 该参数当前被忽略')
        print(f'  [OK] 设备已连接: {info.serial} {info.resolution[0]}x{info.resolution[1]}')
        return True

    def _prepare_static_frames(self) -> bool:
        """用静态截图替身准备离线验证 (不连接设备、不启动游戏)。"""
        self._launcher = _StaticFrameDevice()
        self._bind_task_context(self._launcher)
        print('  [OK] 静态帧模式: 使用外挂截图, 不连接设备')
        return True

    def _bind_task_context(self, ctrl: Any) -> None:
        """绑定本次运行的 dispatch 任务上下文。

        Args:
            ctrl: 已就绪的运行时设备引用。
        """
        from autowsgr.dispatch.context import ContextTemplate, RuntimeBindings, context

        # 只读运行没有生产配置和 OCR 引擎可注入, 只消费设备引用。
        self._runtime = RuntimeBindings(ctrl=ctrl, config=None, ocr=None, ship_ocr=None)
        self._scope_stack = ExitStack()
        self._scope_stack.enter_context(
            context.bind(
                f'e2e:{self.case_name}',
                template=ContextTemplate.for_task('navigation_checker'),
                runtime=self._runtime,
            ),
        )
        self.ctx = context.request()

    # ── 步骤 API (case 调用) ───────────────────────────────────────

    def use_frame(self, path: str | Path) -> None:
        """切换静态验证使用的截图。

        Args:
            path: 外挂截图路径; 换机器或换活动时由 case 指定。

        Raises:
            RuntimeError: 当前不是静态帧模式。
        """
        if not isinstance(self._launcher, _StaticFrameDevice):
            raise RuntimeError('只有静态帧模式可以切换截图')
        self._launcher.use_frame(path)

    def action(self, label: str, fn: Any, /, *args: Any, **kwargs: Any) -> Any:
        """执行一个操作步骤。

        正常返回 fn 的返回值; 抛异常时记录失败、自动截图、返回 ``rt.FAILED``。
        case 约定写法::

            results = rt.action('跑常规战', run_normal_fight_from_yaml, ctx, '1-1')
            if results is rt.FAILED:
                return False
        """
        t0 = time.monotonic()
        try:
            value = fn(*args, **kwargs)
        except Exception as exc:
            self._record(label, ok=False, error=str(exc), t0=t0)
            print(f'  [FAIL] {label}: {exc}')
            self._error_screenshot(label)
            return self.FAILED
        self._record(label, ok=True, t0=t0)
        print(f'  [OK] {label} ({self._ms_since(t0)}ms)')
        return value

    def check(self, label: str, fn: Any, /, *args: Any, **kwargs: Any) -> bool:
        """断言步骤: 把 fn 返回值当 bool 判定, 打印 PASS/FAIL。"""
        t0 = time.monotonic()
        try:
            passed = bool(fn(*args, **kwargs))
            error: str | None = None
        except Exception as exc:
            passed = False
            error = str(exc)
        self._record(label, ok=passed, error=error, t0=t0)
        mark = 'PASS' if passed else 'FAIL'
        suffix = f': {error}' if error else ''
        print(f'  [{mark}] {label}{suffix}')
        return passed

    def note(self, msg: str) -> None:
        """打印一条说明信息 (不计入步骤, 不影响判定)。"""
        print(f'  [i] {msg}')

    # ── 兜底与汇总 ─────────────────────────────────────────────────

    def unexpected(self, exc: Exception) -> None:
        """case 主体自身抛出的未捕获异常兜底 (记为一条失败步骤)。"""
        self._record(f'case 异常 ({type(exc).__name__})', ok=False, error=str(exc))
        print(f'  [FAIL] case 异常: {exc}')
        self._error_screenshot('case_crash')

    def finalize(self, *, overall: bool = True) -> int:
        """先释放运行资源，再打印汇总并返回进程退出码。"""
        self.cleanup()
        total = len(self.state.steps)
        failed = self.state.failed
        print()
        print('═' * 68)
        for i, s in enumerate(self.state.steps, 1):
            mark = 'OK  ' if s.ok else 'FAIL'
            dur = f'{s.duration_ms}ms' if s.duration_ms else ''
            err = f'  ← {s.error}' if s.error else ''
            print(f'  [{mark}] [{i:02d}] {s.label}  {dur}{err}')
        verdict = 'PASS' if (failed == 0 and overall) else 'FAIL'
        print()
        print(f'  {self.case_name}: {total} 步, 失败 {failed} 步 → {verdict}')
        print(f'  日志目录: {self.log_dir.resolve()}')
        print('═' * 68)
        return 0 if verdict == 'PASS' else 1

    def cleanup(self) -> None:
        """无论 case 结果如何，关闭任务上下文并释放设备连接。"""
        if self._cleanup_done:
            return
        self._cleanup_done = True

        # 先退出任务上下文作用域, 再断开设备, 避免残留绑定阻塞下一次 bind。
        if self._scope_stack is not None:
            self._scope_stack.close()
            self._scope_stack = None

        if self._launcher is None:
            return
        try:
            self._launcher.disconnect()
        except Exception as exc:
            self._record('清理: 断开设备', ok=False, error=str(exc))
            print(f'  [FAIL] 清理: 断开设备: {exc}')

    # ── 内部工具 ───────────────────────────────────────────────────

    @staticmethod
    def _ms_since(t0: float) -> int:
        return int((time.monotonic() - t0) * 1000)

    def _record(
        self,
        label: str,
        *,
        ok: bool,
        error: str | None = None,
        t0: float | None = None,
    ) -> None:
        self.state.steps.append(
            StepRec(
                label=label,
                ok=ok,
                duration_ms=self._ms_since(t0) if t0 is not None else 0,
                error=error,
            )
        )

    def _error_screenshot(self, label: str) -> None:
        """失败时自动截图存证 (截图本身失败则静默跳过)。"""
        if self._runtime is None or self._runtime.ctrl is None:
            return
        try:
            # 失败分支才需要图片工具，避免普通 runner 导入时加载图像编码依赖。
            from tools.debug_toolkit.function.screenshot import save_image

            screen = self._runtime.ctrl.screenshot()
            tag = f'e2e_fail_{label.replace(" ", "_")[:40]}'
            path = save_image(screen, tag=tag, img_dir=self.log_dir / 'images')
            if path:
                print(f'        失败截图: {path}')
        except Exception:  # noqa: S110
            pass
