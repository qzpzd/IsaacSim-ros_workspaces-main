#!/bin/bash

# Isaac Sim ROS2 Bridge - Linux端FastDDS配置脚本
# 用于将Linux端的ROS2配置为使用FastDDS，以便与Windows端的Isaac Sim通信

set -e

echo "=========================================="
echo "Isaac Sim ROS2 Bridge - Linux端FastDDS配置"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为Linux系统
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}错误: 此脚本只能在Linux系统上运行${NC}"
    exit 1
fi

# 检查ROS 2是否已安装
if ! command -v ros2 &> /dev/null; then
    echo -e "${RED}错误: 未检测到ROS 2安装${NC}"
    echo "请先安装ROS 2 Humble: https://docs.ros.org/en/humble/Installation.html"
    exit 1
fi

# 检查ROS_DISTRO
if [[ -z "$ROS_DISTRO" ]]; then
    echo -e "${YELLOW}警告: ROS_DISTRO环境变量未设置${NC}"
    echo "尝试检测ROS 2发行版..."
    
    if [[ -f "/opt/ros/humble/setup.bash" ]]; then
        export ROS_DISTRO=humble
        echo -e "${GREEN}检测到ROS 2 Humble${NC}"
    elif [[ -f "/opt/ros/jazzy/setup.bash" ]]; then
        export ROS_DISTRO=jazzy
        echo -e "${GREEN}检测到ROS 2 Jazzy${NC}"
    else
        echo -e "${RED}错误: 无法检测到ROS 2发行版${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}当前ROS发行版: $ROS_DISTRO${NC}"
echo ""

# 步骤1: 安装FastDDS RMW实现
echo "=========================================="
echo "步骤 1/4: 安装FastDDS RMW实现"
echo "=========================================="

if dpkg -l | grep -q "ros-${ROS_DISTRO}-rmw-fastrtps-cpp"; then
    echo -e "${GREEN}FastDDS RMW实现已安装${NC}"
else
    echo "正在安装FastDDS RMW实现..."
    sudo apt update
    sudo apt install -y "ros-${ROS_DISTRO}-rmw-fastrtps-cpp"
    echo -e "${GREEN}FastDDS RMW实现安装完成${NC}"
fi

echo ""

# 步骤2: 设置环境变量
echo "=========================================="
echo "步骤 2/4: 配置环境变量"
echo "=========================================="

# 检查当前使用的RMW实现
CURRENT_RMW=$(ros2 doctor --report 2>/dev/null | grep "RMW implementation" | awk '{print $3}' || echo "unknown")
echo "当前RMW实现: $CURRENT_RMW"

# 设置RMW_IMPLEMENTATION为FastDDS
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

# 设置ROS_DOMAIN_ID（可选，默认为0）
if [[ -z "$ROS_DOMAIN_ID" ]]; then
    export ROS_DOMAIN_ID=0
    echo "设置ROS_DOMAIN_ID: $ROS_DOMAIN_ID"
fi

echo -e "${GREEN}环境变量配置完成${NC}"
echo "  RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"
echo "  ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
echo ""

# 步骤3: 验证配置
echo "=========================================="
echo "步骤 3/4: 验证配置"
echo "=========================================="

# 验证RMW实现
echo "验证RMW实现..."
if [[ "$RMW_IMPLEMENTATION" == "rmw_fastrtps_cpp" ]]; then
    echo -e "${GREEN}✓ RMW_IMPLEMENTATION正确设置为FastDDS${NC}"
else
    echo -e "${RED}✗ RMW_IMPLEMENTATION设置错误${NC}"
    exit 1
fi

# 验证ROS 2功能
echo "验证ROS 2功能..."
if ros2 --help &> /dev/null; then
    echo -e "${GREEN}✓ ROS 2命令可用${NC}"
else
    echo -e "${RED}✗ ROS 2命令不可用${NC}"
    exit 1
fi

echo ""

# 步骤4: 创建持久化配置
echo "=========================================="
echo "步骤 4/4: 创建持久化配置"
echo "=========================================="

# 询问是否创建持久化配置
read -p "是否创建持久化配置（添加到~/.bashrc）？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    BASHRC="$HOME/.bashrc"
    
    # 检查是否已存在配置
    if grep -q "Isaac Sim ROS2 Bridge" "$BASHRC"; then
        echo -e "${YELLOW}配置已存在于~/.bashrc中${NC}"
    else
        # 添加配置到~/.bashrc
        cat >> "$BASHRC" << 'EOF'

# Isaac Sim ROS2 Bridge - FastDDS配置
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
EOF
        echo -e "${GREEN}配置已添加到~/.bashrc${NC}"
        echo "请运行以下命令使配置生效："
        echo "  source ~/.bashrc"
    fi
else
    echo -e "${YELLOW}跳过持久化配置${NC}"
    echo "每次使用前需要手动设置环境变量："
    echo "  export RMW_IMPLEMENTATION=rmw_fastrtps_cpp"
    echo "  export ROS_DOMAIN_ID=0"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}配置完成！${NC}"
echo "=========================================="
echo ""
echo "配置摘要："
echo "  ROS发行版: $ROS_DISTRO"
echo "  RMW实现: $RMW_IMPLEMENTATION"
echo "  ROS_DOMAIN_ID: $ROS_DOMAIN_ID"
echo ""
echo "下一步："
echo "  1. 确保Windows端的Isaac Sim已启动并配置了FastDDS"
echo "  2. 确保两台机器在同一网络中"
echo "  3. 检查防火墙设置（允许端口7400-7401）"
echo "  4. 运行以下命令验证连接："
echo "     ros2 node list"
echo "     ros2 topic list"
echo ""
echo "如果需要诊断连接问题，请运行："
echo "  bash diagnose_connection_fastdds.sh"
echo ""
