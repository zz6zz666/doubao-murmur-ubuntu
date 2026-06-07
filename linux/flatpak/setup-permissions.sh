#!/bin/bash
# setup-permissions.sh - Post-install permission setup for Doubao Murmur
# Run on host after Flatpak install for full functionality.

set -e

echo "=== Doubao Murmur Permission Setup ==="
echo ""

# 1. Add user to input group (for evdev and ydotool)
if ! groups | grep -q input; then
    echo "[1/3] Adding user to 'input' group..."
    sudo usermod -aG input "$USER"
    echo "  -> You must log out and back in for this to take effect."
else
    echo "[1/3] User already in 'input' group. OK"
fi

# 2. Enable ydotoold systemd service (for paste simulation)
if command -v ydotoold &>/dev/null; then
    echo "[2/3] Enabling ydotoold service..."
    sudo systemctl enable --now ydotoold
    echo "  -> ydotoold enabled."
elif systemctl list-unit-files ydotoold.service &>/dev/null 2>&1; then
    echo "[2/3] Enabling ydotoold service..."
    sudo systemctl enable --now ydotoold
else
    echo "[2/3] ydotoold not found. Install with: sudo pacman -S ydotool"
    echo "  -> Auto-paste will not work without ydotool."
fi

# 3. Install recommended packages
echo ""
echo "[3/3] Checking recommended packages..."
MISSING=""
for pkg in wl-clipboard ydotool; do
    if ! pacman -Qq "$pkg" &>/dev/null 2>&1; then
        MISSING="$MISSING $pkg"
    fi
done
if [ -n "$MISSING" ]; then
    echo "  -> Recommended packages not installed:$MISSING"
    echo "  -> Install with: sudo pacman -S$MISSING"
else
    echo "  -> All recommended packages installed. OK"
fi

# 4. Grant Flatpak device access (if installed as Flatpak)
if flatpak list | grep -q com.doubao.Murmur; then
    echo ""
    echo "Granting Flatpak device access..."
    flatpak override --user --device=all com.doubao.Murmur
    flatpak override --user --socket=wayland com.doubao.Murmur
    echo "  -> Flatpak permissions updated."
fi

echo ""
echo "=== Setup complete ==="
if ! groups | grep -q input; then
    echo "IMPORTANT: Please log out and back in for the 'input' group to take effect."
fi
echo ""
echo "Launch with: flatpak run com.doubao.Murmur"
echo "Or:          cd linux && ./run.sh"
