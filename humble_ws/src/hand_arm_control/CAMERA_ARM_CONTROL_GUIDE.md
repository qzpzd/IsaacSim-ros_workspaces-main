# 摄像头机械臂控制系统使用指南

## 系统概述

这个系统实现了从Windows真实摄像头获取图像，检测物体，并控制机械臂移动到物体位置的功能。

## 系统架构

```
Windows端:
├── 真实摄像头 (webcam)
└── Isaac Sim (可选，用于虚拟相机)

    ROS2网络 (FastDDS)

Linux端:
├── 摄像头物体检测
├── 位置转换
└── 机械臂控制
```

## 功能特性

1. **摄像头输入**
   - 从Windows真实摄像头获取图像
   - 话题: `/webcam/image_raw`
   - 分辨率: 640x480

2. **物体检测**
   - 检测红色物体
   - 计算物体中心位置
   - 实时跟踪物体

3. **坐标转换**
   - 将图像坐标转换为3D工作空间坐标
   - 工作空间范围: x(-0.5~0.5m), y(-0.5~0.5m), z(0.0~0.5m)

4. **机械臂控制**
   - 简化的逆运动学映射
   - 实时发布关节轨迹
   - 话题: `/joint_trajectory_controller/joint_trajectory`

## 使用步骤

### 1. 启动Windows摄像头发布器

在Windows端运行：

```bash
cd D:\soft\isaac-sim-standalone-5.0.0-windows-x86_64
python.bat webcam_publisher_nocvbridge.py
```

### 2. 在Linux端启动机械臂控制系统

在Linux端运行：

```bash
cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws
./src/hand_arm_control/start_camera_arm_control.sh
```

或者手动启动：

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_DOMAIN_ID=0
ros2 launch hand_arm_control camera_arm_control.launch.py
```

### 3. 验证系统状态

**检查摄像头话题**:
```bash
ros2 topic list
ros2 topic info /webcam/image_raw
```

**检查机械臂话题**:
```bash
ros2 topic info /joint_trajectory_controller/joint_trajectory
```

## 检测和配置

### 检测参数

在 `camera_arm_controller.py` 中可以调整：

```python
# 颜色范围（红色物体）
lower_red1 = np.array([0, 100, 100])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([160, 100, 100])
upper_red2 = np.array([180, 255, 255])
```

要检测其他颜色，修改HSV范围：

**绿色物体**:
```python
lower_green = np.array([35, 100, 100])
upper_green = np.array([85, 255, 255])
```

**蓝色物体**:
```python
lower_blue = np.array([100, 100, 100])
upper_blue = np.array([130, 255, 255])
```

### 工作空间配置

```python
self.workspace_limits = {
    'x': (-0.5, 0.5),  # x轴范围（米）
    'y': (-0.5, 0.5),  # y轴范围（米）
    'z': (0.0, 0.5)    # z轴范围（米）
}
```

### 检测频率

```python
self.detection_interval = 0.1  # 检测间隔（秒）
```

## 机械臂配置

### 关节名称

根据您的机械臂型号修改 `joint_names`:

```python
self.joint_names = [
    'panda_joint1', 'panda_joint2', 'panda_joint3',
    'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
]
```

常见机械臂配置：

**UR5**:
```python
self.joint_names = [
    'shoulder_pan_joint', 'shoulder_lift_joint',
    'elbow_joint', 'wrist_1_joint',
    'wrist_2_joint', 'wrist_3_joint'
]
```

**ABB IRB 120**:
```python
self.joint_names = [
    'joint_1', 'joint_2', 'joint_3',
    'joint_4', 'joint_5', 'joint_6'
]
```

### 逆运动学

当前使用简化的线性映射，对于精确控制，建议：

1. 使用MoveIt逆运动学求解器
2. 集成专业的运动学库（如IKFast）
3. 使用机械臂制造商提供的逆运动学接口

## 故障排查

### 没有检测到物体

1. **检查颜色配置**：
   - 确保物体颜色在HSV范围内
   - 使用OpenCV工具测试颜色分割

2. **检查摄像头话题**：
   ```bash
   ros2 topic echo /webcam/image_raw --no-arr
   ```

3. **检查网络连接**：
   - 确认Windows和Linux在同一网络
   - 验证FastDDS配置

### 机械臂不响应

1. **检查话题连接**：
   ```bash
   ros2 topic list
   ros2 topic echo /joint_trajectory_controller/joint_trajectory
   ```

2. **检查控制器状态**：
   ```bash
   ros2 control list_controllers
   ros2 control list_hardware_interfaces
   ```

3. **验证轨迹消息**：
   - 检查joint_names是否匹配
   - 确认关节角度在有效范围内

### 网络问题

1. **检查防火墙**：
   - Windows: 允许UDP端口7400-7410
   - Linux: `sudo ufw allow 7400:7410/udp`

2. **验证ROS2通信**：
   ```bash
   # Windows端
   ros2 topic list
   
   # Linux端
   ros2 topic list
   ```

## 扩展功能

### 添加多物体检测

修改检测逻辑支持多个物体：

```python
# 存储所有检测到的物体
detected_objects = []

for contour in contours:
    # 处理每个轮廓...
    detected_objects.append(object_info)

# 选择最近或最大的物体
if detected_objects:
    target = select_target(detected_objects)
```

### 添加路径规划

使用MoveIt添加碰撞检测和路径规划：

```python
from moveit_msgs.srv import GetPositionIK

def compute_ik_request(target_pose):
    request = GetPositionIK.Request()
    request.group_name = "panda_arm"
    request.ik_request.pose_stamped = target_pose
    return request
```

### 添加安全限制

```python
# 碰撞检测
def check_collision(joint_positions):
    # 检查关节角度是否超过限制
    for angle in joint_positions:
        if abs(angle) > max_joint_angle:
            return True
    return False

# 速度限制
def smooth_trajectory(current, target, steps=10):
    # 生成平滑的关节轨迹
    for i in range(steps):
        step = current + (target - current) * (i/steps)
        yield step
```

## 性能优化

1. **降低检测频率**: 增大 `detection_interval`
2. **使用ROI**: 只处理感兴趣区域
3. **多线程处理**: 将检测和控制分离
4. **GPU加速**: 使用CUDA进行图像处理

## 集成到实际项目

### 与视觉系统集成

1. 使用专业物体检测算法（YOLO、SSD等）
2. 3D坐标重建（立体视觉、深度相机）
3. 机器学习增强识别

### 与安全系统集成

1. 急停按钮监控
2. 力矩限制监控
3. 碰撞预警

## 维护和升级

1. **定期校准**: 相机-机器人标定
2. **参数调优**: 根据实际环境调整
3. **性能监控**: 延迟和准确性监控

## 支持和反馈

如有问题，请检查：
1. 日志文件: `ros2 topic echo /rosout`
2. 节点状态: `ros2 node list`
3. 话题数据: `ros2 topic hz <topic_name>`