#!/bin/bash
# Linux 端 ROS2 通信测试脚本
# 用于验证与 Windows Isaac Sim 的连接

echo "============================================================"
echo "Linux ROS2 通信测试"
echo "============================================================"
echo

# 加载环境
source /opt/ros/humble/setup.bash
WORKSPACE_DIR="/home/star/qzp/IsaacSim-ros_workspaces-main/humble_ws"
source ${WORKSPACE_DIR}/install/setup.bash

export FASTRTPS_DEFAULT_PROFILES_FILE=${WORKSPACE_DIR}/fastdds.xml
export ROS_DOMAIN_ID=0

echo "环境变量已加载"
echo "FASTRTPS: ${FASTRTPS_DEFAULT_PROFILES_FILE}"
echo "ROS_DOMAIN_ID: ${ROS_DOMAIN_ID}"
echo

echo "============================================================"
echo "测试步骤"
echo "============================================================"
echo

# 等待几秒让 ROS2 发现
echo "等待 ROS2 发现（5秒）..."
sleep 5

# 步骤 1: 检查主题
echo
echo "[步骤 1/4] 检查可用的 ROS2 主题..."
echo "执行: ros2 topic list"
echo "------------------------------------------------------------"
TOPICS=$(ros2 topic list 2>/dev/null)
if [ -n "$TOPICS" ]; then
    echo "$TOPICS" | while read topic; do
        echo "  - $topic"
    done
else
    echo "  未发现主题"
fi

# 步骤 2: 检查目标主题
echo
echo "[步骤 2/4] 检查 /arm_joint_positions 主题..."
echo "执行: ros2 topic info /arm_joint_positions"
echo "------------------------------------------------------------"
if echo "$TOPICS" | grep -q "/arm_joint_positions"; then
    echo "  ✓ 发现 /arm_joint_positions 主题"
    ros2 topic info /arm_joint_positions 2>/dev/null || echo "  警告: 无法获取主题详细信息"
else
    echo "  ✗ 未发现 /arm_joint_positions 主题"
    echo "  请检查:"
    echo "    1. Windows 端 Isaac Sim 控制器是否正在运行"
    echo "    2. FastDDS 配置文件中的 IP 地址是否正确"
    echo "    3. 网络连接是否正常"
    echo "    4. 防火墙是否允许端口 7400 和 7410"
fi

# 步骤 3: 监听主题
echo
echo "[步骤 3/4] 监听 /arm_joint_positions 主题（10秒）..."
echo "执行: ros2 topic echo /arm_joint_positions --once"
echo "------------------------------------------------------------"
if echo "$TOPICS" | grep -q "/arm_joint_positions"; then
    echo "等待接收消息..."
    timeout 10s ros2 topic echo /arm_joint_positions --once 2>/dev/null &
    ECHO_PID=$!
    
    # 等待 10 秒
    for i in {10..1}; do
        echo -n "."
        sleep 1
    done
    echo
    
    # 检查是否接收到消息
    if ps -p $ECHO_PID > /dev/null 2>&1; then
        kill $ECHO_PID 2>/dev/null
        echo "  超时：未接收到消息"
        echo "  Windows 端可能未发布消息"
    else
        echo "  ✓ 接收到消息（见上方输出）"
    fi
else
    echo "  跳过：主题不存在"
fi

# 步骤 4: 发布测试消息
echo
echo "[步骤 4/4] 发布测试消息..."
echo "执行: ros2 topic pub /arm_joint_positions std_msgs/Float32MultiArray ..."
echo "------------------------------------------------------------"
echo "发送测试消息：[0.5, 0.3, 0.5, 0.2, 0.0, 0.0, 0.0, 0.04, 0.04]"
echo "（单次发送，5秒超时）"
timeout 5s ros2 topic pub /arm_joint_positions std_msgs/Float32MultiArray \
  '{data: [0.5, 0.3, 0.5, 0.2, 0.0, 0.0, 0.0, 0.04, 0.04]}' \
  --once 2>/dev/null

if [ $? -eq 0 ]; then
    echo "  ✓ 消息发送成功"
    echo "  Windows 端应该能看到："
    echo "    ✓ 收到 ROS2 消息: 关节位置 = [0.5 0.3 0.5 ...]"
else
    echo "  ⚠ 发送失败（可能超时）"
fi

echo
echo "============================================================"
echo "测试完成"
echo "============================================================"
echo
echo "下一步:"
echo "  1. 如果所有测试通过，说明通信正常"
echo "  2. 运行手部控制器进行实际测试:"
echo "     python3 src/hand_arm_control/scripts/hand_arm_controller.py"
echo
echo "调试提示:"
echo "  - 检查 Windows 端控制台输出"
echo "  - 确认 ROS_DOMAIN_ID 一致（都是 0）"
echo "  - 验证网络连通性: ping <Windows IP>"
echo "  - 检查防火墙设置"
echo "============================================================"