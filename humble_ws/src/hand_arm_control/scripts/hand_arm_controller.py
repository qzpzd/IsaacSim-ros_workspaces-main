#!/usr/bin/env python3
"""
Hand-based Arm Controller for Isaac Sim
从Windows摄像头检测手部运动，向Isaac Sim发送机械臂控制指令
使用Float32MultiArray替代JointTrajectory
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge
import cv2
import numpy as np
import time

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

class HandArmController(Node):
    def __init__(self):
        super().__init__('hand_arm_controller')
        
        self.bridge = CvBridge()
        
        # 订阅Windows摄像头图像
        self.image_subscription = self.create_subscription(
            Image,
            '/webcam/image_raw',
            self.image_callback,
            10
        )
        
        # 向Isaac Sim发布关节位置指令
        self.joint_publisher = self.create_publisher(
            Float32MultiArray,
            '/arm_joint_positions',
            10
        )
        
        # Isaac Sim机械臂关节数量（Panda机械臂有7个关节 + 2个手指 = 9个）
        self.num_joints = 9
        
        # 初始化MediaPipe Hands
        if MEDIAPIPE_AVAILABLE:
            self.mp_hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.5
            )
            self.mp_draw = mp.solutions.drawing_utils
            self.get_logger().info('MediaPipe Hands initialized')
        else:
            self.get_logger().warn('MediaPipe not available, using optical flow')
            self.mp_hands = None
        
        # 工作空间限制
        self.workspace_limits = {
            'x': (-0.5, 0.5),
            'y': (-0.5, 0.5),
            'z': (0.1, 0.6)
        }
        
        # 机械臂控制参数
        self.current_joint_positions = np.zeros(self.num_joints)  # 9 个关节
        self.target_joint_positions = np.zeros(self.num_joints)  # 9 个关节
        self.previous_hand_center = None
        self.hand_velocity = np.array([0.0, 0.0, 0.0])
        
        # 控制参数
        self.detection_active = True
        self.last_detection_time = time.time()
        self.detection_interval = 0.05
        self.smoothing_factor = 0.3
        self.velocity_scale = 3.0  # 增加移动幅度
        self.joint_velocity_limit = 2.0  # 增加速度限制
        
        # 手指控制参数（默认打开）
        self.finger_open = True
        self.finger_position = 0.04  # 打开位置
        
        # 手部状态
        self.hand_position = None
        
        self.get_logger().info('Hand arm controller for Isaac Sim started')
        self.get_logger().info(f'MediaPipe available: {MEDIAPIPE_AVAILABLE}')
        self.get_logger().info('Subscribed to: /webcam/image_raw (from Windows)')
        self.get_logger().info('Publishing to: /arm_joint_positions (to Isaac Sim)')
    
    def image_callback(self, msg):
        try:
            # 转换ROS图像为OpenCV格式
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # 处理图像检测手部
            if self.detection_active and (time.time() - self.last_detection_time) > self.detection_interval:
                self.detect_hand_and_control(cv_image)
                self.last_detection_time = time.time()
            
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')
    
    def detect_hand_and_control(self, cv_image):
        """检测手部并控制Isaac Sim机械臂"""
        try:
            if MEDIAPIPE_AVAILABLE and self.mp_hands:
                self.detect_with_mediapipe(cv_image)
            else:
                self.detect_with_optical_flow(cv_image)
                
        except Exception as e:
            self.get_logger().error(f'Error in hand detection: {str(e)}')
    
    def detect_with_mediapipe(self, cv_image):
        """使用MediaPipe检测手部"""
        # 转换为RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        # 处理图像
        rgb_image.flags.writeable = False
        results = self.mp_hands.process(rgb_image)
        rgb_image.flags.writeable = True
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 获取关键点
                wrist = hand_landmarks.landmark[0]
                middle_finger_tip = hand_landmarks.landmark[12]
                index_finger_tip = hand_landmarks.landmark[8]
                
                # 计算手部中心位置（使用中指尖端）
                hand_center = self.landmark_to_3d_position(middle_finger_tip, cv_image.shape)
                
                # 计算手部移动速度
                if self.previous_hand_center is not None:
                    self.hand_velocity = (hand_center - self.previous_hand_center) / self.detection_interval
                    # 限制速度
                    velocity_magnitude = np.linalg.norm(self.hand_velocity)
                    max_velocity = 1.0
                    if velocity_magnitude > max_velocity:
                        self.hand_velocity = self.hand_velocity / velocity_magnitude * max_velocity
                
                self.previous_hand_center = hand_center.copy()
                
                # 将手部运动映射到关节空间
                joint_velocity = self.hand_to_joint_velocity(self.hand_velocity)
                
                # 应用速度缩放和平滑
                target_joint_change = joint_velocity * self.velocity_scale * self.smoothing_factor * self.detection_interval
                
                # 更新目标关节位置（前 7 个关节）
                self.target_joint_positions[:7] = self.current_joint_positions[:7] + target_joint_change[:7]
                
                # 设置手指位置（保持打开）
                self.target_joint_positions[7] = self.finger_position  # 手指1
                self.target_joint_positions[8] = self.finger_position  # 手指2
                
                # 限制关节位置
                self.target_joint_positions = np.clip(
                    self.target_joint_positions,
                    -2.0, 2.0
                )
                
                # 发送Isaac Sim机械臂控制指令
                self.send_isaac_sim_command(self.target_joint_positions)
                
                # 绘制检测结果
                self.draw_hand_landmarks(cv_image, hand_landmarks)
                
                # 显示状态信息
                self.display_info(cv_image, hand_center, self.target_joint_positions)
                
        else:
            # 没有检测到手部，保持当前位置
            self.send_isaac_sim_command(self.current_joint_positions)
            cv2.putText(cv_image, "No hand detected", (50, 50), 
                      cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow('Hand Detection', cv_image)
            cv2.waitKey(1)
    
    def detect_with_optical_flow(self, cv_image):
        """备用方法：使用光流检测运动"""
        if not hasattr(self, 'previous_frame'):
            self.previous_frame = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            return
        
        current_gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # 计算光流
        flow = cv2.calcOpticalFlowFarneback(
            self.previous_frame, current_gray, None,
            0.5, 3, 15, 3, 5, 1.2, 0
        )
        
        if flow is not None:
            # 计算平均运动
            magnitude, angle = cv2.cartToPolar(flow)
            avg_magnitude = np.mean(magnitude)
            avg_angle = np.mean(angle)
            
            if avg_magnitude > 1.0:
                # 将运动映射到3D空间
                move_x = avg_magnitude * np.cos(avg_angle) * 0.1
                move_y = avg_magnitude * np.sin(avg_angle) * 0.1
                
                joint_change = np.array([move_x, move_y, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                joint_change = np.clip(joint_change, -0.1, 0.1)
                
                self.target_joint_positions = self.current_joint_positions + joint_change
                self.target_joint_positions = np.clip(self.target_joint_positions, -2.0, 2.0)
                
                self.send_isaac_sim_command(self.target_joint_positions)
                self.current_joint_positions = self.target_joint_positions
        
        self.previous_frame = current_gray
        cv2.imshow('Motion Detection', cv_image)
        cv2.waitKey(1)
    
    def landmark_to_3d_position(self, landmark, image_shape):
        """将手部关键点转换为3D工作空间坐标"""
        height, width = image_shape[:2]
        
        # 将图像坐标映射到工作空间（增加范围）
        x = (landmark.x * 2 - 1) * 1.0  # 从 0.5 增加到 1.0
        y = (landmark.y * 2 - 1) * 1.0  # 从 0.5 增加到 1.0
        z = 0.2 + (1.0 - landmark.z) * 0.8  # 从 0.4 增加到 0.8
        
        return np.array([x, y, z])
    
    def hand_to_joint_velocity(self, hand_velocity):
        """将手部速度映射到关节速度（返回 9 个关节速度）"""
        vx, vy, vz = hand_velocity
        
        # 简化的关节速度映射（增加映射系数使移动更明显）
        joint1 = -vy * 4.0
        joint2 = vz * 4.0
        joint3 = vz * 3.0
        joint4 = -vx * 1.0
        joint5 = vy * 0.6
        joint6 = vx * 0.6
        joint7 = 0.0
        joint8 = 0.0  # 手指1
        joint9 = 0.0  # 手指2
        
        joint_velocity = np.array([joint1, joint2, joint3, joint4, joint5, joint6, joint7, joint8, joint9])
        
        # 限制关节速度
        joint_velocity = np.clip(joint_velocity, -self.joint_velocity_limit, self.joint_velocity_limit)
        
        return joint_velocity
    
    def draw_hand_landmarks(self, image, landmarks):
        """绘制手部关键点"""
        for landmark in landmarks.landmark:
            height, width = image.shape[:2]
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            cv2.circle(image, (x, y), 5, (0, 255, 0), -1)
        
        # 绘制连接线
        self.mp_draw.draw_landmarks(image, landmarks, mp.solutions.hands.HAND_CONNECTIONS)
    
    def display_info(self, image, hand_position, joint_positions):
        """显示当前信息"""
        # 绘制手部位置
        height, width = image.shape[:2]
        
        if hand_position is not None:
            hand_x = int(((hand_position[0] / 0.5) + 1) * width / 2)
            hand_y = int((1.0 - (hand_position[2] - 0.2) / 0.4) * height / 2)
            cv2.circle(image, (hand_x, hand_y), 10, (0, 255, 0), -1)
            
            # 显示位置信息
            info_text = f"Hand: ({hand_position[0]:.2f}, {hand_position[1]:.2f}, {hand_position[2]:.2f})"
            cv2.putText(image, info_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # 显示关节位置（前 3 个关节 + 手指状态）
        finger_status = "Open" if self.finger_position > 0.0 else "Closed"
        joint_text = f"Joints: {joint_positions[:3].round(2)} | Fingers: {finger_status}"
        cv2.putText(image, joint_text, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        
        # 显示系统状态
        status_text = "Isaac Sim Control Active"
        cv2.putText(image, status_text, (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 100, 255), 2)
        
        cv2.imshow('Hand Detection - Isaac Sim Control', image)
        cv2.waitKey(1)
    
    def send_isaac_sim_command(self, joint_positions):
        """向Isaac Sim发送机械臂控制指令"""
        try:
            # 创建关节位置消息
            msg = Float32MultiArray()
            msg.data = joint_positions.tolist()
            
            # 发布关节位置到Isaac Sim
            self.joint_publisher.publish(msg)
            
            # 更新当前位置
            self.current_joint_positions = joint_positions
            
        except Exception as e:
            self.get_logger().error(f'Error sending Isaac Sim command: {str(e)}')
    
    def stop(self):
        """停止节点"""
        if cv2 is not None:
            cv2.destroyAllWindows()

def main(args=None):
    rclpy.init(args=args)
    node = HandArmController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()