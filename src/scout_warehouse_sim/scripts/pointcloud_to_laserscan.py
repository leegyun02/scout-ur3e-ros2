#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan, PointCloud2
from sensor_msgs_py import point_cloud2


class PointCloudToLaserScan(Node):
    """Project a configurable horizontal slice of PointCloud2 into LaserScan."""

    def __init__(self):
        super().__init__("velodyne_to_scan")

        self.declare_parameter("min_height", -0.28)
        self.declare_parameter("max_height", 1.20)
        self.declare_parameter("angle_min", -math.pi)
        self.declare_parameter("angle_max", math.pi)
        self.declare_parameter("angle_increment", math.pi / 360.0)
        self.declare_parameter("scan_time", 0.1)
        self.declare_parameter("range_min", 0.40)
        self.declare_parameter("range_max", 50.0)

        self.publisher = self.create_publisher(
            LaserScan, "/scan", qos_profile_sensor_data
        )
        self.subscription = self.create_subscription(
            PointCloud2,
            "/points",
            self.cloud_callback,
            qos_profile_sensor_data,
        )

    def cloud_callback(self, cloud):
        min_height = self.get_parameter("min_height").value
        max_height = self.get_parameter("max_height").value
        angle_min = self.get_parameter("angle_min").value
        angle_max = self.get_parameter("angle_max").value
        angle_increment = self.get_parameter("angle_increment").value
        range_min = self.get_parameter("range_min").value
        range_max = self.get_parameter("range_max").value
        beam_count = int(math.ceil((angle_max - angle_min) / angle_increment))
        ranges = [math.inf] * beam_count

        for point in point_cloud2.read_points(
            cloud, field_names=("x", "y", "z"), skip_nans=True
        ):
            x = float(point[0])
            y = float(point[1])
            z = float(point[2])
            if z < min_height or z > max_height:
                continue

            distance = math.hypot(x, y)
            if distance < range_min or distance > range_max:
                continue

            angle = math.atan2(y, x)
            index = int((angle - angle_min) / angle_increment)
            if 0 <= index < beam_count and distance < ranges[index]:
                ranges[index] = distance

        scan = LaserScan()
        scan.header = cloud.header
        scan.angle_min = angle_min
        scan.angle_max = angle_min + (beam_count - 1) * angle_increment
        scan.angle_increment = angle_increment
        scan.time_increment = 0.0
        scan.scan_time = self.get_parameter("scan_time").value
        scan.range_min = range_min
        scan.range_max = range_max
        scan.ranges = ranges
        self.publisher.publish(scan)


def main(args=None):
    rclpy.init(args=args)
    node = PointCloudToLaserScan()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
