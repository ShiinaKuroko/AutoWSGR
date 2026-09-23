# Debug Toolkit

This folder is the Agent-facing debug package. Run it from the repository root
with `uv run python tools/debug_toolkit/main.py ...` or
`uv run python -m tools.debug_toolkit ...`.

```text
main.py
function/
  e2e.py
  e2e_runner/   canonical E2E runner and cases
  annotate.py   标注 ROI 矩形和识别像素点
  collect.py    编队页/船池页 OCR 样本采集
  inspect.py    截图、ROI、OCR、像素和页面签名诊断
  screenshot.py
  roi.py
  ocr.py
adb/
result/
```

The `e2e` command runs the bundled canonical runner. All E2E cases live under
this package; the old root-level E2E entry is removed.

## Commands

```text
python tools/debug_toolkit/main.py screenshot --serial 127.0.0.1:16384
python tools/debug_toolkit/main.py annotate --image screenshot.png --roi main:0.90,0.84,1.0,0.95 --point P1:0.6453,0.9375 --point-size 3 --output marked.png
python tools/debug_toolkit/main.py annotate --serial emulator-5554 --roi main:0.90,0.84,1.0,0.95 --point P1:0.6453,0.9375
python tools/debug_toolkit/main.py roi --image result/screenshot/screenshot_*.png --roi 0.25,0.33,0.47,0.60
python tools/debug_toolkit/main.py ocr --image result/screenshot/screenshot_*/1x/screenshot_*_roi_1x.png
python tools/debug_toolkit/main.py inspect --image screenshot.png --roi 0.8,0.8,0.9,0.9 --allowlist "0-9"
python tools/debug_toolkit/main.py inspect --image screenshot.png --check-page main --pixel 0.5,0.5
python tools/debug_toolkit/main.py e2e --serial 127.0.0.1:16384 screenshot --no-launch
python tools/debug_toolkit/main.py e2e --with-ocr change_fleet --fleet 2 --ships U-47,U-96
python tools/debug_toolkit/main.py collect adb 127.0.0.1:16384
python tools/debug_toolkit/main.py collect team --mode A
python tools/debug_toolkit/main.py collect pool --mode B --output D:/ocr-samples
```

## Output

```text
result/
  logs/       copied E2E run logs
  screenshot/ timestamped screenshots and per-screenshot ROI folders
  ocr/        JSON OCR results
  crops/      编队页/船池页 OCR 样本和原始截图
```

`collect team` and `collect pool` require the game to be on the matching page.
They keep the original ADB screenshot and save `name`, `level`, and `type`
regions at 1X, 2X, 3X, and 4X. `--mode A` creates a timestamp directory;
`--mode B` appends non-overlapping captures to the date directory.

`annotate` accepts repeatable normalized `--roi` and `--point` arguments.
Prefix either value with `LABEL:` for an on-image label. If `--image` is
omitted, it captures the current ADB screen; it prints the corresponding pixel
coordinates and writes a new image without overwriting the source.

For a no-Python Windows collector, run `build_collect.ps1` and then use the
generated `start-collector.cmd` beside `main.exe`.

For an input named `screenshot_20260909_120000.png`, ROI output is:

```text
result/screenshot/screenshot_20260909_120000/
  screenshot_20260909_120000.png
  1x/screenshot_20260909_120000_roi_1x.png
  2x/screenshot_20260909_120000_roi_2x.png
  4x/screenshot_20260909_120000_roi_4x.png
  8x/screenshot_20260909_120000_roi_8x.png
```

The generated package includes the ADB runtime sourced from
`autowsgr/common/device/_resources/bin`. Device owns these binaries; the debug
toolkit only consumes the device ADB capability. Specialized standalone tools
remain separate when they provide capabilities not covered by this package.
