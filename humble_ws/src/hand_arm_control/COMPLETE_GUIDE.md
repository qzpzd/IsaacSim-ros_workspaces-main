# 摄像头机械臂控制系统 - 完整使用指南

## 系统概述

这个系统实现了从Windows真实摄像头获取图像，检测物体位置，并控制机械臂移动到物体位置的完整功能。

## 系统架构

```
Windows端                      Linux端
├── 摄像头                     ├── 摄像头物体检测
│   └── 实时图像采集              │   └── OpenCV颜色检测
│                              │
└── Isaac Sim (可选)              ├── 位置转换
    └── 虚拟相机 (备用)           │   └── 图像→3D坐标
                                │
ROS2网络 (FastDDS)                ├── 机械臂控制
                                │   └── 关节轨迹生成
                                │
                                └── 机械臂执行
                                    └── 物理运动
```

## 快速开始

### 第一步：启动Windows摄像头发布器

在Windows端运行：

```bash
cd D:\soft\isaac-sim-standalone-5.0.0-windows-x86_64
python.bat webcam_publisher_nocvbridge.py
```

**预期输出**：
```
[INFO] 摄像头分辨率: 640x480
[INFO] 摄像头帧率: 0
[INFO] 摄像头发布器已启动
```

### 第二步：编译Linux端工作空间（首次使用）

在Linux端运行：

```bash
cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws
./build_install.sh
```

### 第三步：启动Linux端控制系统

在Linux端运行：

```bash
cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws
./src/handle_arm_control/start_camera_arm_control.sh
```

**预期输出**：
```
==========================================
Camera Arm Control System
==========================================
启动摄像头物体检测和机械臂控制系统...
功能说明:
  - 从Windows真实摄像头获取图像
  - 检测红色物体
  - 将物体位置转换为机械臂控制指令
  - 控制机械臂移动到物体位置
话题:
  订阅: /webcam/image_raw (Windows真实摄像头)
  发布: /joint_trajectory_controller/joint_trajectory (机械臂轨迹)
```

### 第四步：验证系统运行

#### 测试摄像头连接

**Windows端**：
```bash
python.bat test_webcam_connection.py
```

**Linux端**：
```bash
cd ~/qzp/IsaacSim-ros_workspaces-main/humble_ws
source install/setup.bash
python3 src/hand_arm_control/scripts/test_system.py
```

#### 检查话题列表

```bash
ros2 topic list
```

**预期话题**：
```
/webcam/image_raw
/webcam/camera_info  
/joint_trajectory_controller/joint_trajectory
/parameter_events
/rosout
```

## 系统组件详解

### 1. 摄像头发布器 (`webcam_publisher_nocvbridge.py`)

**功能**：
- 从Windows摄像头获取实时图像
- 发布到ROS2话题

**配置**：
- 分辨率：640x480
- 编码：BGR8
- 话题：`/webcam/image_raw`

**修改方法**：
- 更改摄像头索引：`camera = cv2.VideoCapture(0)`  # 0=默认摄像头
- 调整分辨率：`camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)`

### 2. 物体检测和机械臂控制 (`camera_arm_controller.py`)

**功能**：
- 订阅摄像头图像
- 检测红色物体
- 计算3D坐标
- 生成机械臂轨迹

**检测参数**：
```python
# 颜色范围（HSV）
lower_red1 = np.array([0, 100, 100])
upper_red1 = np.array([10, 255, 255])

# 工作空间
x: -0.5 ~ 0.5米
y: -0.5 ~ 0.5米  
z: 0.0 ~ 0.5米

# 检测频率
间隔: 0.1秒
```

**机械臂配置**：
```python
# 关节名称
['panda_joint1', 'panda_joint2', 'panda_joint3',
 'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7']
```

## 使用场景

### 场景1：物体拾取任务

1. 准备红色物体放在工作区域内
2. 启动摄像头发布器
3. 启动机械臂控制系统
4. 系统自动检测物体位置
5. 机械臂移动到物体位置

### 场景2：物体跟踪

1. 移动物体
2. 系统实时跟踪物体位置
3. 机械臂持续调整位置
4. 实现物体跟随

### 场景3：多目标检测

修改代码支持多物体检测：

```python
# 存储所有检测到的物体
detected_objects = []

for contour in contours:
    # 处理每个轮廓
    object_info = process_contour(contour)
    detected_objects.append(object_info)

# 选择目标
target = select_target(detected_objects)
```

## 自定义配置

### 更改检测颜色

**绿色物体**：
```python
lower_green = np.array([35, 100, 100])
upper_green = np.array([85, 255, 255])
mask = cv2.inRange(hsv, lower_green, upper_green)
```

**蓝色物体**：
```python
lower_blue = np.array([100, 100, 100])
upper_blue = np.array([130, 255, 255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)
```

**自定义颜色**：
```python
# 使用颜色拾取工具获取HSV值
lower_custom = np.array([H_low, S_low, V_low])
upper_custom = np.array([H_high, S_high, V_high])
mask = cv2.inRange(hsv, lower_custom, upper_custom)
```

### 调整工作空间

```python
self.workspace_limits = {
    'x': (-0.3, 0.3),   # 缩小工作空间
    'y': (-0.3, 0.3),   # 缩小工作空间
    'z': (0.1, 0.4)     # 提高工作空间
}
```

