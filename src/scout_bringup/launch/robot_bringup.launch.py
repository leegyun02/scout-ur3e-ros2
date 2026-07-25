from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    can_interface = LaunchConfiguration("can_interface")
    lidar_ip = LaunchConfiguration("lidar_ip")
    start_base = LaunchConfiguration("start_base")
    start_lidar = LaunchConfiguration("start_lidar")

    description_file = PathJoinSubstitution(
        [FindPackageShare("scout_ur3e_description"), "urdf", "scout_ur3e.xacro"]
    )
    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", description_file]),
        value_type=str,
    )

    base_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("scout_base"), "launch", "scout_base.launch.py"]
            )
        ),
        launch_arguments={
            "port_name": can_interface,
            "odom_frame": "odom",
            "base_frame": "base_link",
            "odom_topic_name": "/odometry",
            "use_sim_time": use_sim_time,
            "auto_reconnect": "true",
        }.items(),
        condition=IfCondition(start_base),
    )

    state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "robot_description": robot_description,
            }
        ],
    )

    bringup_share = FindPackageShare("scout_bringup")
    driver_params = PathJoinSubstitution(
        [bringup_share, "config", "velodyne_driver.yaml"]
    )
    transform_params = PathJoinSubstitution(
        [bringup_share, "config", "velodyne_transform.yaml"]
    )
    laserscan_params = PathJoinSubstitution(
        [bringup_share, "config", "pointcloud_to_laserscan.yaml"]
    )
    calibration_file = PathJoinSubstitution(
        [FindPackageShare("velodyne_pointcloud"), "params", "VLP16db.yaml"]
    )

    velodyne_driver = Node(
        package="velodyne_driver",
        executable="velodyne_driver_node",
        name="velodyne_driver_node",
        output="screen",
        parameters=[
            driver_params,
            {
                "device_ip": ParameterValue(lidar_ip, value_type=str),
                "frame_id": "velodyne_link",
            },
        ],
        condition=IfCondition(start_lidar),
    )

    velodyne_transform = Node(
        package="velodyne_pointcloud",
        executable="velodyne_transform_node",
        name="velodyne_transform_node",
        output="screen",
        parameters=[
            transform_params,
            {"calibration": ParameterValue(calibration_file, value_type=str)},
        ],
        condition=IfCondition(start_lidar),
    )

    pointcloud_to_laserscan = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        name="pointcloud_to_laserscan",
        output="screen",
        parameters=[laserscan_params, {"use_sim_time": use_sim_time}],
        remappings=[
            ("cloud_in", "/velodyne_points"),
            ("scan", "/scan"),
        ],
        condition=IfCondition(start_lidar),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("can_interface", default_value="can0"),
            DeclareLaunchArgument("lidar_ip", default_value="192.168.1.201"),
            DeclareLaunchArgument("start_base", default_value="true"),
            DeclareLaunchArgument("start_lidar", default_value="true"),
            base_launch,
            state_publisher,
            velodyne_driver,
            velodyne_transform,
            pointcloud_to_laserscan,
        ]
    )
