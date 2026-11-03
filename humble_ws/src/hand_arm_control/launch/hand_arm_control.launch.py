from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    # 获取isaac_moveit的启动文件路径
    isaac_moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('isaac_moveit'),
                'launch',
                'isaac_moveit.launch.py'
            )
        ),
        launch_arguments={'use_sim_time': 'true'}.items()
    )
    
    return LaunchDescription([
        # 启动Isaac MoveIt
        isaac_moveit_launch,
        
        # 相机发布器
        Node(
            package='hand_arm_control',
            executable='camera_publisher.py',
            name='camera_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': True
            }]
        ),
        
        # 手部关键点检测器
        Node(
            package='hand_arm_control',
            executable='hand_keypoint_detector.py',
            name='hand_keypoint_detector',
            output='screen',
            parameters=[{
                'use_sim_time': True
            }]
        ),
        
        # TCP末端位姿计算器
        Node(
            package='hand_arm_control',
            executable='arm_controller.py',
            name='arm_controller',
            output='screen',
            parameters=[{
                'use_sim_time': True
            }]
        ),
        
        # MoveIt控制器
        Node(
            package='hand_arm_control',
            executable='moveit_arm_controller.py',
            name='moveit_arm_controller',
            output='screen',
            parameters=[{
                'use_sim_time': True
            }]
        )
    ])