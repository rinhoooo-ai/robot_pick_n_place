"""
simulation.launch.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Main launch file for the Pick and Place simulation.

What this launches:
  1. Gazebo Harmonic  ← world + physics
  2. Robot spawner    ← FR3 into Gazebo
  3. ros2_control     ← joint controllers
  4. robot_state_pub  ← TF tree
  5. RViz2            ← visualization (optional)

Usage:
  ros2 launch pick_n_place_gazebo simulation.launch.py
  ros2 launch pick_n_place_gazebo simulation.launch.py rviz:=false
"""

import os
from ament_python import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription,
    TimerAction, ExecuteProcess
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # ── Package paths ──────────────────────────────────────────
    gazebo_pkg  = get_package_share_directory('pick_n_place_gazebo')
    desc_pkg    = get_package_share_directory('pick_n_place_description')
    ros_gz_pkg  = get_package_share_directory('ros_gz_sim')

    world_file  = os.path.join(gazebo_pkg, 'worlds', 'pick_place_world.sdf')
    xacro_file  = os.path.join(desc_pkg,   'urdf',   'fr3_with_gripper.urdf.xacro')
    ctrl_config = os.path.join(gazebo_pkg, 'config', 'ros2_controllers.yaml')

    # ── Arguments ─────────────────────────────────────────────
    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Launch RViz2 visualization'
    )

    # ── Robot Description (URDF from xacro) ───────────────────
    robot_description = Command(['xacro ', xacro_file, ' use_sim:=true'])

    # ── 1. Gazebo Harmonic ────────────────────────────────────
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_pkg, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items(),
    )

    # ── 2. robot_state_publisher ──────────────────────────────
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )

    # ── 3. Spawn FR3 into Gazebo ──────────────────────────────
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_fr3',
        output='screen',
        arguments=[
            '-name', 'fr3',
            '-topic', 'robot_description',
            '-x', '0.0', '-y', '0.0', '-z', '0.0',
        ],
    )

    # ── 4. ros2_control spawner ───────────────────────────────
    #    Delay by 3s to let Gazebo finish spawning the robot
    joint_state_broadcaster = TimerAction(period=3.0, actions=[
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        )
    ])

    arm_controller = TimerAction(period=4.0, actions=[
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['arm_controller', '--controller-manager', '/controller_manager'],
        )
    ])

    gripper_controller = TimerAction(period=4.5, actions=[
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['gripper_controller', '--controller-manager', '/controller_manager'],
        )
    ])

    # ── 5. RViz2 ─────────────────────────────────────────────
    rviz_config = os.path.join(desc_pkg, 'rviz', 'robot.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen',
    )

    # ── 6. Gazebo ↔ ROS2 bridge ───────────────────────────────
    #    Bridges Gazebo topics → ROS2 topics
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='gz_ros_bridge',
        output='screen',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/camera/color/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/depth/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
        ],
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([
        rviz_arg,
        gazebo,
        rsp,
        spawn_robot,
        gz_bridge,
        joint_state_broadcaster,
        arm_controller,
        gripper_controller,
        rviz,
    ])
