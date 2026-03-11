# pick_n_place_description

ROS2 package chứa toàn bộ mô tả robot (URDF/Xacro) cho hệ thống Pick and Place — bao gồm thân robot Franka FR3, gripper, và camera overhead.

---

## Package Structure

```
pick_n_place_description/
├── CMakeLists.txt
├── package.xml
├── launch/
│   └── display.launch.py          ← preview robot trong RViz2 (không cần Gazebo)
└── urdf/
    ├── fr3_with_gripper.urdf.xacro ← top-level assembly, include 3 file bên dưới
    ├── robots/
    │   └── fr3_base.urdf.xacro    ← thân Franka FR3 + world joint
    ├── end_effectors/
    │   └── franka_hand.xacro      ← Franka Hand gripper + TCP link
    └── sensors/
        └── rgbd_camera.xacro      ← Overhead RGB-D camera (RGB + Depth)
```

---

## URDF Architecture

`fr3_with_gripper.urdf.xacro` là file assembly — nó không định nghĩa gì mới mà chỉ gom 3 folder lại:

```
fr3_with_gripper.urdf.xacro
        │
        ├── robots/fr3_base.urdf.xacro
        │         Thân FR3 (7 khớp), joint world → fr3_link0
        │         Source: franka_description
        │
        ├── end_effectors/franka_hand.xacro
        │         Franka Hand gripper (2 ngón)
        │         TCP link tại đầu ngón tay (fr3_hand_tcp)
        │
        └── sensors/rgbd_camera.xacro
                  Camera mount + RGB sensor (30Hz) + Depth sensor (15Hz)
                  Gắn overhead tại xyz="0.5 0.0 1.5", nhìn thẳng xuống bàn
```

---

## Dependencies

| Package | Lý do |
|---|---|
| `franka_description` | URDF gốc của FR3 arm |
| `xacro` | Parse file `.urdf.xacro` |
| `robot_state_publisher` | Broadcast TF từ URDF |
| `joint_state_publisher_gui` | Kéo slider khớp khi preview |

---

## Usage

### Preview robot trong RViz2 (không cần Gazebo)

Dùng để verify URDF đúng chưa trước khi chạy simulation:

```bash
ros2 launch pick_n_place_description display.launch.py
```

Màn hình sẽ mở:
- **RViz2** — hiển thị robot model + TF tree
- **Joint State Publisher GUI** — slider kéo từng khớp để kiểm tra range of motion

### Dùng trong simulation

Package này không launch Gazebo trực tiếp. Để chạy full simulation:

```bash
ros2 launch pick_n_place_gazebo simulation.launch.py
```

---

## TF Tree

```
world
└── fr3_link0
    └── fr3_link1
        └── ... (fr3_link2 → fr3_link7)
            └── fr3_hand
                ├── fr3_hand_tcp        ← điểm điều khiển gripper
                ├── fr3_leftfinger
                └── fr3_rightfinger
world
└── camera_mount
    └── camera_link
        └── camera_color_optical_frame  ← frame publish image
```
