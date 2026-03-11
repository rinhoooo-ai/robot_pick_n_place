#!/usr/bin/env python3
"""
pick_place_node.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pick and Place state machine using MoveIt2 Python API.

State Machine:
  IDLE ──► DETECT ──► PRE_GRASP ──► GRASP ──► LIFT
                                                 │
  IDLE ◄── PLACE ◄── PRE_PLACE ◄── TRANSPORT ◄──┘

Topics:
  SUB: /block_poses  geometry_msgs/PoseArray  (from perception node)
  PUB: /pick_place_status  std_msgs/String    (current state)

Actions used:
  /fr3/arm_controller/follow_joint_trajectory
  /fr3/gripper_controller/gripper_action
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from enum import Enum, auto

from geometry_msgs.msg import PoseArray, Pose, PoseStamped
from std_msgs.msg import String
from control_msgs.action import FollowJointTrajectory, GripperCommand
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

# MoveIt2 Python bindings
from moveit.planning import MoveItPy
from moveit.core.robot_state import RobotState


class State(Enum):
    IDLE        = auto()
    DETECT      = auto()
    PRE_GRASP   = auto()
    GRASP       = auto()
    LIFT        = auto()
    TRANSPORT   = auto()
    PRE_PLACE   = auto()
    PLACE       = auto()


# ── Robot configuration ──────────────────────────────────────────────────

# Joint names for FR3
JOINT_NAMES = [
    'fr3_joint1', 'fr3_joint2', 'fr3_joint3', 'fr3_joint4',
    'fr3_joint5', 'fr3_joint6', 'fr3_joint7'
]

# Home/ready pose (arm up, clear of table)
HOME_JOINTS = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]

# Place target: fixed position on the red mat
PLACE_POSE = Pose()
PLACE_POSE.position.x    =  0.30
PLACE_POSE.position.y    = -0.25
PLACE_POSE.position.z    =  0.90   # hover height above table
PLACE_POSE.orientation.w =  1.0

# Pre-grasp hover height above block (meters)
PRE_GRASP_OFFSET_Z = 0.15


class PickPlaceNode(Node):
    """
    Orchestrates pick and place using MoveIt2 + ROS2 actions.
    """

    def __init__(self):
        super().__init__('pick_place_node')

        # ── MoveIt2 ───────────────────────────────────────────
        self.moveit = MoveItPy(node_name='pick_place_moveit')
        self.arm    = self.moveit.get_planning_component('fr3_arm')

        # ── Action clients ────────────────────────────────────
        self._arm_client = ActionClient(
            self, FollowJointTrajectory,
            '/fr3/arm_controller/follow_joint_trajectory'
        )
        self._gripper_client = ActionClient(
            self, GripperCommand,
            '/fr3/gripper_controller/gripper_action'
        )

        # ── State ─────────────────────────────────────────────
        self.state         = State.IDLE
        self.target_block  = None   # geometry_msgs/Pose of block to pick
        self.block_queue   = []     # queue of detected block poses

        # ── ROS2 interfaces ───────────────────────────────────
        self.create_subscription(
            PoseArray, '/block_poses',
            self.block_poses_callback, 10
        )
        self.status_pub = self.create_publisher(String, '/pick_place_status', 10)

        # State machine runs at 2 Hz
        self.create_timer(0.5, self.state_machine_tick)

        self.get_logger().info('PickPlaceNode started — waiting for blocks...')

    # ── Subscriber ────────────────────────────────────────────────────────

    def block_poses_callback(self, msg: PoseArray):
        """Update block queue from perception node."""
        self.block_queue = list(msg.poses)

    # ── State Machine ─────────────────────────────────────────────────────

    def state_machine_tick(self):
        """Called at 2 Hz — drives the state machine."""
        self._publish_status(self.state.name)

        if self.state == State.IDLE:
            self._transition_to(State.DETECT)

        elif self.state == State.DETECT:
            if self.block_queue:
                # Pick the first (closest) block
                self.target_block = self.block_queue[0]
                self.get_logger().info(
                    f'Target block at ({self.target_block.position.x:.3f}, '
                    f'{self.target_block.position.y:.3f}, '
                    f'{self.target_block.position.z:.3f})'
                )
                self._transition_to(State.PRE_GRASP)
            else:
                self.get_logger().info('No blocks detected — waiting...', throttle_duration_sec=3.0)

        elif self.state == State.PRE_GRASP:
            success = self._move_to_cartesian(
                x=self.target_block.position.x,
                y=self.target_block.position.y,
                z=self.target_block.position.z + PRE_GRASP_OFFSET_Z,
            )
            if success:
                self._open_gripper()
                self._transition_to(State.GRASP)

        elif self.state == State.GRASP:
            # Move straight down to block
            success = self._move_to_cartesian(
                x=self.target_block.position.x,
                y=self.target_block.position.y,
                z=self.target_block.position.z + 0.01,  # just above surface
            )
            if success:
                self._close_gripper()
                self._transition_to(State.LIFT)

        elif self.state == State.LIFT:
            # Lift straight up
            success = self._move_to_cartesian(
                x=self.target_block.position.x,
                y=self.target_block.position.y,
                z=self.target_block.position.z + PRE_GRASP_OFFSET_Z,
            )
            if success:
                self._transition_to(State.TRANSPORT)

        elif self.state == State.TRANSPORT:
            # Move to above place zone
            success = self._move_to_cartesian(
                x=PLACE_POSE.position.x,
                y=PLACE_POSE.position.y,
                z=PLACE_POSE.position.z,
            )
            if success:
                self._transition_to(State.PRE_PLACE)

        elif self.state == State.PRE_PLACE:
            # Lower to place height
            success = self._move_to_cartesian(
                x=PLACE_POSE.position.x,
                y=PLACE_POSE.position.y,
                z=self.target_block.position.z + 0.06,  # block on table
            )
            if success:
                self._transition_to(State.PLACE)

        elif self.state == State.PLACE:
            self._open_gripper()
            self.get_logger().info('Block placed! Returning home...')
            self._move_to_joints(HOME_JOINTS, duration_sec=3.0)
            self.target_block = None
            self._transition_to(State.IDLE)

    # ── Motion helpers ────────────────────────────────────────────────────

    def _move_to_cartesian(self, x: float, y: float, z: float) -> bool:
        """
        Plan and execute a Cartesian move to (x, y, z) using MoveIt2.
        End-effector orientation: pointing straight down (gripper faces floor).
        Returns True if execution succeeded.
        """
        target_pose = PoseStamped()
        target_pose.header.frame_id = 'world'
        target_pose.header.stamp    = self.get_clock().now().to_msg()
        target_pose.pose.position.x = x
        target_pose.pose.position.y = y
        target_pose.pose.position.z = z
        # Gripper pointing down: rotate 180° around X axis
        target_pose.pose.orientation.x = 1.0
        target_pose.pose.orientation.y = 0.0
        target_pose.pose.orientation.z = 0.0
        target_pose.pose.orientation.w = 0.0

        self.arm.set_start_state_to_current_state()
        self.arm.set_goal_state(
            pose_stamped_msg=target_pose,
            pose_link='fr3_hand_tcp'   # end-effector link
        )

        plan_result = self.arm.plan()
        if not plan_result:
            self.get_logger().error(f'Planning failed for ({x:.2f}, {y:.2f}, {z:.2f})')
            return False

        self.moveit.execute(plan_result.trajectory, controllers=[])
        return True

    def _move_to_joints(self, positions: list, duration_sec: float = 2.0):
        """Send a direct joint trajectory goal (bypasses MoveIt planning)."""
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = JOINT_NAMES

        point = JointTrajectoryPoint()
        point.positions       = positions
        point.time_from_start = Duration(sec=int(duration_sec))
        goal.trajectory.points = [point]

        self._arm_client.wait_for_server()
        self._arm_client.send_goal(goal)

    def _open_gripper(self):
        """Open the Franka Hand fully."""
        goal = GripperCommand.Goal()
        goal.command.position   = 0.08   # 8cm — max open
        goal.command.max_effort = 20.0
        self._gripper_client.wait_for_server()
        self._gripper_client.send_goal(goal)
        self.get_logger().info('Gripper OPENED')

    def _close_gripper(self):
        """Close gripper to grasp a 5cm block."""
        goal = GripperCommand.Goal()
        goal.command.position   = 0.05   # match block width
        goal.command.max_effort = 60.0
        self._gripper_client.wait_for_server()
        self._gripper_client.send_goal(goal)
        self.get_logger().info('Gripper CLOSED')

    def _transition_to(self, new_state: State):
        self.get_logger().info(f'State: {self.state.name} → {new_state.name}')
        self.state = new_state

    def _publish_status(self, status: str):
        self.status_pub.publish(String(data=status))


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
