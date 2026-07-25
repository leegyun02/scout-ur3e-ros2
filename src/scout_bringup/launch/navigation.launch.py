from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    can_interface = LaunchConfiguration("can_interface")
    lidar_ip = LaunchConfiguration("lidar_ip")
    map_yaml = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")
    start_robot = LaunchConfiguration("start_robot")
    use_rviz = LaunchConfiguration("use_rviz")

    bringup_share = FindPackageShare("scout_bringup")
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [bringup_share, "launch", "localization.launch.py"]
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "can_interface": can_interface,
            "lidar_ip": lidar_ip,
            "map": map_yaml,
            "params_file": params_file,
            "start_robot": start_robot,
            "use_rviz": "false",
        }.items(),
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("nav2_bringup_custom"),
                    "launch",
                    "navigation_launch.py",
                ]
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": params_file,
            "autostart": "true",
            "use_composition": "False",
            "use_respawn": "False",
        }.items(),
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=[
            "-d",
            PathJoinSubstitution(
                [FindPackageShare("scout_nav2"), "rviz", "nav2.rviz"]
            ),
        ],
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("can_interface", default_value="can0"),
            DeclareLaunchArgument("lidar_ip", default_value="192.168.1.201"),
            DeclareLaunchArgument(
                "map",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("scout_bringup"), "maps", "scout_map.yaml"]
                ),
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("scout_nav2"), "params", "scout_amcl.yaml"]
                ),
            ),
            DeclareLaunchArgument("start_robot", default_value="true"),
            DeclareLaunchArgument("use_rviz", default_value="true"),
            localization,
            nav2,
            rviz,
        ]
    )
