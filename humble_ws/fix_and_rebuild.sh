#!/bin/bash
# Fix NumPy version and rebuild

echo "Fixing NumPy version issue..."
echo ""

# Uninstall NumPy 2.x
pip3 uninstall -y numpy

# Install NumPy 1.x
pip3 install "numpy<2"

echo "NumPy version fixed"
echo ""

# Rebuild the package
echo "Rebuilding hand_arm_control..."
cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select hand_arm_control --symlink-install

echo ""
echo "Build completed!"
echo ""
echo "Test the executable:"
echo "  source install/setup.bash"
echo "  ros2 run hand_arm_control hand_arm_controller"