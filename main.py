#!/usr/bin/env python3
"""
Switch Cloud Play — Remote-play your Nintendo Switch from your Mac.

Captures video from Switch (via capture card or SysDVR), reads controller
input on Mac, and forwards it to the Switch (via serial/network/NXBT bridge).

Usage:
    python main.py                    # Use config.yaml defaults
    python main.py --video capture_card --bridge serial
    python main.py --video sysdvr --bridge network
    python main.py --fullscreen
"""

import argparse
import os
import signal
import sys
import time
import yaml

from video.capture_card import CaptureCardSource
from video.sysdvr import SysDVRSource
from video.display import Display
from input.controller import ControllerReader
from input.mapper import SwitchMapper
from bridge.serial_bridge import SerialBridge
from bridge.network import NetworkBridge
from bridge.nxbt_bridge import NXBTBridge


def load_config(path="config.yaml"):
    # Resolve path relative to this script's directory
    if not os.path.isabs(path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, path)
    with open(path) as f:
        return yaml.safe_load(f)


def make_video_source(cfg, override=None):
    source_type = override or cfg["video"]["source"]
    if source_type == "capture_card":
        cc = cfg["video"]["capture_card"]
        return CaptureCardSource(
            device_index=cc["device_index"],
            width=cc["width"],
            height=cc["height"],
            fps=cc["fps"],
        )
    elif source_type == "sysdvr":
        sd = cfg["video"]["sysdvr"]
        return SysDVRSource(
            mode=sd["mode"],
            switch_ip=sd.get("switch_ip"),
            port=sd["port"],
        )
    else:
        raise ValueError(f"Unknown video source: {source_type}")


def make_bridge(cfg, override=None):
    bridge_type = override or cfg["bridge"]["mode"]
    if bridge_type == "serial":
        s = cfg["bridge"]["serial"]
        return SerialBridge(port=s["port"], baud_rate=s["baud_rate"])
    elif bridge_type == "network":
        n = cfg["bridge"]["network"]
        return NetworkBridge(host=n["host"], port=n["port"])
    elif bridge_type == "nxbt":
        nx = cfg["bridge"]["nxbt"]
        return NXBTBridge(host=nx["pi_host"], port=nx["pi_port"])
    else:
        raise ValueError(f"Unknown bridge mode: {bridge_type}")


def main():
    parser = argparse.ArgumentParser(description="Switch Cloud Play")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument("--video", choices=["capture_card", "sysdvr"], help="Video source override")
    parser.add_argument("--bridge", choices=["serial", "network", "nxbt"], help="Bridge mode override")
    parser.add_argument("--fullscreen", action="store_true", help="Launch fullscreen")
    parser.add_argument("--view-only", action="store_true", help="Video only, skip controller/bridge setup")
    parser.add_argument("--list-devices", action="store_true", help="List video capture devices and exit")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.list_devices:
        CaptureCardSource.list_devices()
        return

    # Init components
    print("[*] Initializing video source...")
    video_source = make_video_source(cfg, args.video)

    print("[*] Initializing display...")
    fullscreen = args.fullscreen or cfg["display"].get("fullscreen", False)
    display = Display(
        title=cfg["display"]["title"],
        fullscreen=fullscreen,
        show_fps=cfg["display"].get("show_fps", True),
    )

    controller = None
    bridge = None
    mapper = None

    if not args.view_only:
        print("[*] Initializing controller...")
        controller = ControllerReader(
            controller_index=cfg["input"]["controller_index"],
            deadzone=cfg["input"]["deadzone"],
        )

        print("[*] Initializing input bridge...")
        bridge = make_bridge(cfg, args.bridge)
        mapper = SwitchMapper()

    # Graceful shutdown
    running = True
    def shutdown(sig, frame):
        nonlocal running
        running = False
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Connect
    try:
        video_source.open()
    except Exception as e:
        print(f"[!] Failed to open video source: {e}")
        print("    Make sure your capture card is connected or SysDVR is running.")
        sys.exit(1)

    if bridge:
        try:
            bridge.connect()
            print(f"[+] Bridge connected ({cfg['bridge']['mode']})")
        except Exception as e:
            print(f"[!] Failed to connect bridge: {e}")
            print("    Continuing without input forwarding (view-only mode).")
            bridge = None
    else:
        print("[*] View-only mode — no controller input forwarding.")

    print("[+] Running! Press Ctrl+C or close window to quit.")
    print("    Press F to toggle fullscreen.")

    # Main loop
    while running:
        # 1. Grab video frame
        frame = video_source.read()
        if frame is None:
            time.sleep(0.001)
            continue
        capture_time = time.time()

        # 2. Read controller input and forward to Switch
        if controller and bridge and mapper:
            raw_input = controller.poll()
            if raw_input:
                switch_state = mapper.map(raw_input, controller_name=controller.name)
                bridge.send(switch_state)

        # 3. Display frame with latency overlay
        should_quit = display.show(frame, capture_time=capture_time)
        if should_quit:
            break

    # Cleanup
    print("\n[*] Shutting down...")
    video_source.close()
    if bridge:
        bridge.disconnect()
    display.close()
    if controller:
        controller.close()
    print("[+] Done.")


if __name__ == "__main__":
    main()
