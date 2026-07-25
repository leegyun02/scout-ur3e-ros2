import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import yaml

class TrajectoryPlayer(Node):
    def __init__(self):
        super().__init__('trajectory_player')
        self.publisher_ = self.create_publisher(
            JointTrajectory,
            '/scaled_joint_trajectory_controller/joint_trajectory',
            10
        )

        with open('/home/inu/path.txt', 'r') as f:
            # yaml 파일 파싱
            content = f.read()
            msg = yaml.safe_load(content)

        # JointTrajectory 꺼내기
        jt = msg['trajectory'][0]['joint_trajectory']

        trajectory = JointTrajectory()
        trajectory.joint_names = jt['joint_names']
        trajectory.points = []

        for pt in jt['points']:
            point = JointTrajectoryPoint()
            point.positions = pt['positions']
            if 'time_from_start' in pt:
                point.time_from_start.sec = pt['time_from_start']['sec']
                point.time_from_start.nanosec = pt['time_from_start']['nanosec']
            trajectory.points.append(point)

        self.publisher_.publish(trajectory)
        self.get_logger().info('Trajectory published!')

def main():
    rclpy.init()
    node = TrajectoryPlayer()
    rclpy.spin_once(node, timeout_sec=1)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()