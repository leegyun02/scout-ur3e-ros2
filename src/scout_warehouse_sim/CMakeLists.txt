cmake_minimum_required(VERSION 3.8)
project(scout_warehouse_sim)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch maps models rviz urdf worlds
  DESTINATION share/${PROJECT_NAME}
  PATTERN "__pycache__" EXCLUDE
  PATTERN "*.pyc" EXCLUDE
)

install(
  PROGRAMS
    scripts/pointcloud_to_laserscan.py
    scripts/workcell_markers.py
    scripts/arm_pose_demo.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
