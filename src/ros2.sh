colcon build

cd /home/realvm/Rebot_Arm_Simulation-main

source install/setup.bash

gpu-run ros2 launch rebot_bringup gazebo_moveit.launch.py