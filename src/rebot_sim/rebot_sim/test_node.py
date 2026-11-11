import rclpy
from rclpy.node import Node


class SimNode(Node):

    def __init__(self):
        super().__init__('sim_node')
        self.get_logger().info('ReBot Simulation Started!')


def main(args=None):
    rclpy.init(args=args)

    node = SimNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()