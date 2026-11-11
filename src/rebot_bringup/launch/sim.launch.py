#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    node = Node(package="rebot_sim", executable="test_node")

    return LaunchDescription([node])


if __name__ == "__main__":
    generate_launch_description()