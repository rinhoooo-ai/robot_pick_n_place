# pick_n_place_motion

ROS2 Python package điều khiển Franka FR3 thực hiện pick and place tự động — dùng MoveIt2 để plan trajectory và một state machine 8 bước để orchestrate toàn bộ quá trình.

---

## Package Structure

```
pick_n_place_motion/
├── package.xml
├── setup.py
├── config/
│   └── moveit_params.yaml          ← MoveIt2 params, place position, gripper config
├── launch/
│   └── motion.launch.py            ← launch pick_place_node
└── pick_n_place_motion/
    ├── __init__.py
    └── pick_place_node.py          ← state machine node chính
```

---

## State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   IDLE ──► DETECT ──► PRE_GRASP ──► GRASP ──► LIFT             │
│              │                                   │             │
│              │ no block                          ▼             │
│              └── wait 1s ◄──── PLACE ◄── PRE_PLACE ◄── TRANSPORT
│                                  │                             │
│                                  └────────── back to IDLE ─────┘
└─────────────────────────────────────────────────────────────────┘
```

| State | Action |
|---|---|
| `IDLE` | Reset, chờ lệnh |
| `DETECT` | Đọc `/block_poses`, chọn block đầu tiên |
| `PRE_GRASP` | Di chuyển đến điểm hover phía trên block, mở gripper |
| `GRASP` | Hạ xuống block, đóng gripper |
| `LIFT` | Nâng block lên cao |
| `TRANSPORT` | Di chuyển đến trên place zone |
| `PRE_PLACE` | Hạ xuống vị trí đặt |
| `PLACE` | Mở gripper, về home |

---

## Topics & Actions

| Interface | Type | Direction | Description |
|---|---|---|---|
| `/block_poses` | `geometry_msgs/PoseArray` | SUB | Vị trí block từ perception |
| `/pick_place_status` | `std_msgs/String` | PUB | Trạng thái hiện tại của state machine |
| `/fr3/arm_controller/follow_joint_trajectory` | Action | CLIENT | Điều khiển khớp tay |
| `/fr3/gripper_controller/gripper_action` | Action | CLIENT | Điều khiển gripper |

---

## Dependencies

| Package | Lý do |
|---|---|
| `moveit_ros_planning_interface` | Plan Cartesian trajectory |
| `control_msgs` | FollowJointTrajectory, GripperCommand actions |
| `trajectory_msgs` | JointTrajectory message |
| `tf2_ros` | Transform lookup world ↔ robot frame |

---

## Usage

```bash
# Chạy sau khi simulation + perception đã up
ros2 launch pick_n_place_motion motion.launch.py

# Monitor state machine
ros2 topic echo /pick_place_status

# Dừng khẩn cấp
ros2 topic pub /pick_place_status std_msgs/String "data: 'STOP'" --once
```

---

## Tuning

Chỉnh các thông số trong `config/moveit_params.yaml`:

```yaml
motion:
  pre_grasp_offset_z: 0.15   # tăng nếu robot đụng block khi tiếp cận
  max_velocity:       0.3    # giảm nếu chuyển động giật cục

place:
  x:  0.30                   # đổi vị trí drop zone
  y: -0.25

gripper:
  close_position: 0.05       # chỉnh theo kích thước block thực tế
```
