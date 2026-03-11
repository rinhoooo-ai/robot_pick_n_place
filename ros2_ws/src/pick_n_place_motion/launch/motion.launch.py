"""
launch/motion.launch.py
Launch pick_place_node with MoveIt2 parameters.

Run AFTER:
  1. ros2 launch pick_n_place_gazebo simulation.launch.py
  2. ros2 launch pick_n_place_perception perception.launch.py

Usage:
  ros2 launch pick_n_place_motion motion.launch.py
"""

import os
from ament_python import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('pick_n_place_motion')
    params = os.path.join(pkg, 'config', 'moveit_params.yaml')

    return LaunchDescription([
        Node(
            package='pick_n_place_motion',
            executable='pick_place_node',
            name='pick_place_node',
            output='screen',
            parameters=[
                params,
                {'use_sim_time': True},
            ],
        ),
    ])
