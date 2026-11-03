#!/usr/bin/env python3
"""
Camera publisher node that reads from webcam or simulated camera
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import platform

class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')
        
        # 发布相机图像话题
        self.image_publisher = self.create_publisher(
            Image,
            '/camera/image_raw',
            10
        )
        
        # 初始化 CV Bridge
        self.bridge = CvBridge()
        
        # 初始化相机
        self.cap = None
        self.initialize_camera()
        
        # 创建定时器，定期发布图像
        self.timer = self.create_timer(0.033, self.publish_image)  # 约 30 FPS
        
        self.get_logger().info('Camera publisher node started')
        self.get_logger().info(f'Running on platform: {platform.system()}')
    
    def initialize_camera(self):
        """初始化相机，尝试不同的相机索引"""
        system = platform.system()
        
        # 尝试不同的相机索引
        for index in range(5):  # 尝试前5个相机索引
            self.get_logger().info(f'Trying camera index: {index}')
            self.cap = cv2.VideoCapture(index)
            
            if self.cap.isOpened():
                # 设置相机分辨率
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                # Windows平台特定设置
                if system == 'Windows':
                    # 尝试设置视频捕获属性
                    self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                
                self.get_logger().info(f'Successfully opened camera at index {index}')
                return
        
        # 所有相机索引都尝试失败
        self.get_logger().error('Failed to open any camera')
        self.get_logger().info('Running in fallback mode - publishing empty images')
    
    def publish_image(self):
        try:
            if self.cap is not None and self.cap.isOpened():
                # 读取相机图像
                ret, frame = self.cap.read()
                
                if not ret:
                    self.get_logger().warn('Failed to read frame from camera')
                    return
            else:
                # 相机未打开，创建空图像
                frame = cv2.zeros((480, 640, 3), dtype=cv2.CV_8UC3)
                self.get_logger().warn('Using fallback empty image')
            
            # 将 OpenCV 图像转换为 ROS 图像消息
            image_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            
            # 发布图像消息
            self.image_publisher.publish(image_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error publishing image: {str(e)}')
    
    def destroy_node(self):
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = CameraPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()