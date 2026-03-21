# Switch Cloud Play

Remote-play your Nintendo Switch on your Mac. Captures video from Switch, reads controller input on Mac, and forwards it back to the Switch — like cloud gaming, but local.

```
[Switch] ──HDMI──▶ [Capture Card] ──USB──▶ [Mac display]
[Mac controller] ──serial/network──▶ [Microcontroller/Pi] ──USB/BT──▶ [Switch]
```

## What You Need

**Video (pick one):**

| Method | Cost | Latency | Homebrew? |
|--------|------|---------|-----------|
| USB HDMI capture card | $12-30 | ~30-50ms | No |
| SysDVR over USB-C | $0 | ~100ms | Yes (CFW) |
| SysDVR over WiFi | $0 | ~150ms+ | Yes (CFW) |

**Input (pick one):**

| Method | Cost | Latency | Homebrew? |
|--------|------|---------|-----------|
| Pico/Arduino serial bridge | $5-15 | <1ms | No |
| Raspberry Pi + NXBT (Bluetooth) | $15 | ~5-10ms | No |
| sys-hidplus (WiFi) | $0 | ~10-20ms | Yes (CFW) |

**Cheapest setup:** $15 capture card + $5 Pico = $20 total.

## Quick Start

```bash
git clone https://github.com/fnsmdehip/switch-cloud-play.git
cd switch-cloud-play
./setup.sh
```

### 1. Test video capture

Plug your capture card into your Mac and Switch dock:

```
Switch dock HDMI out → capture card HDMI in → capture card USB → Mac
```

```bash
python3 -m scripts.test_capture
```

You should see your Switch output in a window.

### 2. Test controller input

Plug any controller into your Mac (Xbox, PS4/PS5, 8BitDo, Pro Controller):

```bash
python3 -m scripts.test_controller
```

Move sticks and press buttons — you should see the values update.

### 3. Set up input bridge

#### Option A: Pico/Arduino (wired, lowest latency)

1. Flash [GP2040-CE](https://gp2040-ce.info/) to a Raspberry Pi Pico
2. Connect Pico to Switch dock via USB (it appears as a gamepad)
3. Connect Pico to Mac via second USB (serial communication)
4. Set `bridge.mode: serial` in `config.yaml`

#### Option B: Raspberry Pi + NXBT (wireless, no Switch mods)

1. On a Raspberry Pi 3/4/5:
   ```bash
   pip install nxbt
   python3 scripts/nxbt_server.py
   ```
2. Open "Change Grip/Order" on Switch to pair
3. Set `bridge.mode: nxbt` and `bridge.nxbt.pi_host` to your Pi's IP in `config.yaml`

### 4. Run

```bash
python3 -m switch_cloud_play
```

Press `F` to toggle fullscreen, `ESC` to quit.

## Configuration

Edit `config.yaml` to change video source, input bridge, display settings:

```yaml
video:
  source: capture_card          # or "sysdvr"
  capture_card:
    device_index: 0             # 0 = first capture device
    width: 1920
    height: 1080
    fps: 60

bridge:
  mode: serial                  # "serial", "network", or "nxbt"
  serial:
    port: "/dev/tty.usbmodem1101"
```

Run `python3 -m switch_cloud_play --list-devices` to find your capture card's device index.

## Architecture

```
switch_cloud_play/
├── video/              Video capture backends
│   ├── capture_card.py   HDMI capture via OpenCV (AVFoundation on Mac)
│   ├── sysdvr.py         SysDVR homebrew stream (USB or TCP/ffmpeg)
│   └── display.py        Low-latency OpenCV window with FPS overlay
├── input/              Controller input
│   ├── controller.py     Gamepad reading via pygame (any USB/BT controller)
│   └── mapper.py         Maps Xbox/PS/etc button layouts to Switch Pro Controller
├── bridge/             Input forwarding to Switch
│   ├── serial_bridge.py  Binary packets over serial to Pico/Arduino
│   ├── network.py        UDP packets to sys-hidplus or Pi relay
│   └── nxbt_bridge.py    UDP packets to Raspberry Pi running NXBT
├── scripts/            Standalone utilities
│   ├── nxbt_server.py    NXBT bridge server (runs on Raspberry Pi)
│   ├── test_capture.py   Test video capture
│   └── test_controller.py Test controller input
├── hardware/           Microcontroller reference
│   └── pico_firmware.py  CircuitPython reference for Pico (GP2040-CE recommended)
├── config.yaml         Runtime configuration
└── setup.sh            Mac setup script
```

## Latency

The FPS counter shows in the top-left corner. Typical end-to-end latency:

| Component | Latency |
|-----------|---------|
| Capture card (USB 3.0) | 30-50ms |
| OpenCV decode + display | 5-10ms |
| Controller poll (60Hz) | 0-16ms |
| Serial bridge | <1ms |
| Network bridge (LAN) | 1-5ms |
| **Total (capture card + serial)** | **~50-80ms** |

For comparison, native Switch docked play has ~30-50ms of display latency. Cloud gaming services typically have 50-150ms.

## Supported Controllers

Any controller macOS recognizes via USB or Bluetooth:
- Xbox One / Series X|S
- PS4 (DualShock 4) / PS5 (DualSense)
- Nintendo Pro Controller
- 8BitDo controllers
- Generic USB gamepads

Button mapping defaults to Xbox layout with automatic A/B and X/Y swap for Nintendo convention.

## Related Projects

- [SysDVR](https://github.com/exelix11/SysDVR) — Homebrew video capture from Switch
- [NXBT](https://github.com/Brikwerk/nxbt) — Bluetooth controller emulation (Linux)
- [GP2040-CE](https://gp2040-ce.info/) — Open-source gamepad firmware for RP2040
- [Nintendo-Switch-Remote-Control](https://github.com/javmarina/Nintendo-Switch-Remote-Control) — Arduino + WebRTC approach

## License

MIT
