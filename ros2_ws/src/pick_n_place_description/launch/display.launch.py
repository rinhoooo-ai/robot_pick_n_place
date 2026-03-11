"""
display.launch.py
Launch robot_state_publisher + joint_state_publisher_gui + RViz2
to preview and debug the FR3 URDF — run this BEFORE Gazebo to verify
the robot model looks correct.

Usage:
  ros2 launch pick_n_place_description display.launch.py
"""

import os
from ament_python import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('pick_n_place_description')
    xacro_file = os.path.join(pkg, 'urdf', 'fr3_with_gripper.urdf.xacro')

    robot_description = Command(['xacro ', xacro_file, ' use_sim:=false'])

    return LaunchDescription([

        # Publishes TF from joint states + URDF
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description}],
        ),

        # GUI sliders to move joints manually
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            name='joint_state_publisher_gui',
            output='screen',
        ),

        # RViz2 — no config file needed for simple preview
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
        ),
    ])
