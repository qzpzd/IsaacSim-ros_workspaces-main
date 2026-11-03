from setuptools import setup

package_name = 'hand_arm_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/camera_arm_control.launch.py',
                                                 'launch/hand_arm_control.launch.py',
                                                 'launch/hand_arm_with_moveit.launch.py']),
        ('share/' + package_name + '/scripts', ['scripts/arm_controller.py',
                                                  'scripts/camera_publisher.py',
                                                  'scripts/hand_keypoint_detector.py',
                                                  'scripts/camera_arm_controller.py',
                                                  'scripts/hand_arm_controller.py',
                                                  'scripts/test_system.py',
                                                  'scripts/moveit_arm_controller.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Isaac Sim',
    maintainer_email='isaac-sim-maintainers@nvidia.com',
    description='Hand and Arm Control Package',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'hand_arm_controller = hand_arm_control.hand_arm_controller:main',
        ],
    },
)