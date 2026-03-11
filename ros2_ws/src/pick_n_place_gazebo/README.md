# pick_n_place_gazebo

ROS2 package chứa Gazebo Harmonic simulation world, models, controllers và launch files cho hệ thống Pick and Place với Franka FR3.

---

## Package Structure

```
pick_n_place_gazebo/
├── CMakeLists.txt
├── package.xml
├── config/
│   └── ros2_controllers.yaml      ← arm + gripper controller config
├── launch/
│   ├── simulation.launch.py       ← 🚀 launch chính (Gazebo + robot + controllers + RViz)
│   └── spawn_blocks.launch.py     ← spawn blocks lên bàn sau khi sim đã chạy
├── models/
│   ├── block/                     ← 5cm colored cube (0.1kg, friction 0.8)
│   │   ├── model.config
│   │   └── model.sdf
│   └── table/                     ← bàn gỗ 1.2m x 0.8m x 0.8m
│       ├── model.config
│       └── model.sdf
├── rviz/
│   └── simulation.rviz            ← RViz2 config: robot, TF, camera feeds, block poses
├── scripts/
│   └── spawn_blocks.py            ← spawn N blocks thủ công qua CLI
└── worlds/
    └── pick_place_world.sdf       ← world: ground, table, pick/place zone markers, lighting
```

---

## World Layout

```
Top view (XY plane):

        Y
        │
  0.15  │   [  pick zone  ]        (green mat)
  0.10  │   [  block area ]  ←── blocks spawn here
        │
   0.0  │──────────[robot base]────────────── X
        │
 -0.25  │   [  place zone ]        (red mat)
        │
```

| Zone | Position (x, y) | Size |
|---|---|---|
| Pick zone (green) | 0.30, 0.10 | 30cm x 30cm |
| Place zone (red)  | 0.30, -0.25 | 30cm x 30cm |
| Robot base        | 0.0, 0.0 at z=0.8 | — |

---

## Usage

### 1. Launch simulation
```bash
ros2 launch pick_n_place_gazebo simulation.launch.py
```

Launches: Gazebo Harmonic → spawn FR3 → ros2_control → RViz2

### 2. Spawn blocks
```bash
# Via launch file (default 3 blocks)
ros2 launch pick_n_place_gazebo spawn_blocks.launch.py

# Via script (custom count)
ros2 run pick_n_place_gazebo spawn_blocks.py --n 5
```

### 3. Check controllers
```bash
ros2 control list_controllers
```

Expected output:
```
joint_state_broadcaster  [active]
arm_controller           [active]
gripper_controller       [active]
```

### 4. Manual arm test
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

## Controllers (`config/ros2_controllers.yaml`)

| Controller | Type | Topic/Action |
|---|---|---|
| `joint_state_broadcaster` | JointStateBroadcaster | `/joint_states` |
| `arm_controller` | JointTrajectoryController | `/fr3/arm_controller/follow_joint_trajectory` |
| `gripper_controller` | GripperActionController | `/fr3/gripper_controller/gripper_action` |
