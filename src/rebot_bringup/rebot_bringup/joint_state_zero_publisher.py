import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class ZeroJointStatePublisher(Node):
    """周期性发布全零位关节状态，供 robot_state_publisher 计算各 link 的 TF。"""

    JOINT_NAMES = [
        'joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6',
        'gripper_joint1', 'gripper_joint2',
    ]

    def __init__(self):
        super().__init__('rebot_joint_state_publisher')
        self._publisher = self.create_publisher(JointState, 'joint_states', 10)
        self.create_timer(0.05, self._publish)

    def _publish(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(self.JOINT_NAMES)
        msg.position = [0.0] * len(self.JOINT_NAMES)
        self._publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ZeroJointStatePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
