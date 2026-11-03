#!/usr/bin/env python3
"""
Arm controller node that uses MoveIt for inverse kinematics
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from moveit_commander import MoveGroupCommander
import numpy as np

class MoveItArmController(Node):
    def __init__(self):
        super().__init__('moveit_arm_controller')
        
        # 订阅TCP位姿话题
        self.tcp_pose_subscriber = self.create_subscription(
            PoseStamped,
            '/tcp_pose',
            self.tcp_pose_callback,
            10
        )
        
        # 发布关节轨迹话题
        self.trajectory_publisher = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            10
        )
        
        # 机械臂关节名称
        self.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
        ]
        
        # 初始化MoveIt
        self.move_group = MoveGroupCommander('panda_arm')
        self.move_group.set_planning_time(1.0)
        self.move_group.set_num_planning_attempts(10)
        
        self.get_logger().info('MoveIt arm controller node started')
    
    def tcp_pose_callback(self, msg):
        try:
            # 设置目标位姿
            self.move_group.set_pose_target(msg)
            
            # 规划路径
            plan = self.move_group.plan()
            
            if not plan:
                self.get_logger().warn('Failed to plan path')
                return
            
            # 执行规划
            success = self.move_group.execute(plan, wait=True)
            
            if success:
                # 获取规划的关节位置
                joint_positions = self.move_group.get_current_joint_values()
                
                # 创建关节轨迹消息
                trajectory_msg = JointTrajectory()
                trajectory_msg.joint_names = self.joint_names
                
                # 创建轨迹点
                point = JointTrajectoryPoint()
                point.positions = joint_positions
                point.velocities = [0.0] * len(self.joint_names)
                point.accelerations = [0.0] * len(self.joint_names)
                point.time_from_start.sec = 1  # 1秒内完成移动
                
                trajectory_msg.points.append(point)
                
                # 发布轨迹消息
                self.trajectory_publisher.publish(trajectory_msg)
                
                self.get_logger().info(f'Executed MoveIt plan successfully: {joint_positions}')
            else:
                self.get_logger().warn('Failed to execute plan')
                
        except Exception as e:
            self.get_logger().error(f'Error processing TCP pose: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = MoveItArmController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()