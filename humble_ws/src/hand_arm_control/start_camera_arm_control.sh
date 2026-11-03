#!/bin/bash
# 摄像头机械臂控制系统启动脚本
# 从Windows真实摄像头检测物体并控制机械臂

echo "=========================================="
echo "Camera Arm Control System"
echo "=========================================="

# 源ROS2环境
source /opt/ros/humble/setup.bash

# 源工作空间
cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws
source install/setup.bash

# 设置环境变量
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0

echo ""
echo "启动摄像头物体检测和机械臂控制系统..."
echo ""
echo "功能说明:"
echo "  - 从Windows真实摄像头获取图像"
echo "  - 检测红色物体"
echo "  - 将物体位置转换为机械臂控制指令"
echo "  - 控制机械臂移动到物体位置"
echo ""
echo "话题:"
echo "  订阅: /webcam/image_raw (Windows真实摄像头)"
echo "  发布: /joint_trajectory_controller/joint_trajectory (机械臂轨迹)"
echo ""
echo "按Ctrl+C停止系统"
echo ""

# 启动系统
ros2 launch hand_arm_control camera_arm_control.launch.py