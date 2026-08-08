#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import Point
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray


WORKCELLS = {
    "A": {"table": (-8.0, 5.0), "approach": (-6.85, 5.0, math.pi), "color": (0.90, 0.20, 0.20)},
    "B": {"table": (-8.0, -5.0), "approach": (-6.85, -5.0, math.pi), "color": (0.20, 0.45, 0.95)},
    "C": {"table": (8.0, 5.0), "approach": (6.85, 5.0, 0.0), "color": (0.20, 0.75, 0.30)},
    "D": {"table": (8.0, -5.0), "approach": (6.85, -5.0, 0.0), "color": (0.95, 0.65, 0.10)},
}


class WorkcellMarkers(Node):
    def __init__(self):
        super().__init__("workcell_markers")
        self.publisher = self.create_publisher(MarkerArray, "/workcell_markers", 1)
        self.timer = self.create_timer(1.0, self.publish_markers)

    def publish_markers(self):
        now = self.get_clock().now().to_msg()
        markers = MarkerArray()

        for index, (name, data) in enumerate(WORKCELLS.items()):
            red, green, blue = data["color"]
            table_x, table_y = data["table"]
            approach_x, approach_y, yaw = data["approach"]

            label = Marker()
            label.header.frame_id = "map"
            label.header.stamp = now
            label.ns = "workcell_labels"
            label.id = index
            label.type = Marker.TEXT_VIEW_FACING
            label.action = Marker.ADD
            label.pose.position.x = table_x
            label.pose.position.y = table_y
            label.pose.position.z = 1.40
            label.pose.orientation.w = 1.0
            label.scale.z = 0.55
            label.color.r = red
            label.color.g = green
            label.color.b = blue
            label.color.a = 1.0
            label.text = f"ZONE {name}"
            markers.markers.append(label)

            arrow = Marker()
            arrow.header.frame_id = "map"
            arrow.header.stamp = now
            arrow.ns = "workcell_approaches"
            arrow.id = index
            arrow.type = Marker.ARROW
            arrow.action = Marker.ADD
            arrow.pose.position.x = approach_x
            arrow.pose.position.y = approach_y
            arrow.pose.position.z = 0.08
            arrow.pose.orientation.z = math.sin(yaw / 2.0)
            arrow.pose.orientation.w = math.cos(yaw / 2.0)
            arrow.scale.x = 0.75
            arrow.scale.y = 0.12
            arrow.scale.z = 0.12
            arrow.color.r = red
            arrow.color.g = green
            arrow.color.b = blue
            arrow.color.a = 1.0
            markers.markers.append(arrow)

            line = Marker()
            line.header.frame_id = "map"
            line.header.stamp = now
            line.ns = "workcell_reach_lines"
            line.id = index
            line.type = Marker.LINE_STRIP
            line.action = Marker.ADD
            line.scale.x = 0.035
            line.color.r = red
            line.color.g = green
            line.color.b = blue
            line.color.a = 0.8
            line.points = [
                Point(x=approach_x, y=approach_y, z=0.05),
                Point(x=table_x, y=table_y, z=0.57),
            ]
            markers.markers.append(line)

        self.publisher.publish(markers)


def main(args=None):
    rclpy.init(args=args)
    node = WorkcellMarkers()
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
