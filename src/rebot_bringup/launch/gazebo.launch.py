import os
import re
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_dir = get_package_share_directory('rebotarm_description')
    urdf_config = os.path.join(pkg_dir, 'urdf', 'RS', 'urdf', 'ReBot_Arm_RS.urdf')

    bringup_share = get_package_share_directory('rebot_bringup')
    controllers_yaml = os.path.join(bringup_share, 'config', 'rebot_controllers.yaml')

    with open(urdf_config, 'r') as e:
        rebot_description = e.read().replace('__CONTROLLERS_YAML__', controllers_yaml)

    # gazebo_ros2_control 会把整段 robot_description 作为 --param 命令行参数传给
    # controller_manager，XML 注释里的 "Version: 1.6.0" 这类 "冒号+空格" 会破坏
    # rcl 的 YAML 解析（Couldn't parse parameter override rule），这里剔除注释。
    rebot_description = re.sub(r'<!--.*?-->', '', rebot_description, flags=re.S)

    # URDF 里用的是 package://rebotarm_description/...，Gazebo Classic 会把它转成
    # model://rebotarm_description/...，必须在 GAZEBO_MODEL_PATH 里能找到该目录，
    # 否则 mesh 加载失败：既没有视觉模型，也没有碰撞体，机械臂会直接穿过地面掉下去。
    model_root = os.path.dirname(pkg_dir)
    gazebo_model_path = model_root
    if os.environ.get('GAZEBO_MODEL_PATH'):
        gazebo_model_path += ':' + os.environ['GAZEBO_MODEL_PATH']

    set_gazebo_model_path = SetEnvironmentVariable('GAZEBO_MODEL_PATH', gazebo_model_path)

    gazebo_classic = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py'))

    )

    get_joints = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[{'robot_description': rebot_description}],
        output='screen'
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'rebot_arm',
            '-x', '0',
            '-y', '0',
            '-z', '0'
        ],
        output='screen'
    )

    # 控制器由 gzserver 里的 gazebo_ros2_control 插件加载，必须等模型 spawn 完成后再拉起
    jsb_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager-timeout', '60'],
        output='screen'
    )

    arm_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller', '--controller-manager-timeout', '60'],
        output='screen'
    )

    gripper_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['gripper_controller', '--controller-manager-timeout', '60'],
        output='screen'
    )

    load_jsb_after_spawn = RegisterEventHandler(
        OnProcessExit(target_action=spawn_entity, on_exit=[jsb_spawner])
    )
    load_arm_after_jsb = RegisterEventHandler(
        OnProcessExit(target_action=jsb_spawner, on_exit=[arm_spawner])
    )
    load_gripper_after_arm = RegisterEventHandler(
        OnProcessExit(target_action=arm_spawner, on_exit=[gripper_spawner])
    )

    return LaunchDescription([
        set_gazebo_model_path,
        gazebo_classic,
        get_joints,
        spawn_entity,
        load_jsb_after_spawn,
        load_arm_after_jsb,
        load_gripper_after_arm,
    ])
