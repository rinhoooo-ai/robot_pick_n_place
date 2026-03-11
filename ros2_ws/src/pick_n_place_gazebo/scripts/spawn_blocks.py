#!/usr/bin/env python3
"""
scripts/spawn_blocks.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Spawn colored blocks onto the pick zone via Gazebo's /world service.
Run this AFTER simulation.launch.py is up.

Usage:
  ros2 run pick_n_place_gazebo spawn_blocks.py
  ros2 run pick_n_place_gazebo spawn_blocks.py --n 5
"""

import argparse
import subprocess
import os
from ament_python import get_package_share_directory


def spawn_block(name: str, x: float, y: float, z: float, sdf_path: str):
    cmd = [
        'ros2', 'run', 'ros_gz_sim', 'create',
        '-name', name,
        '-file', sdf_path,
        '-x', str(x),
        '-y', str(y),
        '-z', str(z),
    ]
    print(f'[spawn] {name} at ({x:.2f}, {y:.2f}, {z:.2f})')
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description='Spawn blocks on the pick zone')
    parser.add_argument('--n', type=int, default=3,
                        help='Number of blocks to spawn (default: 3)')
    args = parser.parse_args()

    pkg = get_package_share_directory('pick_n_place_gazebo')
    sdf_path = os.path.join(pkg, 'models', 'block', 'model.sdf')

    # Pick zone positions — table top at z=0.80, block half-height=0.025
    positions = [
        ('block_1', 0.25, 0.10, 0.825),
        ('block_2', 0.30, 0.10, 0.825),
        ('block_3', 0.35, 0.10, 0.825),
        ('block_4', 0.25, 0.15, 0.825),
        ('block_5', 0.30, 0.15, 0.825),
    ]

    for i in range(min(args.n, len(positions))):
        name, x, y, z = positions[i]
        spawn_block(name, x, y, z, sdf_path)

    print(f'\n✅ Spawned {min(args.n, len(positions))} block(s)')


if __name__ == '__main__':
    main()
