"""
launch/perception.launch.py
Launch block_detector node with camera parameters.

Usage:
  ros2 launch pick_n_place_perception perception.launch.py
  ros2 launch pick_n_place_perception perception.launch.py debug:=true
"""

import os
from ament_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('pick_n_place_perception')
    params = os.path.join(pkg, 'config', 'camera_params.yaml')

    return LaunchDescription([
        DeclareLaunchArgument(
            'debug', default_value='false',
            description='Publish debug overlay image to /camera/debug_image'
        ),

        Node(
            package='pick_n_place_perception',
            executable='block_detector',
            name='block_detector',
            output='screen',
            parameters=[
                params,
                {'use_sim_time': True},
            ],
        ),
    ])
