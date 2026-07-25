cmake_minimum_required(VERSION 3.8)
project(scout_bringup)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch maps
  DESTINATION share/${PROJECT_NAME}
)

install(
  FILES README.md PARAMETER_TUNING.md
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
