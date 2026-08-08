#!/usr/bin/env python3
"""Send a small, known-safe UR3e joint trajectory in the warehouse sim."""

import argparse
import time

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


JOINTS = [
    "ur3e_shoulder_pan_joint",
    "ur3e_shoulder_lift_joint",
    "ur3e_elbow_joint",
    "ur3e_wrist_1_joint",
    "ur3e_wrist_2_joint",
    "ur3e_wrist_3_joint",
]

POSES = {
    "home": [0.0, -1.5708, 1.5708, -1.5708, -1.5708, 1.5708],
    "inspect": [0.35, -1.35, 1.35, -1.35, -1.35, 0.25],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pose", choices=POSES)
    parser.add_argument("--duration", type=float, default=3.0)
    args, ros_args = parser.parse_known_args()

    rclpy.init(args=ros_args)
    node = Node("ur3e_pose_demo")
    publisher = node.create_publisher(JointTrajectory, "/arm_joint_trajectory", 10)

    deadline = time.monotonic() + 5.0
    while publisher.get_subscription_count() == 0 and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)

    message = JointTrajectory()
    message.joint_names = JOINTS
    point = JointTrajectoryPoint()
    point.positions = POSES[args.pose]
    nanoseconds = int(max(args.duration, 0.1) * 1_000_000_000)
    point.time_from_start.sec = nanoseconds // 1_000_000_000
    point.time_from_start.nanosec = nanoseconds % 1_000_000_000
    message.points = [point]
    publisher.publish(message)
    node.get_logger().info(
        f"Sent UR3e pose '{args.pose}' over {max(args.duration, 0.1):.1f} s"
    )
    rclpy.spin_once(node, timeout_sec=0.5)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
