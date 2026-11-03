#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge
import cv2
import numpy as np
import time

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


class HandArmController(Node):
    def __init__(self):
        super().__init__('hand_arm_controller')
        
        self.bridge = CvBridge()
        
        self.image_subscription = self.create_subscription(
            Image, '/webcam/image_raw', self.image_callback, 10
        )
        
        self.joint_publisher = self.create_publisher(
            Float32MultiArray, '/arm_joint_positions', 10
        )

        self.num_joints = 9
        self.current_joint_positions = np.zeros(self.num_joints)
        self.target_joint_positions = np.zeros(self.num_joints)

        # 初始安全位（避免从0开始不动）
        self.current_joint_positions[:7] = [0.0, -0.6, 0.2, -1.4, 0.0, 1.0, 0.0]
        self.target_joint_positions[:7] = self.current_joint_positions[:7].copy()

        # 夹爪默认张开
        self.target_joint_positions[7] = 0.04
        self.target_joint_positions[8] = 0.04

        self.previous_hand_center = None
        self.last_detection_time = time.time()
        self.detection_interval = 0.04

        # ====================== 灵敏度拉满 ======================
        self.speed_scale = 1.4
        self.smoothing_factor = 0.7
        self.joint_gain = 1.5

        # MediaPipe
        if MEDIAPIPE_AVAILABLE:
            self.mp_hands = mp.solutions.hands.Hands(
                static_image_mode=False, max_num_hands=1,
                min_detection_confidence=0.6, min_tracking_confidence=0.4
            )
            self.mp_draw = mp.solutions.drawing_utils

        self.get_logger().info('✅ 高灵敏度 TCP 控制器已启动')

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            if time.time() - self.last_detection_time > self.detection_interval:
                self.detect_hand_and_control(cv_image)
                self.last_detection_time = time.time()
            cv2.waitKey(1)
        except Exception as e:
            self.get_logger().error(f'图像错误: {e}')

    def detect_hand_and_control(self, cv_image):
        if not MEDIAPIPE_AVAILABLE:
            return

        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        results = self.mp_hands.process(rgb_image)

        if results.multi_hand_landmarks:
            for hand_lm in results.multi_hand_landmarks:
                hand_center = self.get_hand_3d_position(hand_lm, cv_image.shape)

                if self.previous_hand_center is not None:
                    delta = hand_center - self.previous_hand_center
                    self.update_arm_by_tcp_velocity(delta)

                self.previous_hand_center = hand_center.copy()
                self.send_joint_command()
                self.draw_ui(cv_image, hand_lm, hand_center)
        else:
            self.send_joint_command()
            cv2.putText(cv_image, "No Hand", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

        cv2.imshow("Hand TCP Controller", cv_image)

    def get_hand_3d_position(self, landmarks, img_shape):
        h, w = img_shape[:2]
        tip = landmarks.landmark[12]
        # 放大映射范围
        x = (tip.x - 0.5) * 2.8
        y = (tip.y - 0.5) * 2.8
        z = 0.2 + (1 - tip.z) * 1.2
        return np.array([x, y, z])

    def update_arm_by_tcp_velocity(self, delta):
        dx, dy, dz = delta * self.speed_scale

        tcp_vel = np.zeros(6)
        tcp_vel[0] = -dy * 2.0
        tcp_vel[1] = -dx * 2.0
        tcp_vel[2] =  dz * 2.0

        J = self.get_simplified_jacobian()
        J_pinv = np.linalg.pinv(J)
        joint_vel = J_pinv @ tcp_vel

        joint_vel *= self.joint_gain

        new_joints = self.current_joint_positions[:7] + joint_vel * self.smoothing_factor
        new_joints = np.clip(new_joints, -2.4, 2.4)

        self.target_joint_positions[:7] = new_joints

    def get_simplified_jacobian(self):
        q = self.current_joint_positions[:7]
        q1, q2, q3, q4, q5, q6, q7 = q
        return np.array([
            [0, -np.sin(q1), np.sin(q1), 0, 0, 0, 0],
            [0,  np.cos(q1),-np.cos(q1), 0, 0, 0, 0],
            [1,  0, 0, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ], dtype=np.float32)

    def send_joint_command(self):
        self.current_joint_positions = self.target_joint_positions.copy()
        msg = Float32MultiArray()
        msg.data = self.current_joint_positions.tolist()
        self.joint_publisher.publish(msg)

    def draw_ui(self, img, landmarks, pos):
        self.mp_draw.draw_landmarks(img, landmarks, mp.solutions.hands.HAND_CONNECTIONS)
        text = f"TCP X:{pos[0]:.1f} Y:{pos[1]:.1f} Z:{pos[2]:.1f}"
        cv2.putText(img, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)


def main(args=None):
    rclpy.init(args=args)
    node = HandArmController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()