# Isaac Sim ROS2工作空间 - 摄像头机械臂控制

## 快速开始

### Windows端：启动摄像头发布器

```bash
cd D:\soft\isaac-sim-standalone-5.0.0-windows-x86_64
python.bat webcam_publisher_nocvbridge.py
```

### Linux端：启动机械臂控制系统

```bash
cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws
./src/hand_arm_control/start_camera_arm_control.sh
```

## 系统功能

✅ **Windows真实摄像头** - 发布图像到ROS2
✅ **物体检测** - 检测红色物体位置
✅ **坐标转换** - 图像坐标→3D工作空间坐标
✅ **机械臂控制** - 发送关节轨迹指令
✅ **实时跟踪** - 持续跟踪物体位置

## 话题列表

### 订阅话题
- `/webcam/image_raw` - 摄像头图像（Windows发布）

### 发布话题
- `/joint_trajectory_controller/jaint_trajectory` - 机械臂关节轨迹

## 主要文件

### 新增文件
- `camera_arm_controller.py` - 摄像头物体检测和机械臂控制
- `camera_arm_control.launch.py` - 系统启动文件
- `start_camera_arm_control.sh` - 启动脚本
- `build_install.sh` - 编译安装脚本
- `CAMERA_ARM_CONTROL_GUIDE.md` - 详细使用指南

### 现有文件
- `arm_controller.py` - 基于手关键点的机械臂控制
- `hand_keypoint_detector.py` - 手部关键点检测
- `camera_publisher.py` - 摄像头发布器

## 配置说明

### 检测颜色

默认检测红色物体，可在 `camera_arm_controller.py` 中修改：

```python
# 红色物体范围
lower_red1 = np.array([0, 100, 100])
upper_red1 = np.array([10, 255, 255])
```

### 工作空间

默认工作空间：x(-0.5~0.5m), y(-0.5~0.5m), z(0.0~0.5m)

### 机械臂配置

默认配置Panda机械臂7个关节，可根据实际情况修改。

## 故障排查

### 无法检测物体
- 确保物体颜色为红色
- 检查光照条件
- 验证摄像头话题: `ros2 topic echo /webcam/image_raw`

### 机械臂不响应
- 检查控制器: `ros2 control list_controllers`
- 验证话题连接: `ros2 topic info /joint_trajectory_controller/joint_trajectory`

### 网络问题
- 确认两台机器在同一网络
- 验证ROS_DOMAIN_ID一致性

## 文档

详细使用说明请参阅 `CAMERA_ARM_CONTROL_GUIDE.md`