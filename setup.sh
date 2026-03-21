#!/bin/bash
# Switch Cloud Play — Mac Setup
set -e

echo "=== Switch Cloud Play Setup ==="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[!] Python 3 not found. Install from https://python.org or: brew install python"
    exit 1
fi

# Check pip
if ! python3 -m pip --version &>/dev/null; then
    echo "[!] pip not found. Installing..."
    python3 -m ensurepip --upgrade
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[*] Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "[*] Installing Python dependencies..."
pip install -r requirements.txt

# Check ffmpeg (needed for SysDVR TCP mode)
if command -v ffmpeg &>/dev/null; then
    echo "[+] ffmpeg found"
else
    echo "[!] ffmpeg not found. Install for SysDVR support: brew install ffmpeg"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "QUICK START:"
echo ""
echo "  1. CAPTURE CARD (recommended, no homebrew needed):"
echo "     - Buy a USB HDMI capture card (~\$15 on Amazon)"
echo "     - Switch dock HDMI → capture card → Mac USB"
echo "     - python3 scripts/test_capture.py  (test video)"
echo ""
echo "  2. FOR CONTROLLER INPUT, pick one:"
echo ""
echo "     a) Raspberry Pi + NXBT (wireless, no extra hardware on Switch):"
echo "        - On Pi: pip install nxbt && python3 scripts/nxbt_server.py"
echo "        - On Mac: set bridge.mode=nxbt in config.yaml"
echo ""
echo "     b) Pico/Arduino microcontroller (wired, most reliable):"
echo "        - Flash GP2040-CE: https://gp2040-ce.info/"
echo "        - Connect: Mac → Pico (serial) → Switch (USB gamepad)"
echo "        - Set bridge.mode=serial in config.yaml"
echo ""
echo "     c) SysDVR + sys-hidplus (all WiFi, needs homebrew/CFW):"
echo "        - Set video.source=sysdvr and bridge.mode=network"
echo ""
echo "  3. RUN: source venv/bin/activate && python3 -m switch_cloud_play"
echo ""
