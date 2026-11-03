# Hand and Arm Control Package

This package provides a complete system for controlling a Franka robot arm using hand keypoints detected from a camera.

## Features

- **Camera Publisher**: Reads images from a webcam or simulated camera and publishes them to ROS2 topics
- **Hand Keypoint Detector**: Uses MediaPipe to detect hand keypoints from camera images
- **Arm Controller**: Maps hand keypoints to joint positions and publishes joint trajectory commands

## Requirements

### Software
- ROS2 Humble
- Python 3.8+
- OpenCV
- MediaPipe
- cv_bridge

### Hardware
- Webcam (for real camera input)
- Franka robot arm (simulated in Isaac Sim)

## Installation

1. **Clone the repository** into your ROS2 workspace:

   ```bash
   cd ~/humble_ws/src
   git clone <repository_url>
   ```

2. **Install dependencies**:

   ```bash
   # For Ubuntu/Linux
   sudo apt install python3-pip
   pip3 install opencv-python mediapipe

   # For Windows
   pip install opencv-python mediapipe
   ```

3. **Build the package**:

   ```bash
   cd ~/humble_ws
   colcon build
   source install/setup.bash  # For Linux
   # or
   .\install\setup.ps1  # For Windows
   ```

## Usage

### 1. Start Isaac Sim with ROS2 Bridge

- Open Isaac Sim
- Enable the ROS2 Bridge extension
- Load a Franka robot into the scene
- Run the `enable_ros2_topics.py` script to start publishing ROS2 topics

### 2. Start the hand and arm control system

```bash
# For Linux
ros2 launch hand_arm_control hand_arm_control.launch.py

# For Windows
ros2 launch hand_arm_control hand_arm_control.launch.py
```

### 3. Control the robot

- Position your hand in front of the camera
- The system will detect your hand keypoints
- The robot arm will move according to your hand position

## ROS2 Topics

### Published Topics

- `/camera/image_raw` - Camera images
- `/hand_keypoints` - Detected hand keypoints
- `/joint_trajectory_controller/joint_trajectory` - Joint trajectory commands

### Subscribed Topics

- `/camera/image_raw` - Camera images (used by hand keypoint detector)
- `/hand_keypoints` - Detected hand keypoints (used by arm controller)

## Configuration

### Camera Settings

You can modify the camera resolution and FPS in `camera_publisher.py`:

```python
# Set camera resolution
self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Set publishing rate
self.timer = self.create_timer(0.033, self.publish_image)  # ~30 FPS
```

### Hand Keypoint Detection Settings

You can modify the hand detection parameters in `hand_keypoint_detector.py`:

```python
self.hands = self.mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
```

### Arm Control Settings

You can modify the joint mapping parameters in `arm_controller.py`:

```python
# 手关键点到关节位置的映射参数
self.scale_factor = 0.5  # 缩放因子，调整手移动到关节移动的比例
self.offset = np.array([0.0, 0.0, 0.0, -1.57, 0.0, 1.57, 0.785])  # 初始关节位置偏移
```

## Troubleshooting

### Camera Issues
- If the camera is not detected, try changing the camera index in `camera_publisher.py`:
  ```python
  self.cap = cv2.VideoCapture(1)  # Try different index
  ```

### Hand Detection Issues
- Ensure proper lighting conditions
- Keep your hand within the camera frame
- Adjust the detection confidence thresholds if needed

### Arm Control Issues
- Check if the Franka robot is properly loaded in Isaac Sim
- Ensure the ROS2 Bridge is enabled and topics are being published
- Adjust the scale factor and offset in `arm_controller.py` for better mapping

## Cross-Platform Compatibility

This package is designed to work on both Windows and Linux platforms:

- **Windows**: Tested with Isaac Sim 5.0 and ROS2 Humble
- **Linux**: Tested with ROS2 Humble

## License

Apache 2.0
