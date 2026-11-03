# ... existing code ...

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(control_msgs REQUIRED)

# ... existing code ...

catkin_install_python(PROGRAMS
  scripts/arm_controller.py
  scripts/camera_publisher.py
  scripts/hand_keypoint_detector.py
  scripts/camera_arm_controller.py
  scripts/hand_arm_controller.py
  scripts/test_system.py
  scripts/hand_to_moveit_bridge.py
  DESTINATION lib/${PROJECT_NAME}
)

# ... existing code ...cmake_minimum_required(VERSION 3.5)
project(hand_arm_control)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # uncomment the line when a copyright and license is not present in all source files
  #set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # uncomment the line when this package is not in a git repo
  #set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# Install scripts and launch files
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})

# Install Python scripts as executables
catkin_install_python(PROGRAMS
  scripts/arm_controller.py
  scripts/camera_publisher.py
  scripts/hand_keypoint_detector.py
  scripts/camera_arm_controller.py
  scripts/hand_arm_controller.py
  scripts/test_system.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()