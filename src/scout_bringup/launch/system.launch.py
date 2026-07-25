from pathlib import Path

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.substitutions import FindPackageShare


def validate_navigation_map(context):
    if LaunchConfiguration("mode").perform(context) != "navigation":
        return []

    map_value = LaunchConfiguration("map").perform(context).strip()
    if not map_value:
        raise RuntimeError(
            "Navigation requires an explicit map path. "
            "Use map:=/absolute/path/to/map.yaml"
        )

    map_path = Path(map_value)
    if not map_path.is_absolute():
        raise RuntimeError(f"Map path must be absolute: {map_value}")
    if map_path.suffix.lower() != ".yaml":
        raise RuntimeError(f"Map path must point to a .yaml file: {map_value}")
    if not map_path.is_file():
        raise RuntimeError(f"Map YAML file does not exist: {map_value}")

    return []


def generate_launch_description():
    mode = LaunchConfiguration("mode")
    use_sim_time = LaunchConfiguration("use_sim_time")
    can_interface = LaunchConfiguration("can_interface")
    lidar_ip = LaunchConfiguration("lidar_ip")
    map_yaml = LaunchConfiguration("map")
    bringup_share = FindPackageShare("scout_bringup")

    mapping = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, "launch", "slam.launch.py"])
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "can_interface": can_interface,
            "lidar_ip": lidar_ip,
        }.items(),
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'mapping'"])
        ),
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, "launch", "navigation.launch.py"])
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "can_interface": can_interface,
            "lidar_ip": lidar_ip,
            "map": map_yaml,
        }.items(),
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'navigation'"])
        ),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "mode",
                default_value="mapping",
                choices=["mapping", "navigation"],
            ),
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("can_interface", default_value="can0"),
            DeclareLaunchArgument("lidar_ip", default_value="192.168.1.201"),
            DeclareLaunchArgument(
                "map",
                default_value="",
                description=(
                    "Absolute map YAML path; required when mode:=navigation"
                ),
            ),
            OpaqueFunction(function=validate_navigation_map),
            mapping,
            navigation,
        ]
    )
