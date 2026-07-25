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
    start_robot = LaunchConfiguration("start_robot")

    bringup_share = FindPackageShare("scout_bringup")
    slam_params = PathJoinSubstitution(
        [bringup_share, "config", "slam_toolbox.yaml"]
    )

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

    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("slam_toolbox"), "launch", "online_sync_launch.py"]
            )
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "slam_params_file": slam_params,
        }.items(),
    )

    map_saver = Node(
        package="nav2_map_server",
        executable="map_saver_server",
        name="map_saver",
        output="screen",
        parameters=[slam_params, {"use_sim_time": use_sim_time}],
    )
    map_saver_lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_slam",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time},
            {"autostart": True},
            {"node_names": ["map_saver"]},
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
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("can_interface", default_value="can0"),
            DeclareLaunchArgument("lidar_ip", default_value="192.168.1.201"),
            DeclareLaunchArgument("start_robot", default_value="true"),
            robot_bringup,
            slam_toolbox,
            map_saver,
            map_saver_lifecycle,
            rviz,
        ]
    )
