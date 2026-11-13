from launch import LaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node


def generate_launch_description():
    # ros2_control Humble 的 spawner 在并行启动时存在竞态：
    # list_controllers 会返回仅在参数中定义但尚未实例化的控制器，
    # 导致 spawner 误判 "already loaded" 而跳过 load_controller，
    # 随后 configure_controller 报 "no controller with this name exists"。
    # 这里用 OnProcessExit 把三个 spawner 串成串行链，彻底避免竞态。
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager-timeout", "60"],
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller", "--controller-manager-timeout", "60"],
    )

    gripper_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "--controller-manager-timeout", "60"],
    )

    # joint_state_broadcaster 先启动，arm_controller 等它结束，
    # gripper_controller 再等 arm_controller 结束。
    load_arm_after_jsb = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[arm_controller_spawner],
        )
    )

    load_gripper_after_arm = RegisterEventHandler(
        OnProcessExit(
            target_action=arm_controller_spawner,
            on_exit=[gripper_controller_spawner],
        )
    )

    return LaunchDescription(
        [
            joint_state_broadcaster_spawner,
            load_arm_after_jsb,
            load_gripper_after_arm,
        ]
    )
