"""执行 Scrcpy 视频、控制和输入能力。

直接调用方：device_engine 的设备连接、截图和操作流程。
下层依赖：设备配置、操作时序、system.logger、已连接的 ADB 设备、Scrcpy server 和 PyAV。
边界：只维护一个 Scrcpy 执行器实例的通道与 I/O，不负责 ADB 会话或业务流程。
"""

from __future__ import annotations

import socket
import struct
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from autowsgr.common.device.config import DeviceConfig
from autowsgr.common.device.device_engine.foundation.delay import (
    calculate_operation_delay,
    configure_operation_delay_bounds,
)
from autowsgr.common.device.errors import DeviceConnectionError
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    import numpy
    from adbutils import AdbConnection, AdbDevice


_log = get_logger('device.engine.scrcpy')

# ── scrcpy 资源 ─────────────────────────────────────────────────────────────

# Scrcpy server 与执行代码由 scrcpy_engine 私有持有。
_SCRCPY_ENGINE_DIR = Path(__file__).resolve().parent
_SCRCPY_SERVER_FILE = _SCRCPY_ENGINE_DIR / 'scrcpy-server.jar'
_SCRCPY_SERVER_VERSION = '5.0.1'
_DEVICE_JAR_PATH = '/data/local/tmp/scrcpy-server.jar'

# ── scrcpy 控制协议 ─────────────────────────────────────────────────────────

# 协议常量对应 scrcpy 5.0.1 的 control_msg.h / control_msg.c。

# 控制消息类型。
_TYPE_INJECT_KEYCODE = 0
_TYPE_INJECT_TEXT = 1
_TYPE_INJECT_TOUCH_EVENT = 2
_TYPE_SET_CLIPBOARD = 9

# SET_CLIPBOARD 文本上限。
_CLIPBOARD_TEXT_MAX_LENGTH_BYTES = (1 << 18) - 14

# Android MotionEvent 动作码。
_ACTION_DOWN = 0
_ACTION_UP = 1
_ACTION_MOVE = 2

# Android KeyEvent 动作码。
_KEY_ACTION_DOWN = 0
_KEY_ACTION_UP = 1

# 触摸事件使用的 pointer id。
# scrcpy 中 SC_POINTER_ID_GENERIC_FINGER = UINT64_C(-2)，
# 作为有符号 int64 写入 q 格式即 -2，对应无符号 0xFFFFFFFFFFFFFFFE。
_POINTER_ID_FINGER = -2

# ── 流和输入参数 ────────────────────────────────────────────────────────────

# 同一手势内相邻控制消息之间的最小间隔。
_GESTURE_EVENT_INTERVAL_SECONDS = 0.01
_SCRCPY_CHANNEL_CONNECT_ATTEMPTS = 30
_SCRCPY_CHANNEL_RETRY_DELAY_SECONDS = 0.1
_SCRCPY_SERVER_START_DELAY_SECONDS = 0.5
_DECODER_JOIN_TIMEOUT_SECONDS = 3.0
_FRAME_READ_BUFFER_BYTES = 0x10000
_FRAME_POLL_INTERVAL_SECONDS = 0.01
_TEXT_INPUT_MAX_LENGTH_BYTES = 300
_DEFAULT_SCREEN_RESOLUTION = (960, 540)


