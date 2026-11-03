#!/bin/bash
# 快速测试：发送一系列关节位置到 Windows Isaac Sim

echo "============================================================"
echo "快速测试：发送关节位置到 Windows Isaac Sim"
echo "============================================================"
echo

# 加载环境
source /opt/ros/humble/setup.bash
WORKSPACE_DIR="/home/star/qzp/IsaacSim-ros_workspaces-main/humble_ws"
source ${WORKSPACE_DIR}/install/setup.bash

export FASTRTPS_DEFAULT_PROFILES_FILE=${WORKSPACE_DIR}/fastdds.xml
export ROS_DOMAIN_ID=0

echo "准备发送测试消息..."
echo "确保 Windows 端 Isaac Sim 控制器正在运行"
echo
echo "按 Enter 开始，或 Ctrl+C 取消"
read

echo
echo "开始发送测试消息序列..."
echo "------------------------------------------------------------"

# 测试消息序列
TEST_MESSAGES=(
    "0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.04, 0.04"  # 初始位置
    "0.5, 0.3, 0.5, 0.2, 0.0, 0.0, 0.0, 0.04, 0.04"  # 举起手臂
    "-0.5, -0.3, -0.5, -0.2, 0.0, 0.0, 0.0, 0.04, 0.04"  # 反向
    "0.0, 0.0, 0.0, 0.0, 0.5, 0.3, 0.5, 0.04, 0.04"  # 腕部运动
    "0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0"      # 闭合手指
    "0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.04, 0.04"  # 打开手指
)

MESSAGE_NAMES=(
    "初始位置"
    "举起手臂"
    "反向运动"
    "腕部运动"
    "闭合手指"
    "打开手指"
)

for i in "${!TEST_MESSAGES[@]}"; do
    echo
    echo "[测试 $((i+1))/${#TEST_MESSAGES[@]}] ${MESSAGE_NAMES[$i]}"
    echo "  关节位置: [${TEST_MESSAGES[$i]}]"
    
    # 发送消息
    ros2 topic pub /arm_joint_positions std_msgs/Float32MultiArray \
      "{data: [${TEST_MESSAGES[$i]}]}" \
      --once > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "  ✓ 发送成功"
    else
        echo "  ✗ 发送失败"
    fi
    
    # 等待 2 秒
    sleep 2
done

echo
echo "------------------------------------------------------------"
echo "测试序列完成"
echo
echo "检查 Windows 端 Isaac Sim 窗口："
echo "  - 机械臂应该跟随消息移动"
echo "  - 控制台应该显示接收到的消息"
echo
echo "如果一切正常，可以运行手部控制器："
echo "  python3 src/hand_arm_control/scripts/hand_arm_controller.py"
echo "============================================================"