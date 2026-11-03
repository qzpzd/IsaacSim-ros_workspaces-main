#!/usr/bin/env python3
"""
系统测试脚本 - 验证摄像头机械臂控制系统
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from trajectory_msgs.msg import JointTrajectory
import time

class SystemTester(Node):
    def __init__(self):
        super().__init__('system_tester')
        
        self.camera_detected = False
        self.arm_controller_detected = False
        self.camera_message_count = 0
        self.arm_message_count = 0
        
        # 测试摄像头订阅
        self.camera_sub = self.create_subscription(
            Image,
            '/webcam/image_raw',
            self.camera_callback,
            10
        )
        
        # 测试机械臂话题
        self.arm_sub = self.create_subscription(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            self.arm_callback,
            10
        )
        
        # 测试发布
        self.test_publisher = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            10
        )
        
        self.start_time = time.time()
        self.test_duration = 10  # 测试10秒
        
        self.get_logger().info('系统测试启动')
        self.get_logger().info(f'测试持续时间: {self.test_duration}秒')
    
    def camera_callback(self, msg):
        if not self.camera_detected:
            self.camera_detected = True
            self.get_logger().info('✓ 摄像头话题正常工作')
            self.get_logger().info(f'  图像尺寸: {msg.width}x{msg.height}')
            self.get_logger().info(f'  编码格式: {msg.encoding}')
        
        self.camera_message_count += 1
    
    def arm_callback(self, msg):
        if not self.arm_controller_detected:
            self.arm_controller_detected = True
            self.get_logger().info('✓ 机械臂话题正常工作')
            self.get_logger().info(f'  关节数量: {len(msg.joint_names)}')
            self.get_logger().info(f'  关节名称: {msg.joint_names}')
        
        self.arm_message_count += 1
    
    def test_arm_publisher(self):
        """测试机械臂发布器"""
        from trajectory_msgs.msg import JointTrajectoryPoint
        
        trajectory_msg = JointTrajectory()
        trajectory_msg.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
        ]
        
        point = JointTrajectoryPoint()
        point.positions = [0.0, -0.5, 0.5, 0.0, 0.5, 0.0, 0.0]
        point.time_from_start.sec = 1
        
        trajectory_msg.points.append(point)
        
        self.test_publisher.publish(trajectory_msg)
        self.get_logger().info('✓ 测试轨迹消息已发布')
    
    def print_results(self):
        """打印测试结果"""
        print("\n" + "="*50)
        print("系统测试结果")
        print("="*50)
        
        print(f"测试时长: {time.time() - self.start_time:.1f}秒")
        print(f"\n摄像头测试:")
        print(f"  状态: {'✓ 正常' if self.camera_detected else '✗ 失败'}")
        print(f"  消息数量: {self.camera_message_count}")
        print(f"  频率: {self.camera_message_count/(time.time() - self.start_time):.1f} Hz")
        
        print(f"\n机械臂测试:")
        print(f"  状态: {'✓ 正常' if self.arm_controller_detected else '✗ 失败'}")
        print(f"  消息数量: {self.arm_message_count}")
        
        print(f"\n总体状态:")
        if self.camera_detected and self.arm_controller_detected:
            print("  ✓ 系统运行正常")
            print("  ✓ 可以开始使用")
        else:
            print("  ✗ 系统存在问题")
            if not self.camera_detected:
                print("  ✗ 摄像头话题不可用")
            if not self.arm_controller_detected:
                print("  ✗ 机械臂话题不可用")
        
        print("="*50)

def main(args=None):
    rclpy.init(args=args)
    node = SystemTester()
    
    try:
        # 运行测试
        while time.time() - node.start_time < node.test_duration:
            rclpy.spin_once(node, timeout_sec=0.1)
            
            # 每5秒测试一次发布器
            if int(time.time() - node.start_time) % 5 == 0:
                node.test_arm_publisher()
                time.sleep(0.1)
        
        # 打印结果
        node.print_results()
        
    except KeyboardInterrupt:
        print("\n测试被中断")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()