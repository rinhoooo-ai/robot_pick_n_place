# pick_n_place_perception

ROS2 Python package xử lý camera feed để detect vị trí 3D của các block trên bàn — dùng RGB-D camera kết hợp OpenCV HSV color filtering.

---

## Package Structure

```
pick_n_place_perception/
├── package.xml
├── setup.py
├── config/
│   └── camera_params.yaml          ← HSV ranges + camera topic names (tune ở đây)
├── launch/
│   └── perception.launch.py        ← launch block_detector node
└── pick_n_place_perception/
    ├── __init__.py
    └── block_detector.py           ← node chính: camera → detect → publish poses
```

---

## How It Works

```
/camera/color/image_raw  ──┐
                            ├──► block_detector.py ──► /block_poses (PoseArray)
/camera/depth/image_raw  ──┘         │
/camera/color/camera_info ───────────┘         └──► /camera/debug_image (overlay)
```

### Detection Pipeline

```
RGB frame
   │
   ▼
Convert BGR → HSV
   │
   ▼
Apply HSV threshold per color (red / green / blue)
   │
   ▼
Morphological cleanup (remove noise, fill holes)
   │
   ▼
Find contours → filter by area (min 500 px²)
   │
   ▼
Compute centroid (u, v) in image space
   │
   ▼
Lookup depth at (u, v) → Z
   │
   ▼
Back-project: X = (u - cx) * Z / fx
              Y = (v - cy) * Z / fy
   │
   ▼
Publish geometry_msgs/PoseArray on /block_poses
```

---

## Topics

| Topic | Type | Direction | Description |
|---|---|---|---|
| `/camera/color/image_raw` | `sensor_msgs/Image` | SUB | RGB camera feed |
| `/camera/depth/image_raw` | `sensor_msgs/Image` | SUB | Depth image |
| `/camera/color/camera_info` | `sensor_msgs/CameraInfo` | SUB | Camera intrinsics (fx, fy, cx, cy) |
| `/block_poses` | `geometry_msgs/PoseArray` | PUB | 3D poses of detected blocks |
| `/camera/debug_image` | `sensor_msgs/Image` | PUB | RGB overlay with contours + labels |

---

## Dependencies

| Package | Lý do |
|---|---|
| `cv_bridge` | Convert ROS Image ↔ OpenCV Mat |
| `opencv-python` | HSV filtering, contour detection |
| `numpy` | Array operations |
| `sensor_msgs` | Image, CameraInfo |
| `geometry_msgs` | PoseArray output |

---

## Usage

```bash
# Launch detection node
ros2 launch pick_n_place_perception perception.launch.py

# View debug overlay in RViz hoặc:
ros2 run rqt_image_view rqt_image_view /camera/debug_image

# Monitor detected block poses
ros2 topic echo /block_poses
```

---

## Tuning HSV Ranges

Nếu block không được detect đúng, chỉnh `config/camera_params.yaml`:

```yaml
hsv_ranges:
  red:
    - lower: [0,   100, 100]
      upper: [10,  255, 255]
```

Cách nhanh nhất để tìm đúng range:
1. Chạy sim + perception node
2. Mở `/camera/debug_image` trong RViz
3. Chỉnh lower/upper cho đến khi contour bao đúng block
