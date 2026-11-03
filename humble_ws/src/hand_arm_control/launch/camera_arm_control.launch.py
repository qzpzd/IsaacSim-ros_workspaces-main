#!/usr/bin/env python3
"""
Launch file for camera-based arm control system
从摄像头检测物体并控制机械臂
"""
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 摄像头物体检测和机械臂控制器节点
        Node(
            package='hand_arm_control',
            executable='camera_arm_controller.py',
            name='camera_arm_controller',
            output='screen',
            arguments=['--ros-args']
        )
    ])