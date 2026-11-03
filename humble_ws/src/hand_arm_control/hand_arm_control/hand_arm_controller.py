#!/usr/bin/env python3
"""
Hand to MoveIt Bridge
将手部检测到的位姿转换为MoveIt规划目标
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge
import numpy as np
import mediapipe as mp

# MoveIt相关
from moveit_msgs.action import MoveGroup
from rclpy.action import ActionClient
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory


class HandToMoveItBridge(Node):
    def __init__(self):
        super().__init__('hand_to_moveit_bridge')
        
        self.bridge = CvBridge()
        
        # 订阅摄像头图像
        self.image_sub = self.create_subscription(
            Image,
            '/webcam/image_raw',
            self.image_callback,
            10
        )
        
        # 初始化MediaPipe Hands
        self.mp_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # MoveIt action client
        self.move_action_client = ActionClient(
            self,
            MoveGroup,
            'move_action'
        )
        
        # 或者直接发布到joint_trajectory_controller
        self.trajectory_pub = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            10
        )
        
        # 手部状态
        self.current_pose = None
        self.last_command_time = self.get_clock().now()
        self.command_interval = 0.5  # 每0.5秒发送一次命令
        
        self.get_logger().info('Hand to MoveIt Bridge initialized')
    
    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.detect_hand_and_plan(cv_image)
        except Exception as e:
            self.get_logger().error(f'Error: {str(e)}')
    
    def detect_hand_and_plan(self, cv_image):
        """检测手部并调用MoveIt规划"""
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        results = self.mp_hands.process(rgb_image)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 获取手腕和指尖位置
                wrist = hand_landmarks.landmark[0]
                middle_tip = hand_landmarks.landmark[12]
                
                # 转换为目标位姿
                target_pose = self.hand_to_pose(wrist, middle_tip)
                
                # 检查是否需要发送新命令
                now = self.get_clock().now()
                if (now - self.last_command_time).nanoseconds / 1e9 > self.command_interval:
                    # 方法1: 使用MoveIt Action
                    # self.send_moveit_goal(target_pose)
                    
                    # 方法2: 直接发布轨迹（简化版）
                    self.publish_simple_trajectory(target_pose)
                    self.last_command_time = now
    
    def hand_to_pose(self, wrist, fingertip):
        """将手部关键点转换为机械臂末端位姿"""
        pose = PoseStamped()
        pose.header.frame_id = 'world'
        pose.header.stamp = self.get_clock().now().to_msg()
        
        # 简化的坐标映射（需要根据实际标定调整）
        pose.pose.position.x = (wrist.x - 0.5) * 1.0
        pose.pose.position.y = (wrist.y - 0.5) * 1.0
        pose.pose.position.z = 0.3 + (1.0 - wrist.z) * 0.4
        
        # 简单的朝向计算
        dx = fingertip.x - wrist.x
        dy = fingertip.y - wrist.y
        angle = np.arctan2(dy, dx)
        
        from tf_transformations import quaternion_from_euler
        q = quaternion_from_euler(0, 0, angle)
        pose.pose.orientation.x = q[0]
        pose.pose.orientation.y = q[1]
        pose.pose.orientation.z = q[2]
        pose.pose.orientation.w = q[3]
        
        return pose
    
    def send_moveit_goal(self, target_pose):
        """通过MoveIt Action发送规划目标"""
        if not self.move_action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn('MoveIt action server not available')
            return
        
        goal_msg = MoveGroup.Goal()
        goal_msg.request.workspace_parameters.header.frame_id = 'world'
        goal_msg.request.workspace_parameters.min_corner.x = -0.5
        goal_msg.request.workspace_parameters.min_corner.y = -0.5
        goal_msg.request.workspace_parameters.min_corner.z = 0.0
        goal_msg.request.workspace_parameters.max_corner.x = 0.5
        goal_msg.request.workspace_parameters.max_corner.y = 0.5
        goal_msg.request.workspace_parameters.max_corner.z = 1.0
        
        goal_msg.request.goal_constraints.append(
            self.create_pose_constraint(target_pose)
        )
        
        self._send_goal_future = self.move_action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)
    
    def create_pose_constraint(self, pose):
        """创建位姿约束"""
        from moveit_msgs.msg import Constraints, PositionConstraint, OrientationConstraint, BoundingVolume
        from shape_msgs.msg import SolidPrimitive
        
        constraints = Constraints()
        
        # 位置约束
        pos_constraint = PositionConstraint()
        pos_constraint.header.frame_id = 'world'
        pos_constraint.link_name = 'panda_link8'
        pos_constraint.constraint_region.primitives.append(SolidPrimitive())
        pos_constraint.constraint_region.primitives[0].type = SolidPrimitive.SPHERE
        pos_constraint.constraint_region.primitives[0].dimensions = [0.01]
        pos_constraint.constraint_region.primitive_poses.append(pose.pose)
        pos_constraint.weight = 1.0
        
        constraints.position_constraints.append(pos_constraint)
        
        return constraints
    
    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected')
            return
        
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)
    
    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Motion planning result: {result.error_code.val}')
    
    def publish_simple_trajectory(self, target_pose):
        """简化版：直接发布关节轨迹（不使用MoveIt规划）"""
        # 这里应该使用逆运动学计算关节角度
        # 为了简化，暂时使用固定值
        joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
        ]
        
        trajectory = JointTrajectory()
        trajectory.joint_names = joint_names
        
        point = JointTrajectoryPoint()
        # TODO: 根据target_pose计算逆运动学
        point.positions = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
        point.time_from_start.sec = 2
        
        trajectory.points.append(point)
        
        self.trajectory_pub.publish(trajectory)
        self.get_logger().info('Published simple trajectory')


def main(args=None):
    rclpy.init(args=args)
    node = HandToMoveItBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()