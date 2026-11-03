#!/bin/bash
# Quick build script for hand_arm_control

set -e

echo "Building hand_arm_control package..."
echo ""

cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws

# Source ROS2
source /opt/ros/humble/setup.bash

# Build only the hand_arm_control package
colcon build --packages-select hand_arm_control --symlink-install

echo ""
echo "Build completed!"
echo ""
echo "Source the workspace:"
echo "  source install/setup.bash"
echo ""
echo "Then run the controller:"
echo "  ./src/hand_arm_control/start_hand_arm_control.sh"