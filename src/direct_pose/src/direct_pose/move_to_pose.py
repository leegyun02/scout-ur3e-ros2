#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from moveit2 import MoveIt2

class PoseMover(Node):
    def __init__(self):
        super().__init__('pose_mover')

        self.moveit2 = MoveIt2(
            node=self,
            joint_names=[
                'shoulder_pan_joint',
                'shoulder_lift_joint',
                'elbow_joint',
                'wrist_1_joint',
                'wrist_2_joint',
                'wrist_3_joint',
            ],
            base_link_name='base_link',
            end_effector_name='tool0',
            group_name='ur_manipulator'
        )

    def move(self):
        pose = PoseStamped()
        pose.header.frame_id = 'base_link'
        pose.pose.position.x = 0.35
        pose.pose.position.y = 0.0
        pose.pose.position.z = 0.25
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = 0.0
        pose.pose.orientation.w = 1.0

        self.moveit2.move_to_pose(pose.pose)
        self.moveit2.wait_until_executed()

def main():
    rclpy.init()
    node = PoseMover()
    node.move()
    rclpy.shutdown()

def main():
    print("🦾 Moving robot to target pose...")

if __name__ == '__main__':
    main()