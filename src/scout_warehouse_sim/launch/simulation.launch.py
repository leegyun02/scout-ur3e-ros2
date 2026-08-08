import os
from math import pi

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_share = get_package_share_directory("scout_warehouse_sim")

    world = LaunchConfiguration("world")
    gui = LaunchConfiguration("gui")
    rviz = LaunchConfiguration("rviz")

    world_default = os.path.join(
        package_share, "worlds", "scout_pick_place_warehouse.sdf"
    )
    model_path = os.path.join(package_share, "models")
    # sdformat converts package:// mesh URIs to model:// URIs.  Adding the
    # parent of the vendor package shares lets Fortress resolve those meshes.
    ros_package_model_path = os.path.dirname(
        get_package_share_directory("ur_description")
    )
    robot_file = os.path.join(
        package_share, "urdf", "scout_ur3e_velodyne.urdf.xacro"
    )
    bridge_file = os.path.join(package_share, "config", "ros_gz_bridge.yaml")
    rviz_file = os.path.join(package_share, "rviz", "warehouse_nav2.rviz")

    robot_description = {
        "robot_description": ParameterValue(
            Command([FindExecutable(name="xacro"), " ", robot_file]),
            value_type=str,
        )
    }

    gazebo_gui = ExecuteProcess(
        cmd=["ign", "gazebo", "-r", "--verbose", "2", world],
        output="screen",
        condition=IfCondition(gui),
    )
    gazebo_headless = ExecuteProcess(
        cmd=["ign", "gazebo", "-r", "-s", "--verbose", "2", world],
        output="screen",
        condition=UnlessCondition(gui),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"use_sim_time": True}, robot_description],
        output="screen",
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "scout_ur3e",
            "-topic", "robot_description",
            "-x", LaunchConfiguration("x"),
            "-y", LaunchConfiguration("y"),
            "-z", LaunchConfiguration("z"),
            "-Y", LaunchConfiguration("yaw"),
        ],
        output="screen",
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="scout_gz_bridge",
        parameters=[{
            "config_file": bridge_file,
            "qos_overrides./tf_static.publisher.durability": "transient_local",
        }],
        output="screen",
    )

    pointcloud_to_scan = Node(
        package="scout_warehouse_sim",
        executable="pointcloud_to_laserscan.py",
        name="velodyne_to_scan",
        parameters=[{
            # Height is expressed in velodyne_link.  This removes the floor
            # while retaining table legs, workpieces, walls and racks.
            "min_height": -0.28,
            "max_height": 1.20,
            "angle_min": -pi,
            "angle_max": pi,
            "angle_increment": pi / 360.0,
            "scan_time": 0.1,
            "range_min": 0.40,
            "range_max": 50.0,
        }],
        output="screen",
    )

    workcell_markers = Node(
        package="scout_warehouse_sim",
        executable="workcell_markers.py",
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_file],
        parameters=[{"use_sim_time": True}],
        condition=IfCondition(rviz),
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument("world", default_value=world_default),
        DeclareLaunchArgument("gui", default_value="true", choices=["true", "false"]),
        DeclareLaunchArgument("rviz", default_value="true", choices=["true", "false"]),
        DeclareLaunchArgument("x", default_value="0.0"),
        DeclareLaunchArgument("y", default_value="0.0"),
        DeclareLaunchArgument("z", default_value="0.2346"),
        DeclareLaunchArgument("yaw", default_value="0.0"),
        AppendEnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", model_path),
        AppendEnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", ros_package_model_path),
        gazebo_gui,
        gazebo_headless,
        robot_state_publisher,
        bridge,
        TimerAction(period=2.0, actions=[spawn_robot]),
        TimerAction(period=3.0, actions=[pointcloud_to_scan, workcell_markers, rviz_node]),
    ])
