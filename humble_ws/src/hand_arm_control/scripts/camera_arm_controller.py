#!/usr/bin/env python3
"""
Camera-based object detection and arm controller
从摄像头检测物体并控制机械臂移动
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from cv_bridge import CvBridge
import cv2
import numpy as np
import time

class CameraArmController(Node):
    def __init__(self):
        super().__init__('camera_arm_controller')
        
        # CvBridge用于图像转换
        self.bridge = CvBridge()
        
        # 订阅摄像头图像
        self.image_subscription = self.create_subscription(
            Image,
            '/webcam/image_raw',  # 使用真实摄像头话题
            self.image_callback,
            10
        )
        
        # 发布关节轨迹
        self.trajectory_publisher = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            10
        )
        
        # 机械臂关节名称（根据您的机械臂调整）
        self.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
        ]
        
        # 机械臂工作空间限制
        self.workspace_limits = {
            'x': (-0.5, 0.5),  # x轴范围（米）
            'y': (-0.5, 0.5),  # y轴范围（米）
            'z': (0.0, 0.5)    # z轴范围（米）
        }
        
        # 初始位置
        self.current_position = np.array([0.0, 0.0, 0.3])
        self.target_position = np.array([0.0, 0.0, 0.3])
        
        # 检测参数
        self.detection_active = True
        self.last_detection_time = time.time()
        self.detection_interval = 0.1  # 检测间隔（秒）
        
        self.get_logger().info('Camera arm controller node started')
        self.get_logger().info('Subscribed to: /webcam/image_raw')
        self.get_logger().info('Publishing to: /joint_trajectory_controller/joint_trajectory')
    
    def image_callback(self, msg):
        try:
            # 转换ROS图像为OpenCV格式
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # 处理图像检测物体
            if self.detection_active and (time.time() - self.last_detection_time) > self.detection_interval:
                self.detect_and_control(cv_image)
                self.last_detection_time = time.time()
            
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')
    
    def detect_and_control(self, cv_image):
        """检测物体并控制机械臂"""
        try:
            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
            
            # 定义颜色范围（红色物体）
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([160, 100, 100])
            upper_red2 = np.array([180, 255, 255])
            
            # 创建红色掩码
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask = mask1 + mask2
            
            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) > 0:
                # 找到最大轮廓
                max_contour = max(contours, key=cv2.contourArea)
                
                # 计算轮廓中心
                M = cv2.moments(max_contour)
                if M['m00'] > 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    
                    # 转换为3D坐标（简单映射）
                    # 假设摄像头固定，图像中心对应工作空间中心
                    height, width = cv_image.shape[:2]
                    center_x, center_y = width // 2, height // 2
                    
                    # 将图像坐标转换为工作空间坐标
                    x = (cx - center_x) / width * (self.workspace_limits['x'][1] - self.workspace_limits['x'][0])
                    y = (cy - center_y) / height * (self.workspace_limits['y'][1] - self.workspace_limits['y'][0])
                    z = 0.2  # 固定高度
                    
                    # 限制在工作空间内
                    x = np.clip(x, self.workspace_limits['x'][0], self.workspace_limits['x'][1])
                    y = np.clip(y, self.workspace_limits['y'][0], self.workspace_limits['y'][1])
                    z = np.clip(z, self.workspace_limits['z'][0], self.workspace_limits['z'][1])
                    
                    # 设置目标位置
                    self.target_position = np.array([x, y, z])
                    
                    # 发送机械臂控制指令
                    self.send_arm_command(self.target_position)
                    
                    # 在图像上绘制检测结果
                    cv2.circle(cv_image, (cx, cy), 10, (0, 255, 0), 2)
                    cv2.putText(cv_image, f'({x:.2f}, {y:.2f}, {z:.2f})', 
                              (cx + 15, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    self.get_logger().info(f'Detected object at: {self.target_position}')
                    
                    # 显示调试窗口
                    cv2.imshow('Detection', cv_image)
                    cv2.waitKey(1)
            
            else:
                # 没有检测到物体时，保持当前位置
                self.send_arm_command(self.current_position)
                cv2.imshow('Detection', cv_image)
                cv2.waitKey(1)
                
        except Exception as e:
            self.get_logger().error(f'Error in detection: {str(e)}')
    
    def send_arm_command(self, target_position):
        """发送机械臂控制指令"""
        try:
            # 简单的位置映射（实际应用中需要逆运动学求解）
            # 这里使用简化的线性映射
            joint_positions = self.position_to_joints(target_position)
            
            # 创建轨迹消息
            trajectory_msg = JointTrajectory()
            trajectory_msg.joint_names = self.joint_names
            
            point = JointTrajectoryPoint()
            point.positions = joint_positions.tolist()
            point.velocities = [0.0] * len(self.joint_names)
            point.accelerations = [0.0] * len(self.joint_names)
            point.time_from_start.sec = 0  # 立即执行
            
            trajectory_msg.points.append(point)
            
            # 发布轨迹
            self.trajectory_publisher.publish(trajectory_msg)
            
            # 更新当前位置
            self.current_position = target_position
            
        except Exception as e:
            self.get_logger().error(f'Error sending arm command: {str(e)}')
    
    def position_to_joints(self, position):
        """
        将3D位置转换为关节角度（简化版本）
        实际应用中应该使用逆运动学求解器
        """
        x, y, z = position
        
        # 简化的映射关系（根据您的机械臂调整）
        # 这是一个线性映射，实际机械臂可能需要更复杂的逆运动学
        
        # 基础位置
        base_joint = np.arctan2(y, x)  # 底座关节
        shoulder_joint = np.arctan2(z, np.sqrt(x**2 + y**2))  # 肩关节
        elbow_joint = shoulder_joint * 0.5  # 肘关节
        wrist_joint = base_joint  # 手腕关节
        
        return np.array([
            base_joint,        # panda_joint1
            shoulder_joint,    # panda_joint2
            elbow_joint,       # panda_joint3
            0.0,              # panda_joint4
            0.0,              # panda_joint5
            0.0               # panda_joint6
        ])
    
    def stop(self):
        """停止节点"""
        cv2.destroyAllWindows()

def main(args=None):
    rclpy.init(args=args)
    node = CameraArmController()
    
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