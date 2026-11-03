#!/usr/bin/env python3
"""
Arm controller node that maps hand keypoints to TCP end-effector pose
"""
import rclpy
from rclpy.node import Node
from custom_message.msg import HandKeypoints
from geometry_msgs.msg import PoseStamped
import numpy as np
from scipy.spatial.transform import Rotation as R

class ArmController(Node):
    def __init__(self):
        super().__init__('arm_controller')
        
        # 订阅手关键点话题
        self.keypoints_subscriber = self.create_subscription(
            HandKeypoints,
            '/hand_keypoints',
            self.keypoints_callback,
            10
        )
        
        # 发布TCP末端位姿话题
        self.tcp_pose_publisher = self.create_publisher(
            PoseStamped,
            '/tcp_pose',
            10
        )
        
        # 手关键点到TCP位姿的映射参数
        self.position_scale = 0.5  # 位置缩放因子
        self.rotation_scale = 1.0  # 旋转缩放因子
        
        # 初始TCP位姿偏移
        self.tcp_offset = np.array([0.5, 0.0, 0.5])  # 初始位置偏移
        
        self.get_logger().info('Arm controller node started')
    
    def keypoints_callback(self, msg):
        try:
            if len(msg.keypoints) < 21:  # 确保有足够的关键点
                self.get_logger().warn('Not enough keypoints detected')
                return
            
            # 获取手腕关键点（索引 0）、食指指尖（索引 8）和中指指尖（索引 12）
            wrist = msg.keypoints[0]
            index_finger = msg.keypoints[8]
            middle_finger = msg.keypoints[12]
            
            # 计算手的位置（使用手腕位置）
            hand_position = np.array([wrist.x, wrist.y, wrist.z])
            
            # 计算手的方向向量
            # 食指指向作为x轴
            index_direction = np.array([
                index_finger.x - wrist.x,
                index_finger.y - wrist.y,
                index_finger.z - wrist.z
            ])
            
            # 中指指向作为y轴
            middle_direction = np.array([
                middle_finger.x - wrist.x,
                middle_finger.y - wrist.y,
                middle_finger.z - wrist.z
            ])
            
            # 归一化方向向量
            if np.linalg.norm(index_direction) > 0:
                index_direction = index_direction / np.linalg.norm(index_direction)
            if np.linalg.norm(middle_direction) > 0:
                middle_direction = middle_direction / np.linalg.norm(middle_direction)
            
            # 计算z轴（叉积）
            z_direction = np.cross(index_direction, middle_direction)
            if np.linalg.norm(z_direction) > 0:
                z_direction = z_direction / np.linalg.norm(z_direction)
            else:
                # 如果叉积为零，使用默认z轴
                z_direction = np.array([0.0, 0.0, 1.0])
            
            # 重新计算y轴以确保正交
            y_direction = np.cross(z_direction, index_direction)
            y_direction = y_direction / np.linalg.norm(y_direction)
            
            # 构建旋转矩阵
            rotation_matrix = np.array([index_direction, y_direction, z_direction]).T
            
            # 转换为四元数
            r = R.from_matrix(rotation_matrix)
            quaternion = r.as_quat()  # [x, y, z, w]
            
            # 计算TCP位置（缩放和偏移）
            tcp_position = self.tcp_offset + self.position_scale * np.array([
                hand_position[0] - 0.5,  # 中心化x坐标
                0.5 - hand_position[1],  # 反转y坐标以匹配机器人坐标系
                hand_position[2]
            ])
            
            # 创建PoseStamped消息
            pose_msg = PoseStamped()
            pose_msg.header.frame_id = 'world'
            pose_msg.header.stamp = self.get_clock().now().to_msg()
            
            # 设置位置
            pose_msg.pose.position.x = tcp_position[0]
            pose_msg.pose.position.y = tcp_position[1]
            pose_msg.pose.position.z = tcp_position[2]
            
            # 设置姿态（四元数）
            pose_msg.pose.orientation.x = quaternion[0]
            pose_msg.pose.orientation.y = quaternion[1]
            pose_msg.pose.orientation.z = quaternion[2]
            pose_msg.pose.orientation.w = quaternion[3]
            
            # 发布TCP位姿
            self.tcp_pose_publisher.publish(pose_msg)
            
            self.get_logger().info(f'Published TCP pose: position={tcp_position.tolist()}, orientation={quaternion.tolist()}')
            
        except Exception as e:
            self.get_logger().error(f'Error processing keypoints: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = ArmController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()