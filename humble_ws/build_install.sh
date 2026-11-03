#!/bin/bash
# 编译和安装hand_arm_control包

echo "=========================================="
echo "Building hand_arm_control package"
echo "=========================================="

# 切换到工作空间目录
cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws

# 源ROS2环境
source /opt/ros/humble/setup.bash

# 安装依赖
echo "Installing dependencies..."
rosdep install --from-paths src --ignore-src -r -y

# 编译
echo "Building packages..."
colcon build --packages-select hand_arm_control --symlink-install

# 源编译后的环境
source install/setup.bash

echo ""
echo "=========================================="
echo "Build complete!"
echo "=========================================="
echo ""
echo "现在可以启动系统了："
echo "  ./src/hand_arm_control/start_camera_arm_control.sh"
echo ""