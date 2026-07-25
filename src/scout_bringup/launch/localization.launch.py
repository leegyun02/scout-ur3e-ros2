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
    robot_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [bringup_share, "launch", "robot_bringup.launch.py"]
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "can_interface": can_interface,
            "lidar_ip": lidar_ip,
        }.items(),
        condition=IfCondition(start_robot),
    )

    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[
            params_file,
            {
                "yaml_filename": map_yaml,
                "use_sim_time": use_sim_time,
            },
        ],
    )
    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=[params_file, {"use_sim_time": use_sim_time}],
    )
    localization_lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time},
            {"autostart": True},
            {"node_names": ["map_server", "amcl"]},
        ],
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
                description="Absolute path to the map YAML file",
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("scout_nav2"), "params", "scout_amcl.yaml"]
                ),
            ),
            DeclareLaunchArgument("start_robot", default_value="true"),
            DeclareLaunchArgument("use_rviz", default_value="true"),
            robot_bringup,
            map_server,
            amcl,
            localization_lifecycle,
            rviz,
        ]
    )
