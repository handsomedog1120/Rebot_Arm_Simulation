#!/usr/bin/env python3
"""
Gazebo + MoveIt2 联合启动：用 MoveIt 规划并控制 Gazebo 里的机械臂。

架构：
  - rebot_bringup/gazebo.launch.py：启动 Gazebo Classic + 生成机械臂 +
    gazebo_ros2_control 插件（GazeboSystem）加载 arm_controller /
    gripper_controller / joint_state_broadcaster，并暴露
    /arm_controller/follow_joint_trajectory 和
    /gripper_controller/follow_joint_trajectory action。
  - move_group：读取 moveit_controllers.yaml，把规划结果以 FollowJointTrajectory
    形式发给上面这两个 Gazebo 控制器。**不启动** FakeSystem ros2_control_node，
    避免出现两套 controller_manager 抢占 /joint_states。
  - rviz2：加载 MoveIt MotionPlanning 插件，用于交互规划与执行。
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    bringup_share = get_package_share_directory('rebot_bringup')
    moveit_share = get_package_share_directory('rebot_arm_moveit_config')

    # ---------- 1. Gazebo + 真实 ros2_control 控制器 ----------
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'gazebo.launch.py')
        )
    )

    # ---------- 2. MoveIt move_group（对接 Gazebo 控制器） ----------
    moveit_config = (
        MoveItConfigsBuilder("ReBot_Arm_RS", package_name="rebot_arm_moveit_config")
        .robot_description(file_path=os.path.join(moveit_share, 'config', 'ReBot_Arm_RS.urdf.xacro'))
        .robot_description_semantic(file_path=os.path.join(moveit_share, 'config', 'ReBot_Arm_RS.srdf'))
        .trajectory_execution(file_path=os.path.join(moveit_share, 'config', 'moveit_controllers.yaml'))
        .planning_scene_monitor(
            # 不发布 robot_description：robot_state_publisher 已发布含 gazebo_ros2_control
            # 插件块的 URDF。若 move_group 再发布 MoveIt 的 FakeSystem URDF，
            # spawn_entity 可能读到不含插件块的版本，导致 Gazebo 不加载控制器。
            publish_robot_description=False,
            publish_robot_description_semantic=True,
        )
        .to_moveit_configs()
    )

    # move_group 必须用 Gazebo 的仿真时钟，否则轨迹时间戳对不上
    moveit_config.moveit_cpp.update({"use_sim_time": True})

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
        arguments=["--ros-args", "--log-level", "info"],
    )

    # ---------- 3. RViz + MoveIt MotionPlanning 插件 ----------
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", os.path.join(moveit_share, 'config', 'moveit.rviz')],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            {"use_sim_time": True},
        ],
    )

    return LaunchDescription([
        gazebo_launch,
        move_group_node,
        rviz_node,
    ])