### 配置不同机械臂

**UR5机械臂**：
```python
self.joint_names = [
    'shoulder_pan_joint', 'shoulder_lift_joint',
    'elbow_joint', 'wrist_1_joint',
    'wrist_2_joint', 'wrist_3_joint'
]
```

**自定义机械臂**：
```python
self.joint_names = [
    'joint1', 'joint2', 'joint3',
    'joint4', 'joint5', 'joint6'
]
```

## 故障排查

### 问题1：无法检测到物体

**可能原因**：
- 物体颜色不在检测范围内
- 光照条件不佳
- 摄像头角度问题

**解决方法**：
1. 使用OpenCV工具测试颜色分割：
   ```bash
   python3 -c "import cv2; import numpy as np; cap = cv2.VideoCapture(0); ret, frame = cap.read(); hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV); print('HSV range:', hsv.min(), hsv.max())"
   ```

2. 调整颜色范围参数
3. 改善光照条件

### 问题2：机械臂不响应

**可能原因**：
- 话题名称不匹配
- 控制器未启动
- 关节角度超出限制

**解决方法**：
1. 检查话题连接：
   ```bash
   ros2 topic info /joint_trajectory_controller/joint_trajectory
   ```

2. 检查控制器状态：
   ```bash
   ros2 control list_controllers
   ```

3. 验证关节角度范围

### 问题3：网络连接问题

**可能原因**：
- 两台机器不在同一网络
- 防火墙阻止通信
- ROS2配置不一致

**解决方法**：
1. 验证网络连接：
   ```bash
   ping <Linux机器IP>
   ```

2. 检查防火墙：
   ```bash
   # Windows
   netsh advfirewall firewall add rule name="ROS2" dir=in action=allow protocol=UDP localport=7400 remoteport=7400
   
   # Linux
   sudo ufw allow 7400:7410/udp
   ```

3. 验证ROS2配置：
   ```bash
   # Windows端
   echo $ROS_DOMAIN_ID
   echo $RMW_IMPLEMENTATION
   
   # Linux端
   echo $ROS_DOMAIN_ID
   echo $RMW_IMPLEMENTATION
   ```

### 问题4：延迟过高

**可能原因**：
- 检测频率过高
- 网络延迟
- 机械臂响应慢

**解决方法**：
1. 降低检测频率：
   ```python
   self.detection_interval = 0.2  # 从0.1秒增加到0.2秒
   ```

2. 优化网络配置：
   - 使用有线网络
   - 减少网络跳数

3. 优化机械臂控制：
   - 使用更高效的控制器
   - 预测物体运动

## 性能优化

### 1. 降低检测频率

```python
self.detection_interval = 0.2  # 10Hz → 5Hz
```

### 2. 使用ROI（感兴趣区域）

```python
# 只处理图像中心区域
h, w = cv_image.shape[:2]
roi = cv_image[h//4:3*h//4, w//4:3*w//4]
```

### 3. 降低图像分辨率

```python
# 在摄像头发布器中降低分辨率
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
```

### 4. 多线程处理

```python
import threading
from queue import Queue

class AsyncDetector:
    def __init__(self):
        self.queue = Queue()
        self.running = True
        
    def detection_thread(self):
        while self.running:
            # 异步检测处理
            pass
```

## 扩展功能

### 1. 添加深度信息

```python
# 使用深度相机获取3D坐标
depth_camera = cv2.VideoCapture(1)
ret, depth_frame = depth_camera.read()
```

### 2. 使用深度学习检测

```python
import torch
import torchvision

# 使用YOLO进行检测
model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt')
results = model(image)
```

### 3. 添加路径规划

```python
from moveit_msgs.srv import GetPositionIK

def plan_trajectory(current_pos, target_pos):
    # 使用MoveIt进行路径规划
    pass
```

### 4. 添加安全监控

```python
def check_safety(joint_positions):
    # 检查关节角度限制
    # 检查碰撞风险
    # 检查速度限制
    pass
```

## 维护建议

### 1. 定期校准

- 摄像头内参标定
- 手眼标定
- 工作空间校准

### 2. 参数调优

- 根据实际环境调整检测参数
- 优化机械臂运动参数
- 调整网络配置

### 3. 性能监控

- 监控延迟
- 监控准确性
- 监控系统资源使用

## 支持和资源

### 文档
- `CAMERA_ARM_CONTROL_GUIDE.md` - 详细使用指南
- `README.md` - 项目概述
- 代码注释 - 每个函数都有详细说明

### 工具
- `test_system.py` - 系统测试工具
- `test_webcam_connection.py` - 连接测试工具
- `build_install.sh` - 编译安装工具

### 示例代码
- `camera_arm_controller.py` - 主要控制脚本
- `arm_controller.py` - 基础机械臂控制器
- `hand_keypoint_detector.py` - 手部检测示例

## 总结

这个系统提供了完整的从摄像头图像到机械臂控制的解决方案：

✅ **易于使用** - 简单的启动脚本
✅ **高度可配置** - 灵活的参数调整
✅ **实时性能** - 实时检测和控制
✅ **可扩展** - 支持多种扩展功能
✅ **完整文档** - 详细的使用指南

通过本系统，您可以快速实现从摄像头图像到机械臂控制的自动化任务。