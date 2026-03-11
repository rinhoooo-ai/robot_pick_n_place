"""
spawn_blocks.launch.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Spawns N colored blocks on the pick zone of the table.

Usage:
  # Spawn 3 blocks (default)
  ros2 launch pick_n_place_gazebo spawn_blocks.launch.py

  # Spawn 1 block at custom position
  ros2 launch pick_n_place_gazebo spawn_blocks.launch.py x:=0.3 y:=0.1 z:=0.83
"""

import os
from ament_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def spawn_blocks(context, *args, **kwargs):
    gazebo_pkg = get_package_share_directory('pick_n_place_gazebo')
    block_sdf   = os.path.join(gazebo_pkg, 'models', 'block', 'model.sdf')

    # Block spawn positions on the pick zone (green mat area)
    # Table top at z=0.80, block half-height = 0.025 → spawn at z=0.825
    blocks = [
        {'name': 'block_red',   'x':  0.25, 'y':  0.10, 'z': 0.825},
        {'name': 'block_green', 'x':  0.30, 'y':  0.10, 'z': 0.825},
        {'name': 'block_blue',  'x':  0.35, 'y':  0.10, 'z': 0.825},
    ]

    spawn_nodes = []
    for block in blocks:
        spawn_nodes.append(
            Node(
                package='ros_gz_sim',
                executable='create',
                name=f"spawn_{block['name']}",
                output='screen',
                arguments=[
                    '-name', block['name'],
                    '-file', block_sdf,
                    '-x', str(block['x']),
                    '-y', str(block['y']),
                    '-z', str(block['z']),
                ],
            )
        )
    return spawn_nodes


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=spawn_blocks)
    ])
