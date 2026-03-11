#!/usr/bin/env python3
"""
block_detector.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Detects colored blocks using RGB + Depth camera feeds.

Pipeline:
  1. Subscribe /camera/color/image_raw  → RGB frame
  2. Subscribe /camera/depth/image_raw  → Depth frame
  3. Convert RGB → HSV color space
  4. Apply HSV thresholds per color (red, green, blue)
  5. Find contours → compute centroid (u, v) in image
  6. Use depth value at (u, v) → compute 3D position (x, y, z)
  7. Publish geometry_msgs/PoseArray on /block_poses

Topic I/O:
  SUB: /camera/color/image_raw   sensor_msgs/Image
  SUB: /camera/depth/image_raw   sensor_msgs/Image
  SUB: /camera/color/camera_info sensor_msgs/CameraInfo
  PUB: /block_poses              geometry_msgs/PoseArray
  PUB: /camera/debug_image       sensor_msgs/Image  (visualization)
"""

import rclpy
from rclpy.node import Node

import cv2
import numpy as np
from cv_bridge import CvBridge

from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseArray, Pose, Point, Quaternion
from std_msgs.msg import Header


# ── HSV color ranges ────────────────────────────────────────────────────
# Tune these ranges by running: python3 -c "import cv2; ..."
# or use the debug image topic to visualize masks
COLOR_RANGES = {
    'red': [
        (np.array([0,   100, 100]), np.array([10,  255, 255])),   # lower red
        (np.array([160, 100, 100]), np.array([180, 255, 255])),   # upper red (wraps)
    ],
    'green': [
        (np.array([40,  80, 80]),  np.array([80,  255, 255])),
    ],
    'blue': [
        (np.array([100, 80, 80]),  np.array([140, 255, 255])),
    ],
}

# Minimum contour area in pixels² — filters out noise
MIN_CONTOUR_AREA = 500


class BlockDetector(Node):
    """
    Detects colored blocks via HSV thresholding and publishes
    their 3D world poses using the depth camera.
    """

    def __init__(self):
        super().__init__('block_detector')

        self.bridge       = CvBridge()
        self.depth_image  = None
        self.camera_info  = None

        # ── Subscribers ────────────────────────────────────────
        self.create_subscription(
            Image, '/camera/color/image_raw',
            self.rgb_callback, 10
        )
        self.create_subscription(
            Image, '/camera/depth/image_raw',
            self.depth_callback, 10
        )
        self.create_subscription(
            CameraInfo, '/camera/color/camera_info',
            self.camera_info_callback, 10
        )

        # ── Publishers ─────────────────────────────────────────
        self.pose_pub  = self.create_publisher(PoseArray, '/block_poses', 10)
        self.debug_pub = self.create_publisher(Image, '/camera/debug_image', 10)

        self.get_logger().info('BlockDetector node started ✓')

    # ── Callbacks ──────────────────────────────────────────────────────

    def depth_callback(self, msg: Image):
        """Cache latest depth frame."""
        self.depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')

    def camera_info_callback(self, msg: CameraInfo):
        """Cache camera intrinsics (fx, fy, cx, cy)."""
        self.camera_info = msg

    def rgb_callback(self, msg: Image):
        """Main processing callback — runs on every RGB frame."""
        if self.depth_image is None or self.camera_info is None:
            return  # wait for depth + camera info to arrive

        # Convert ROS Image → OpenCV BGR → HSV
        bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        pose_array = PoseArray()
        pose_array.header = Header(
            stamp=self.get_clock().now().to_msg(),
            frame_id='world'
        )
        debug_img = bgr.copy()

        # ── Detect each color ───────────────────────────────────
        for color_name, ranges in COLOR_RANGES.items():
            # Build binary mask — union of all HSV ranges for this color
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for (lo, hi) in ranges:
                mask |= cv2.inRange(hsv, lo, hi)

            # Morphological cleanup: remove tiny noise, fill small holes
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
            mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # Find contours
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < MIN_CONTOUR_AREA:
                    continue

                # Centroid in image space
                M   = cv2.moments(cnt)
                if M['m00'] == 0:
                    continue
                u = int(M['m10'] / M['m00'])
                v = int(M['m01'] / M['m00'])

                # 3D position from depth
                pose = self._pixel_to_world(u, v)
                if pose is None:
                    continue

                pose_array.poses.append(pose)

                # Draw on debug image
                color_bgr = {'red': (0,0,255), 'green': (0,255,0), 'blue': (255,0,0)}
                cv2.drawContours(debug_img, [cnt], -1, color_bgr[color_name], 2)
                cv2.circle(debug_img, (u, v), 6, color_bgr[color_name], -1)
                label = f"{color_name} ({pose.position.x:.2f},{pose.position.y:.2f})"
                cv2.putText(debug_img, label, (u+8, v),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                            color_bgr[color_name], 1, cv2.LINE_AA)

        # Publish
        self.pose_pub.publish(pose_array)
        self.debug_pub.publish(
            self.bridge.cv2_to_imgmsg(debug_img, encoding='bgr8')
        )

        if pose_array.poses:
            self.get_logger().info(
                f'Detected {len(pose_array.poses)} block(s)', throttle_duration_sec=2.0
            )

    # ── Helpers ────────────────────────────────────────────────────────

    def _pixel_to_world(self, u: int, v: int):
        """
        Back-project pixel (u, v) + depth → 3D world point.
        Uses pinhole camera model: X = (u - cx) * Z / fx
        Returns geometry_msgs/Pose or None if depth is invalid.
        """
        ci = self.camera_info
        fx, fy = ci.k[0], ci.k[4]
        cx, cy = ci.k[2], ci.k[5]

        # Guard bounds
        h, w = self.depth_image.shape[:2]
        if not (0 <= v < h and 0 <= u < w):
            return None

        Z = float(self.depth_image[v, u])
        if Z <= 0.01 or np.isnan(Z) or np.isinf(Z):
            return None   # invalid depth reading

        # Camera frame → world frame
        # Note: camera is mounted overhead looking down → axes differ
        X = (u - cx) * Z / fx
        Y = (v - cy) * Z / fy

        pose = Pose()
        pose.position    = Point(x=X, y=Y, z=Z)
        pose.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
        return pose


def main(args=None):
    rclpy.init(args=args)
    node = BlockDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
