#!/bin/bash
# Complete fix script for Linux environment

echo "=========================================="
echo "Fixing Linux Environment Issues"
echo "=========================================="
echo ""

# Issue 1: Fix NumPy version
echo "[1/3] Fixing NumPy version compatibility..."
pip3 uninstall -y numpy 2>/dev/null || true
pip3 install "numpy<2"

# Verify NumPy version
python3 -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
echo "NumPy version fixed"
echo ""

# Issue 2: Test cv_bridge
echo "[2/3] Testing cv_bridge..."
python3 -c "from cv_bridge import CvBridge; print('cv_bridge OK')" || {
    echo "ERROR: cv_bridge still has issues"
    echo "You may need to reinstall cv_bridge:"
    echo "  sudo apt-get install --reinstall ros-humble-cv-bridge"
    exit 1
}
echo "cv_bridge working"
echo ""

# Issue 3: Rebuild package
echo "[3/3] Rebuilding hand_arm_control..."
cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws
source /opt/ros/humble/setup.bash

# Clean previous build
rm -rf build/hand_arm_control install/hand_arm_control

# Build
colcon build --packages-select hand_arm_control --symlink-install

echo ""
echo "=========================================="
echo "Fix completed!"
echo "=========================================="
echo ""
echo "Start the controller with:"
echo "  source install/setup.bash"
echo "  ./src/hand_arm_control/start_hand_arm_control.sh"
echo ""