from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mode = LaunchConfiguration("mode")
    use_sim_time = LaunchConfiguration("use_sim_time")
    can_interface = LaunchConfiguration("can_interface")
    lidar_ip = LaunchConfiguration("lidar_ip")
    map_yaml = LaunchConfiguration("map")
    use_rviz = LaunchConfiguration("use_rviz")
    bringup_share = FindPackageShare("scout_bringup")

    mapping = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, "launch", "slam.launch.py"])
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "can_interface": can_interface,
            "lidar_ip": lidar_ip,
            "use_rviz": use_rviz,
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
            "use_rviz": use_rviz,
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
                default_value=PathJoinSubstitution(
                    [FindPackageShare("scout_bringup"), "maps", "scout_map.yaml"]
                ),
            ),
            DeclareLaunchArgument("use_rviz", default_value="true"),
            mapping,
            navigation,
        ]
    )
