# 🦾 Robot Pick and Place

> Franka FR3 robotic arm simulation in Gazebo that **detects**, **picks**, and **places** colored blocks autonomously using a RGB-D camera and MoveIt2.

**Stack:** ROS2 Jazzy · Gazebo Harmonic · MoveIt2 · OpenCV · Python

---

## What it does

```
Camera sees block  →  Compute 3D position  →  Plan path  →  Pick  →  Place
```

The arm reads an overhead RGB-D camera feed, detects colored blocks via HSV filtering, plans a collision-free trajectory with MoveIt2, grasps the block, and drops it in the target zone — then loops.

---

## Demo

> *(add a GIF here once you run the sim)*

---

## Repo Structure

```
robot_pick_n_place/
│
├── 📄 README.md
├── 🔧 scripts/
│   └── setup.sh                        ← install deps + build in one command
│
├── 📚 docs/
│   └── images/                         ← screenshots, diagrams
│
└── 🤖 ros2_ws/
    └── src/
        │
        ├── pick_n_place_description/   ← Robot model (URDF/Xacro + camera)
        │   ├── urdf/
        │   │   └── fr3_with_gripper.urdf.xacro
        │   ├── meshes/                 ← 3D mesh files
        │   ├── rviz/                   ← RViz2 config
        │   └── launch/
        │       └── display.launch.py   ← preview robot in RViz
        │
        ├── pick_n_place_gazebo/        ← Simulation world + controllers
        │   ├── worlds/
        │   │   └── pick_place_world.sdf  ← floor, table, pick/place zones
        │   ├── models/
        │   │   └── block/              ← colored block SDF
        │   ├── config/
        │   │   └── ros2_controllers.yaml
        │   └── launch/
        │       ├── simulation.launch.py  ← 🚀 start here
        │       └── spawn_blocks.launch.py
        │
        ├── pick_n_place_perception/    ← Camera → detect block → 3D pose
        │   ├── pick_n_place_perception/
        │   │   └── block_detector.py   ← OpenCV HSV detection node
        │   ├── config/
        │   │   └── camera_params.yaml
        │   └── launch/
        │       └── perception.launch.py
        │
        └── pick_n_place_motion/        ← MoveIt2 pick & place logic
            ├── pick_n_place_motion/
            │   └── pick_place_node.py  ← 8-state state machine
            ├── config/
            │   └── moveit_params.yaml
            └── launch/
                └── motion.launch.py
```

---

## Prerequisites

```bash
# ROS2 Jazzy
sudo apt install ros-jazzy-desktop

# Gazebo Harmonic + bridge
sudo apt install ros-jazzy-ros-gz

# MoveIt2
sudo apt install ros-jazzy-moveit

# Controllers
sudo apt install ros-jazzy-ros2-control ros-jazzy-ros2-controllers

# Python
pip install opencv-python numpy
```

---

## Installation

```bash
git clone https://github.com/<your-username>/robot_pick_n_place.git
cd robot_pick_n_place

bash scripts/setup.sh
source ros2_ws/install/setup.bash
```

---

## Usage

Open 4 terminals, run in order:

```bash
# 1️⃣  Launch Gazebo world + FR3 robot + controllers
ros2 launch pick_n_place_gazebo simulation.launch.py

# 2️⃣  Spawn colored blocks on the table
ros2 launch pick_n_place_gazebo spawn_blocks.launch.py

# 3️⃣  Start camera block detection
ros2 run pick_n_place_perception block_detector

# 4️⃣  Start pick and place!
ros2 run pick_n_place_motion pick_place_node
```

---

## How It Works

### State Machine
```
IDLE → DETECT → PRE_GRASP → GRASP → LIFT → TRANSPORT → PRE_PLACE → PLACE → IDLE
                    │                                                      │
                    └─────────── no block found: wait 1s ─────────────────┘
```

### Topic Graph
| Topic | Type | Direction |
|---|---|---|
| `/camera/color/image_raw` | `sensor_msgs/Image` | Gazebo → Perception |
| `/camera/depth/image_raw` | `sensor_msgs/Image` | Gazebo → Perception |
| `/block_poses` | `geometry_msgs/PoseArray` | Perception → Motion |
| `/fr3/arm_controller/follow_joint_trajectory` | Action | Motion → Robot |
| `/pick_place_status` | `std_msgs/String` | Motion → Monitor |

---

## Manual Joint Control (testing)

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
