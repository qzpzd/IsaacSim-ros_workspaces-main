#!/bin/bash
# Hand-based Arm Controller for Isaac Sim - Linux startup
# Detects hand movements and sends commands to Isaac Sim

set -e

echo "=========================================="
echo "Hand Arm Controller for Isaac Sim - Linux"
echo "=========================================="
echo ""
echo "Function: Detect hand movements from Windows webcam"
echo "          Send arm control commands to Isaac Sim"
echo ""

# Setup ROS2 environment
echo "[1/4] Setting up ROS2 environment..."
source /opt/ros/humble/setup.bash
cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws
source install/setup.bash
echo "ROS2 environment configured"
echo ""

# Check MediaPipe
echo "[2/4] Checking MediaPipe..."
python3 -c "import mediapipe as mp; print(f'MediaPipe version: {mp.__version__}')" 2>/dev/null || {
    echo "WARNING: MediaPipe not found"
    echo "Installing MediaPipe..."
    pip3 install mediapipe
}
echo "MediaPipe check completed"
echo ""

# Check cv_bridge
echo "[3/4] Checking cv_bridge..."
python3 -c "from cv_bridge import CvBridge; print('cv_bridge available')" || {
    echo "ERROR: cv_bridge not found"
    echo "Install cv_bridge with:"
    echo "  sudo apt-get install ros-humble-cv-bridge"
    exit 1
}
echo "cv_bridge available"
echo ""

# Start hand detection and command sending
echo "[4/4] Starting hand detection and Isaac Sim control..."
echo ""
echo "System architecture:"
echo "  1. Subscribe to Windows webcam: /webcam/image_raw"
echo "  2. Detect hand movements"
echo "  3. Send commands to Isaac Sim: /arm_joint_positions"
echo "  4. Isaac Sim receives and controls robot"
echo ""
echo "Press Ctrl+C to stop controller"
echo ""
echo "=========================================="
echo "Hand control mapping:"
echo "=========================================="
echo ""
echo "Hand movement mapping:"
echo "  - Hand left/right -> Base rotation"
echo "  - Hand up/down -> Shoulder/elbow joints"
echo "  - Hand forward/backward -> Arm reach"
echo ""
echo "Workspace:"
echo "  - X: -0.5m to 0.5m"
echo "  - Y: -0.5m to 0.5m"
echo "  - Z: 0.1m to 0.6m"
echo ""
echo "=========================================="
echo ""

# Start controller
ros2 run hand_arm_control hand_arm_controller

echo ""
echo "=========================================="
echo "Hand arm controller stopped"
echo "=========================================="