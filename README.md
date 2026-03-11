# 🦾 Robot Pick and Place

> Autonomous **Franka FR3** robotic arm simulation — detects colored blocks with an overhead RGB-D camera, plans collision-free trajectories with MoveIt2, and picks and places them into a target zone.

**Stack:** ROS2 Jazzy &nbsp;·&nbsp; Gazebo Harmonic &nbsp;·&nbsp; MoveIt2 &nbsp;·&nbsp; OpenCV &nbsp;·&nbsp; Python 3

---

## Demo

> *(add a GIF here once you run the sim)*

---

## How It Works

```
Overhead camera
      │
      ▼
 block_detector.py          pick_place_node.py
 HSV color filter    ──►    8-state machine     ──►   MoveIt2   ──►   FR3 arm
 depth back-project         /block_poses                               + gripper
      │                          │
      ▼                          ▼
 /block_poses            DETECT → PRE_GRASP → GRASP → LIFT
                         TRANSPORT → PRE_PLACE → PLACE → IDLE
```

---

## Repo Structure

```
robot_pick_n_place/
│
├── scripts/
│   └── setup.sh                             ← install all deps + build
│
└── ros2_ws/
    └── src/
        │
        ├── pick_n_place_description/        ← 🤖 Robot model (URDF/Xacro)
        │   ├── launch/
        │   │   └── display.launch.py        ← preview robot in RViz2 (no Gazebo)
        │   └── urdf/
        │       ├── fr3_with_gripper.urdf.xacro   ← top-level assembly
        │       ├── robots/
        │       │   └── fr3_base.urdf.xacro        ← FR3 arm + world joint
        │       ├── end_effectors/
        │       │   └── franka_hand.xacro          ← Franka Hand gripper + TCP
        │       └── sensors/
        │           └── rgbd_camera.xacro          ← overhead RGB-D camera
        │
        ├── pick_n_place_gazebo/             ← 🌍 Simulation world
        │   ├── config/
        │   │   └── ros2_controllers.yaml    ← arm + gripper controller config
        │   ├── launch/
        │   │   ├── simulation.launch.py     ← 🚀 main launch (Gazebo + robot + RViz)
        │   │   └── spawn_blocks.launch.py   ← spawn colored blocks onto table
        │   ├── models/
        │   │   ├── block/                   ← 5cm colored cube (0.1kg)
        │   │   └── table/                   ← wooden table 1.2m × 0.8m × 0.8m
        │   ├── rviz/
        │   │   └── simulation.rviz          ← RViz2 layout: robot + camera + poses
        │   ├── scripts/
        │   │   └── spawn_blocks.py          ← spawn N blocks via CLI
        │   └── worlds/
        │       └── pick_place_world.sdf     ← ground, table, pick/place zone markers
        │
        ├── pick_n_place_perception/         ← 👁️ Camera → detect block → 3D pose
        │   ├── config/
        │   │   └── camera_params.yaml       ← HSV ranges (tune here)
        │   ├── launch/
        │   │   └── perception.launch.py
        │   └── pick_n_place_perception/
        │       └── block_detector.py        ← OpenCV HSV + depth back-projection
        │
        └── pick_n_place_motion/             ← 🦾 MoveIt2 pick & place logic
            ├── config/
            │   └── moveit_params.yaml       ← place position, velocity, gripper config
            ├── launch/
            │   └── motion.launch.py
            └── pick_n_place_motion/
                └── pick_place_node.py       ← 8-state machine node
```

---

## Prerequisites

Ubuntu 24.04 + ROS2 Jazzy. Run `setup.sh` to install everything automatically, or install manually:

```bash
# ROS2 Jazzy
sudo apt install ros-jazzy-desktop

# Gazebo Harmonic
sudo apt install ros-jazzy-ros-gz ros-jazzy-ros-gz-bridge

# MoveIt2
sudo apt install ros-jazzy-moveit

# ros2_control
sudo apt install ros-jazzy-ros2-control ros-jazzy-ros2-controllers

# Franka
sudo apt install ros-jazzy-franka-description ros-jazzy-franka-msgs

# Python
pip install opencv-python numpy
```

---

## Installation

```bash
# 1. Clone
git clone https://github.com/rinhoooo-ai/robot_pick_n_place.git
cd robot_pick_n_place

# 2. Install deps + build (automated)
bash scripts/setup.sh

# 3. Activate workspace
source ros2_ws/install/setup.bash
```

---

## Running Locally

Open **4 terminals**, run in order:

### Terminal 1 — Launch Gazebo + FR3 + controllers + RViz2
```bash
source ros2_ws/install/setup.bash
ros2 launch pick_n_place_gazebo simulation.launch.py
```
Wait until you see `[INFO] arm_controller: active` before continuing.

### Terminal 2 — Spawn blocks onto the table
```bash
source ros2_ws/install/setup.bash
ros2 launch pick_n_place_gazebo spawn_blocks.launch.py

# or spawn a custom number of blocks
ros2 run pick_n_place_gazebo spawn_blocks.py --n 5
```

### Terminal 3 — Start block detection
```bash
source ros2_ws/install/setup.bash
ros2 launch pick_n_place_perception perception.launch.py
```
Check detection is working:
```bash
ros2 topic echo /block_poses
```

### Terminal 4 — Start pick and place
```bash
source ros2_ws/install/setup.bash
ros2 launch pick_n_place_motion motion.launch.py
```
Monitor state machine:
```bash
ros2 topic echo /pick_place_status
```

---

## Topic Graph

| Topic | Type | Flow |
|---|---|---|
| `/camera/color/image_raw` | `sensor_msgs/Image` | Gazebo → Perception |
| `/camera/depth/image_raw` | `sensor_msgs/Image` | Gazebo → Perception |
| `/block_poses` | `geometry_msgs/PoseArray` | Perception → Motion |
| `/fr3/arm_controller/follow_joint_trajectory` | Action | Motion → Robot |
| `/fr3/gripper_controller/gripper_action` | Action | Motion → Robot |
| `/pick_place_status` | `std_msgs/String` | Motion → Monitor |

---

## Manual Joint Control

For testing arm movement without running the full pipeline:

```bash
ros2 action send_goal /fr3/arm_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory "{
    trajectory: {
      joint_names: ['fr3_joint1','fr3_joint2','fr3_joint3','fr3_joint4','fr3_joint5','fr3_joint6','fr3_joint7'],
      points: [{
        positions: [0.3, -0.3, 0.0, -1.2, 0.0, 1.0, 0.3],
        time_from_start: {sec: 2, nanosec: 0}
      }]
    }
  }" --feedback
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Blocks not detected | Tune HSV ranges in `pick_n_place_perception/config/camera_params.yaml` |
| MoveIt2 planning fails | Increase `planning_time` in `pick_n_place_motion/config/moveit_params.yaml` |
| Controllers not active | Wait longer after launching sim, or run `ros2 control list_controllers` |
| Robot jerky | Reduce `max_velocity` in `moveit_params.yaml` |
