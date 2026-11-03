from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    # 启动官方MoveIt
    isaac_moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_directory('isaac_moveit'),
            '/launch/isaac_moveit.launch.py'
        ]),
        launch_arguments={
            'use_sim_time': 'true',
            'ros2_control_hardware_type': 'isaac'
        }.items()
    )
    
    # 启动手部到MoveIt桥接节点
    hand_to_moveit_node = Node(
        package='hand_arm_control',
        executable='hand_to_moveit_bridge.py',
        name='hand_to_moveit_bridge',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )
    
    return LaunchDescription([
        isaac_moveit_launch,
        hand_to_moveit_node,
    ])