import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_dir = get_package_share_directory('rebotarm_description')
    urdf_config = os.path.join(pkg_dir, 'urdf', 'RS', 'urdf', 'ReBot_Arm_RS.urdf')

    bringup_dir = get_package_share_directory('rebot_bringup')
    rviz_config = os.path.join(bringup_dir, 'rviz', 'rebot_arm.rviz')

    with open(urdf_config, 'r') as infp:
        rebot_description = infp.read()

    get_description = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': rebot_description}],
    )
    # get_joint_states = Node(
    #     package='rebot_bringup',
    #     executable='joint_state_zero_publisher',
    #     name='joint_state_zero_publisher',
    # )

    get_joint_states = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
    )
    get_rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
    )

    return LaunchDescription([get_description, get_joint_states, get_rviz])
