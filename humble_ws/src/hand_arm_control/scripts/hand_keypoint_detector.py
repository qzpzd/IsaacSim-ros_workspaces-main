#!/usr/bin/env python3
"""
Hand keypoint detector node using MediaPipe
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from custom_message.msg import HandKeypoints
from geometry_msgs.msg import Point
import cv2
import mediapipe as mp
import numpy as np
from cv_bridge import CvBridge

class HandKeypointDetector(Node):
    def __init__(self):
        super().__init__('hand_keypoint_detector')
        
        # 订阅相机图像话题
        self.image_subscriber = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )
        
        # 发布手关键点话题
        self.keypoints_publisher = self.create_publisher(
            HandKeypoints,
            '/hand_keypoints',
            10
        )
        
        # 初始化 MediaPipe 手部检测
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 初始化 CV Bridge
        self.bridge = CvBridge()
        
        self.get_logger().info('Hand keypoint detector node started')
    
    def image_callback(self, msg):
        try:
            # 将 ROS 图像消息转换为 OpenCV 图像
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # 处理图像
            image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            results = self.hands.process(image_rgb)
            
            # 如果检测到手
            if results.multi_hand_landmarks:
                for hand_landmarks, handness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    # 创建手关键点消息
                    keypoints_msg = HandKeypoints()
                    
                    # 提取关键点
                    for landmark in hand_landmarks.landmark:
                        point = Point()
                        point.x = landmark.x
                        point.y = landmark.y
                        point.z = landmark.z
                        keypoints_msg.keypoints.append(point)
                    
                    # 提取手的类型（左手/右手）
                    keypoints_msg.handness = 1 if handness.classification[0].label == 'Right' else 0
                    
                    # 提取置信度
                    keypoints_msg.confidence = handness.classification[0].score
                    
                    # 发布消息
                    self.keypoints_publisher.publish(keypoints_msg)
                    
                    # 可选：在图像上绘制关键点
                    # self.draw_keypoints(cv_image, hand_landmarks)
            
        except Exception as e:
            self.get_logger().error(f'Error processing image: {str(e)}')
    
    def draw_keypoints(self, image, hand_landmarks):
        """在图像上绘制手关键点"""
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing.draw_landmarks(
            image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
        )
        cv2.imshow('Hand Keypoints', image)
        cv2.waitKey(1)
    
    def destroy_node(self):
        self.hands.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = HandKeypointDetector()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()