class ScrcpyEngine:
    """通过 Scrcpy 控制已连接的 Android 设备。

    Args:
        config: 设备连接、ADB、Scrcpy 和操作时序配置；省略时使用默认值。
    """

    def __init__(self, config: DeviceConfig | None = None) -> None:
        self._config = config or DeviceConfig()
        self._serial: str | None = None
        self._max_size = self._config.SCRCPY_MAX_SIZE
        self._bitrate = self._config.SCRCPY_BITRATE
        self._max_fps = self._config.SCRCPY_MAX_FPS
        self._screenshot_timeout = self._config.SCRCPY_SCREENSHOT_TIMEOUT
        configure_operation_delay_bounds(
            self._config.DEVICE_OPERATION_DELAY_MIN,
            self._config.DEVICE_OPERATION_DELAY_MAX,
        )

        self._device: AdbDevice | None = None
        self._resolution: tuple[int, int] = (0, 0)
        # 截图目标显示器；多显示器模拟器在连接后由上层跟随应用切换。
        self._display_id = 0
        self._last_frame: numpy.ndarray | None = None

        # scrcpy 连接状态。
        self._alive = False
        self._server_stream: AdbConnection | None = None
        self._video_socket: socket.socket | None = None
        self._control_socket: socket.socket | None = None
        self._decode_thread: threading.Thread | None = None
        self._frame_ready = threading.Event()  # 首帧就绪信号
        self._frame_lock = threading.Lock()
        self._reconnect_lock = threading.Lock()
        self._control_lock = threading.Lock()  # 控制流写串行化

    # ── 连接建立 ────────────────────────────────────────────────────────────

    def connect_scrcpy(self, device: AdbDevice, serial: str) -> tuple[int, int]:
        """使用已连接的 ADB 设备建立 Scrcpy 通道并等待首帧。

        Args:
            device: 已建立 ADB 连接的设备对象。
            serial: 设备的 ADB serial。

        Returns:
            Scrcpy 实际使用的设备分辨率。

        Raises:
            DeviceConnectionError: 服务、通道或首帧初始化失败。
        """
        self._device = device
        self._serial = serial
        _log.debug('[DEVICE] Scrcpy 连接 → 开始：serial={!r}', serial)

        try:
            # 初始化是一个连续流程：服务、双通道、解码线程和首帧必须全部成功。
            wsize = device.window_size()
            if wsize:
                self._resolution = (wsize[0], wsize[1])
            else:
                self._resolution = _DEFAULT_SCREEN_RESOLUTION
                _log.warning(
                    '[DEVICE] Scrcpy 连接 → 降级：分辨率={}，reason={!r}，result={!r}',
                    self._resolution,
                    'device_resolution_unavailable',
                    'fallback',
                )

            self._push_scrcpy_server()
            self._start_scrcpy_server()
            self._connect_video_channel()
            self._connect_control_channel()
            self._start_frame_decoder()
            if not self._frame_ready.wait(timeout=self._screenshot_timeout):
                raise DeviceConnectionError(
                    f'Scrcpy 视频流未能在 {self._screenshot_timeout}s 内产生首帧'
                )
        except Exception:
            self._close_scrcpy_channels()
            self._device = None
            raise

        _log.debug(
            '[DEVICE] Scrcpy 连接 → 完成：serial={!r}, resolution=({}, {}), result={!r}',
            serial,
            *self._resolution,
            'success',
        )
        return self._resolution

    # ── 连接关闭 ────────────────────────────────────────────────────────────

    def disconnect_scrcpy(self) -> None:
        """断开 Scrcpy 通道并释放其视频、控制和服务端资源。"""
        serial = self._serial or '自动选择'
        self._close_scrcpy_channels()

        self._device = None
        self._serial = None
        self._resolution = (0, 0)
        self._last_frame = None
        _log.debug('[DEVICE] Scrcpy 连接 → 断开：serial={!r}, result={!r}', serial, 'success')

    def is_scrcpy_connected(self) -> bool:
        """返回 Scrcpy 设备通道是否仍处于可用状态。"""
        return self._device is not None and self._alive

    @property
    def resolution(self) -> tuple[int, int]:
        """返回当前设备分辨率。"""
        return self._resolution

    # ── 截图 ────────────────────────────────────────────────────────────────

    def capture_screenshot(self) -> numpy.ndarray:
        """获取当前 RGB 截图。

        Returns:
            当前视频帧的 RGB 数组。

        Raises:
            DeviceConnectionError: 视频流恢复失败或在等待范围内没有产生帧。
        """
        self._ensure_scrcpy_stream()

        start = time.monotonic()
        while True:
            with self._frame_lock:
                frame = self._last_frame

            if frame is not None:
                return frame

            if not self._alive:
                self._ensure_scrcpy_stream()
                start = time.monotonic()
                continue

            if time.monotonic() - start > self._screenshot_timeout:
                _log.error(
                    '[DEVICE] 视频流 → 超时：等待={}秒，结果=失败，后续=断开',
                    self._screenshot_timeout,
                )
                raise DeviceConnectionError(
                    f'截图超时 ({self._screenshot_timeout}s)，scrcpy 视频流无数据'
                )
            time.sleep(_FRAME_POLL_INTERVAL_SECONDS)

    # ── 输入操作 ────────────────────────────────────────────────────────────

    def click_screen(self, x: float, y: float, *, delay: bool = False) -> None:
        """点击屏幕上的相对坐标。

        Args:
            x: 横向相对坐标，范围为 0.0 到 1.0。
            y: 纵向相对坐标，范围为 0.0 到 1.0。
            delay: 是否在发送触控事件前应用配置的随机延迟。
        """
        # 1. 按调用方要求在动作前等待全局操作延迟。
        if delay:
            time.sleep(calculate_operation_delay())

        # 2. 发送按下和抬起事件，组成一次点击。
        self._send_touch_event(_ACTION_DOWN, x, y, pressure=1.0)
        time.sleep(_GESTURE_EVENT_INTERVAL_SECONDS)
        self._send_touch_event(_ACTION_UP, x, y, pressure=0.0)

    def swipe_screen(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        duration: float = 0.5,
        *,
        delay: bool = False,
    ) -> None:
        """在两个相对坐标之间执行滑动。

        Args:
            x1: 起点横向相对坐标。
            y1: 起点纵向相对坐标。
            x2: 终点横向相对坐标。
            y2: 终点纵向相对坐标。
            duration: 手势持续时间，单位为秒。
            delay: 是否在发送触控事件前应用配置的随机延迟。
        """
        ms = int(duration * 1000)
        # 1. 按调用方要求在动作前等待全局操作延迟。
        if delay:
            time.sleep(calculate_operation_delay())

        # 2. 发送按下事件。
        self._send_touch_event(_ACTION_DOWN, x1, y1, pressure=1.0)
        time.sleep(_GESTURE_EVENT_INTERVAL_SECONDS)

        # 3. 在持续时间内插入移动事件，保持手势连续。
        steps = max(1, ms // 16)  # ~60fps，每步约 16ms
        step_ms = ms / steps
        for i in range(1, steps + 1):
            t = i / steps
            cx = x1 + (x2 - x1) * t
            cy = y1 + (y2 - y1) * t
            self._send_touch_event(_ACTION_MOVE, cx, cy, pressure=1.0)
            time.sleep(max(step_ms / 1000.0, _GESTURE_EVENT_INTERVAL_SECONDS))

        # 4. 发送抬起事件。
        self._send_touch_event(_ACTION_UP, x2, y2, pressure=0.0)

    def long_press_screen(self, x: float, y: float, duration: float = 1.0) -> None:
        """在相对坐标处执行长按。

        Args:
            x: 横向相对坐标。
            y: 纵向相对坐标。
            duration: 长按持续时间，单位为秒。
        """
        # 1. 按下后保持不动，确保长按持续指定时长。
        self._send_touch_event(_ACTION_DOWN, x, y, pressure=1.0)
        time.sleep(duration)

        # 2. 发送抬起事件，结束长按。
        self._send_touch_event(_ACTION_UP, x, y, pressure=0.0)

    # ── 按键和文本 ──────────────────────────────────────────────────────────

    def send_key_event(self, key_code: int, *, delay: bool = False) -> None:
        """发送一个 Android 按键事件。

        Args:
            key_code: Android 按键编码。
            delay: 是否在发送按键前应用配置的随机延迟。
        """
        # 1. 按调用方要求在动作前等待全局操作延迟。
        if delay:
            time.sleep(calculate_operation_delay())

        # 2. 发送 DOWN 和 UP，组成一次按键。
        self._send_key_event(key_code, action=_KEY_ACTION_DOWN)
        time.sleep(_GESTURE_EVENT_INTERVAL_SECONDS)
        self._send_key_event(key_code, action=_KEY_ACTION_UP)

    def input_text(self, content: str, *, delay: bool = False) -> None:
        """向当前输入目标写入文本。

        Args:
            content: 待输入文本。
            delay: 是否在输入文本前应用配置的随机延迟。
        """
        # 按调用方要求在动作前等待全局操作延迟。
        if delay:
            time.sleep(calculate_operation_delay())

        if content.isascii():
            # ASCII 文本直接走 INJECT_TEXT。
            self._send_text_input(content)
        else:
            # 多字节文本走剪贴板粘贴，保证中文输入能力。
            self._set_device_clipboard(content, paste=True)

    # ── scrcpy 服务 ─────────────────────────────────────────────────────────

    def _push_scrcpy_server(self) -> None:
        """推送 scrcpy-server.jar 到设备。"""
        if not _SCRCPY_SERVER_FILE.exists():
            _log.error(
                '[DEVICE] Scrcpy 服务 → 拒绝：路径={!r}，原因=缺少服务文件，结果=失败',
                str(_SCRCPY_SERVER_FILE),
            )
            raise DeviceConnectionError(
                f'找不到 scrcpy-server.jar: {_SCRCPY_SERVER_FILE}\n请确认 autowsgr 包数据完整'
            )
        _log.debug(
            '[DEVICE] scrcpy 服务 → 部署：path={!r}',
            str(_SCRCPY_SERVER_FILE),
        )
        dev = self._require_adb_device()
        dev.push(str(_SCRCPY_SERVER_FILE), _DEVICE_JAR_PATH)
        _log.debug("[DEVICE] scrcpy 服务 → 部署：result='success'")

    def _start_scrcpy_server(self) -> None:
        """在设备上启动 scrcpy-server 进程。"""
        cmd = [
            f'CLASSPATH={_DEVICE_JAR_PATH}',
            'app_process',
            '/',
            'com.genymobile.scrcpy.Server',
            _SCRCPY_SERVER_VERSION,
            'log_level=info',
            'tunnel_forward=true',
            'video=true',
            'audio=false',
            'control=true',
            f'max_size={self._max_size}',
            f'video_bit_rate={self._bitrate}',
            f'max_fps={self._max_fps}',
            'video_codec=h264',
            f'display_id={self._display_id}',
            'send_device_meta=false',
            'send_frame_meta=false',
            'send_codec_meta=false',
            'send_dummy_byte=true',
        ]
        _log.debug(
            '[DEVICE] scrcpy 服务 → 启动：version={!r}, max_size={}, bitrate={}, max_fps={}',
            _SCRCPY_SERVER_VERSION,
            self._max_size,
            self._bitrate,
            self._max_fps,
        )
        dev = self._require_adb_device()
        self._server_stream = dev.shell(cmd, stream=True)
        _log.debug("[DEVICE] scrcpy 服务 → 启动：result='submitted'")
        # 等待服务端完成初始化后再建立 socket。
        time.sleep(_SCRCPY_SERVER_START_DELAY_SECONDS)

    def _connect_video_channel(self) -> None:
        """连接 scrcpy 视频 socket。"""
        # ADB 客户端仅在建立 scrcpy 通道时加载。
        import adbutils

        dev = self._require_adb_device()
        for _attempt in range(_SCRCPY_CHANNEL_CONNECT_ATTEMPTS):
            try:
                self._video_socket = dev.create_connection(
                    adbutils.Network.LOCAL_ABSTRACT,
                    'scrcpy',
                )
                break
            except Exception:
                time.sleep(_SCRCPY_CHANNEL_RETRY_DELAY_SECONDS)
        else:
            _log.error(
                '[DEVICE] 视频流 → 失败：channel={!r}，attempts={}，result={!r}，next_action={!r}',
                'video',
                _SCRCPY_CHANNEL_CONNECT_ATTEMPTS,
                'failed',
                'disconnect',
            )
            raise DeviceConnectionError('无法连接 scrcpy-server 视频通道（3s 超时）')

        # 读取服务端首字节，确认视频通道已完成握手。
        dummy = self._video_socket.recv(1)
        if not dummy:
            _log.error(
                '[DEVICE] 视频流 → 校验失败：channel={!r}，expected={!r}，result={!r}',
                'video',
                'dummy_byte',
                'failed',
            )
            raise DeviceConnectionError('未收到 scrcpy dummy byte，连接可能已断开')
        _log.debug("[DEVICE] 视频流 → 连接：channel='video', result='success'")

    # ── 控制通道 ────────────────────────────────────────────────────────────

    def _connect_control_channel(self) -> None:
        """连接 scrcpy 控制通道。

        scrcpy 2.7 只在视频 socket 发送 dummy byte，控制 socket 不重复读取。
        """
        # ADB 客户端仅在建立 scrcpy 通道时加载。
        import adbutils

        dev = self._require_adb_device()
        for _attempt in range(_SCRCPY_CHANNEL_CONNECT_ATTEMPTS):
            try:
                self._control_socket = dev.create_connection(
                    adbutils.Network.LOCAL_ABSTRACT,
                    'scrcpy',
                )
                break
            except Exception:
                time.sleep(_SCRCPY_CHANNEL_RETRY_DELAY_SECONDS)
        else:
            _log.error(
                '[DEVICE] 控制流 → 失败：channel={!r}，attempts={}，result={!r}，next_action={!r}',
                'control',
                _SCRCPY_CHANNEL_CONNECT_ATTEMPTS,
                'failed',
                'disconnect',
            )
            raise DeviceConnectionError('无法连接 scrcpy-server 控制通道（3s 超时）')

        # 禁用 Nagle，降低控制指令延迟。
        try:
            self._control_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError as exc:
            _log.debug(
                "[DEVICE] 控制流 → 降级：option='tcp_nodelay', "
                "error_type={!r}, error={!r}, result='continued'",
                type(exc).__name__,
                str(exc),
            )
        _log.debug("[DEVICE] 控制流 → 连接：channel='control', result='success'")

    def _start_frame_decoder(self) -> None:
        """启动后台 H264 解码线程。"""
        self._alive = True
        self._decode_thread = threading.Thread(
            target=self._decode_video_stream,
            name='scrcpy-decode',
            daemon=True,
        )
        self._decode_thread.start()

    def _decode_video_stream(self) -> None:
        """后台解码循环：接收 H264 流并解码为 numpy 帧。"""
        # PyAV 只在视频流线程启动时加载。
        import av

        codec = av.CodecContext.create('h264', 'r')
        video_sock = self._video_socket
        assert video_sock is not None
        while self._alive:
            try:
                raw = video_sock.recv(_FRAME_READ_BUFFER_BYTES)
                if not raw:
                    if self._alive:
                        _log.warning(
                            "[DEVICE] 视频流 → 断开：reason='empty_frame', "
                            "result='retry', next_action='reconnect'",
                        )
                        self._alive = False
                    break

                for packet in codec.parse(raw):
                    for frame in codec.decode(packet):
                        rgb = frame.to_ndarray(format='rgb24')
                        h, w = rgb.shape[:2]

                        with self._frame_lock:
                            self._last_frame = rgb
                            if self._resolution != (w, h):
                                self._resolution = (w, h)
                                _log.debug(
                                    '[DEVICE] 视频流 → 更新：resolution=({}, {}), result={!r}',
                                    w,
                                    h,
                                    'success',
                                )

                        if not self._frame_ready.is_set():
                            self._frame_ready.set()

            except BlockingIOError:
                time.sleep(_FRAME_POLL_INTERVAL_SECONDS)
            except (ConnectionError, OSError) as exc:
                if self._alive:
                    _log.warning(
                        '[DEVICE] 视频流 → 异常：error_type={!r}, error={!r}, '
                        "result='retry', next_action='reconnect'",
                        type(exc).__name__,
                        str(exc),
                    )
                    self._alive = False
                break

    # ── 通道关闭与恢复 ──────────────────────────────────────────────────────

    def _close_scrcpy_channels(self) -> None:
        """关闭视频、控制和服务端通道。"""
        if self._control_socket is not None:
            try:
                self._control_socket.close()
            except Exception as exc:
                _log.debug(
                    "[DEVICE] 控制流 → 关闭：channel='control', error_type={!r}, "
                    "error={!r}, result='continued'",
                    type(exc).__name__,
                    str(exc),
                )
            self._control_socket = None

        if self._video_socket is not None:
            try:
                self._video_socket.close()
            except Exception as exc:
                _log.debug(
                    "[DEVICE] 视频流 → 关闭：channel='video', error_type={!r}, "
                    "error={!r}, result='continued'",
                    type(exc).__name__,
                    str(exc),
                )
            self._video_socket = None

        if self._server_stream is not None:
            try:
                self._server_stream.close()
            except Exception as exc:
                _log.debug(
                    "[DEVICE] scrcpy 服务 → 关闭：error_type={!r}, error={!r}, result='continued'",
                    type(exc).__name__,
                    str(exc),
                )
            self._server_stream = None

        if self._decode_thread is not None:
            self._decode_thread.join(timeout=_DECODER_JOIN_TIMEOUT_SECONDS)
            self._decode_thread = None

        self._alive = False
        self._frame_ready.clear()

    def reconnect_to_display(self, display_id: int) -> None:
        """切换截图目标显示器并重建视频流。

        目标显示器与当前相同时不重连，避免每次启动应用都白重建一次通道。

        Args:
            display_id: 目标显示器编号。

        Raises:
            DeviceConnectionError: 重建后仍拿不到首帧。
        """
        with self._reconnect_lock:
            if display_id == self._display_id and self._alive:
                return
            self._display_id = display_id
            _log.info('[DEVICE] scrcpy 服务 → 切换显示器：display_id={}，结果=重连', display_id)
            self._reconnect_scrcpy_stream()

    def _reconnect_scrcpy_stream(self) -> None:
        """在保持 ADB 设备连接的前提下重建 scrcpy 视频流与控制流。"""
        # 1. 关闭旧通道并清空上一帧，避免恢复期间返回过期画面。
        self._close_scrcpy_channels()
        self._last_frame = None

        # 2. 重建 scrcpy 服务、视频通道和控制通道。
        self._push_scrcpy_server()
        self._start_scrcpy_server()
        self._connect_video_channel()
        self._connect_control_channel()
        self._start_frame_decoder()

        # 3. 等待首帧，确认视频流已经恢复。
        if not self._frame_ready.wait(timeout=self._screenshot_timeout):
            _log.error(
                '[DEVICE] 视频流 → 恢复失败：等待={}秒，结果=失败，后续=断开',
                self._screenshot_timeout,
            )
            raise DeviceConnectionError(
                f'scrcpy 视频流重连失败：{self._screenshot_timeout}s 内无首帧'
            )

        _log.debug('[DEVICE] 视频流 → 重连：result={!r}', 'success')

    def _ensure_scrcpy_stream(self) -> None:
        """确保视频流可用，不可用时尝试一次重连。"""
        if self._alive:
            return

        with self._reconnect_lock:
            if self._alive:
                return

            _log.warning(
                "[DEVICE] 视频流 → 重连：reason='stream_not_alive', result='retry'",
            )
            self._reconnect_scrcpy_stream()

    # ── 控制流消息 ──────────────────────────────────────────────────────────

    def _require_control_channel(self) -> socket.socket:
        """返回控制 socket；视频流未就绪时先尝试恢复。"""
        self._ensure_scrcpy_stream()
        if self._control_socket is None:
            raise DeviceConnectionError('scrcpy 控制通道未连接')
        return self._control_socket

    def _send_control_message(self, data: bytes) -> None:
        """向控制 socket 串行写入一帧消息（线程安全）。"""
        sock = self._require_control_channel()
        with self._control_lock:
            try:
                sock.sendall(data)
            except (ConnectionError, OSError) as exc:
                # 控制消息发送失败时仅恢复一次，再重发同一消息。
                _log.warning(
                    "[DEVICE] 控制流 → 重连：error_type={!r}, error={!r}, result='retry'",
                    type(exc).__name__,
                    str(exc),
                )
                self._alive = False
                self._ensure_scrcpy_stream()
                sock = self._require_control_channel()
                try:
                    sock.sendall(data)
                except (ConnectionError, OSError) as retry_exc:
                    _log.error(
                        '[DEVICE] 控制流 → 恢复失败：error_type={!r}, error={!r}, '
                        "result='failed', next_action='disconnect'",
                        type(retry_exc).__name__,
                        str(retry_exc),
                    )
                    raise

    # ── 控制消息编码 ────────────────────────────────────────────────────────

    @staticmethod
    def _convert_pressure_to_u16fp(value: float) -> int:
        """将 [0.0, 1.0] 压力值编码为 scrcpy u16 定点数。"""
        clamped = max(0.0, min(1.0, value))
        return round(clamped * 0xFFFF)

    def _convert_relative_coordinate(self, x: float, y: float) -> tuple[int, int]:
        """将相对坐标 [0.0, 1.0] 转换为设备像素坐标。"""
        w, h = self._resolution
        return int(x * w), int(y * h)

    def _send_touch_event(
        self,
        action: int,
        x: float,
        y: float,
        pressure: float = 1.0,
        pointer_id: int = _POINTER_ID_FINGER,
    ) -> None:
        """发送 INJECT_TOUCH_EVENT 控制消息（scrcpy 2.7，32 字节）。

        布局：type(1) | action(1) | pointer_id(8) | x(4) | y(4)
              | width(2) | height(2) | pressure(2) | action_button(4) | buttons(4)
        """
        w, h = self._resolution
        px, py = self._convert_relative_coordinate(x, y)
        u16_pressure = self._convert_pressure_to_u16fp(pressure)
        data = struct.pack(
            '>BBqIIHHHII',
            _TYPE_INJECT_TOUCH_EVENT,
            action,
            pointer_id,
            px,
            py,
            w,
            h,
            u16_pressure,
            0,  # action_button（触摸事件为 0）
            0,  # buttons（触摸事件为 0）
        )
        # struct '>BBqIIHHHII' = 1+1+8+4+4+2+2+2+4+4 = 32 字节
        self._send_control_message(data)

    def _send_key_event(self, key_code: int, action: int = _KEY_ACTION_UP) -> None:
        """发送 INJECT_KEYCODE 控制消息（scrcpy 2.7，14 字节）。

        布局：type(1) | action(1) | keycode(4) | repeat(4) | metastate(4)
        """
        data = struct.pack(
            '>BBIII',
            _TYPE_INJECT_KEYCODE,
            action,
            key_code,
            0,  # repeat
            0,  # metastate
        )
        self._send_control_message(data)

    def _send_text_input(self, content: str) -> None:
        """发送 INJECT_TEXT 控制消息（scrcpy 2.7）。

        布局：type(1) | length(4) | utf8_bytes
        最大长度 300 字节。

        注意：INJECT_TEXT 通过 InputConnection.commitText 注入，
        仅对 ASCII/拉丁字符可靠；中文等多字节字符请使用 :meth:`_set_device_clipboard`。
        """
        raw = content.encode('utf-8')[:_TEXT_INPUT_MAX_LENGTH_BYTES]
        data = struct.pack('>BI', _TYPE_INJECT_TEXT, len(raw)) + raw
        self._send_control_message(data)

    def _set_device_clipboard(self, content: str, paste: bool = True) -> None:
        """发送 SET_CLIPBOARD 控制消息（scrcpy 2.7）。

        布局：type(1) | sequence(8) | paste(1) | length(4) | utf8_bytes

        ``paste=True`` 时，server 在设置剪贴板后会自动注入
        ``KEYCODE_PASTE``（Android ≥ 7），实现立即粘贴。
        该路径通过系统剪贴板 + 粘贴键工作，可正确输入中文等
        INJECT_TEXT 无法处理的字符。

        Args:
            content: 要输入的文本（UTF-8，最长 262130 字节）。
            paste: 是否在设置剪贴板后立即粘贴。
        """
        raw = content.encode('utf-8')[:_CLIPBOARD_TEXT_MAX_LENGTH_BYTES]
        # sequence=0 表示 SEQUENCE_INVALID，不请求 ack。
        data = struct.pack('>BQBI', _TYPE_SET_CLIPBOARD, 0, 1 if paste else 0, len(raw)) + raw
        self._send_control_message(data)

    def _require_adb_device(self) -> AdbDevice:
        """返回已连接的设备实例，未连接时抛出异常。"""
        if self._device is None:
            raise DeviceConnectionError('设备未连接，请先调用 device.service.connect()')
        return self._device


__all__ = ['ScrcpyEngine']
