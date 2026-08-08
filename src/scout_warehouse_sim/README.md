# Scout Warehouse SLAM and Nav2 Simulation

ROS 2 Humble과 Gazebo Fortress에서 Scout 2.0, 실제 CAD 형상의 UR3e/Robotiq,
VLP-16 형태의 3D LiDAR를 사용해 창고 SLAM과 Nav2를 시험하는 패키지입니다.
`unita_minicar_sim_ws`에는 의존하지 않습니다.

## Warehouse layout

월드는 23 x 17 m의 폐쇄형 창고이며 중앙에 네 개의 팔레트 랙과 순환 통로가
있습니다. 양쪽 벽에는 UR3e 작업용으로 낮춘 상판 높이 0.57 m의 작업 구역이 있습니다.

| 구역 | 색상 | 작업대 중심 `(x, y)` | 로봇 접근 pose `(x, y, yaw)` |
|---|---|---:|---:|
| A | 빨강 | `(-8.0, 5.0)` | `(-6.85, 5.0, 3.14159)` |
| B | 파랑 | `(-8.0, -5.0)` | `(-6.85, -5.0, 3.14159)` |
| C | 초록 | `(8.0, 5.0)` | `(6.85, 5.0, 0.0)` |
| D | 주황 | `(8.0, -5.0)` | `(6.85, -5.0, 0.0)` |

각 작업대에는 그리퍼 크기에 맞춘 상자와 원통이 별도 동적 entity로 배치되어
있습니다. RViz의 `/workcell_markers`에는 구역 이름과 권장 접근 방향이 표시됩니다.

## Build

```bash
cd /home/gyun/scout_sin_ws
source /opt/ros/humble/setup.bash
colcon build --packages-up-to scout_warehouse_sim --symlink-install
source install/setup.bash
```

별도의 `pointcloud_to_laserscan` apt 패키지는 필요하지 않습니다. 이 패키지에
포함된 변환 노드가 `/points`에서 바닥을 제외한 수평 slice를 만들어 `/scan`으로
발행합니다.

## Run SLAM and Nav2

```bash
ros2 launch scout_warehouse_sim slam.launch.py
```

다른 터미널에서 주행합니다.

```bash
source /home/gyun/scout_sin_ws/install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

지도 작성 중에도 Nav2가 활성화되므로 충분히 탐색한 뒤 RViz의 `Nav2 Goal`을
사용할 수 있습니다. 처음에는 중앙 통로를 한 바퀴 돌고 A–D 구역을 차례로
방문하면 loop closure와 작업대 경계가 잘 생성됩니다.

GUI 없이 센서와 주행만 확인하려면 다음을 실행합니다.

```bash
ros2 launch scout_warehouse_sim simulation.launch.py gui:=false rviz:=false
```

## Save and reuse a map

창고 전체를 탐색한 뒤 맵을 저장합니다.

```bash
ros2 run nav2_map_server map_saver_cli \
  -f /home/gyun/scout_sin_ws/src/scout_warehouse_sim/maps/warehouse
```

SLAM launch를 완전히 종료한 후 저장된 맵으로 localization과 Nav2를 실행합니다.

```bash
ros2 launch scout_warehouse_sim navigation.launch.py \
  map:=/home/gyun/scout_sin_ws/src/scout_warehouse_sim/maps/warehouse.yaml
```

RViz에서 `2D Pose Estimate`로 초기 위치를 지정한 다음 `Nav2 Goal`을 사용합니다.

## Data flow

```text
Gazebo VLP-16 -> /points (PointCloud2)
                    |-> local costmap 3D VoxelLayer
                    `-> pointcloud_to_laserscan.py -> /scan
                                                     |-> SLAM Toolbox
                                                     `-> AMCL/global costmap

Gazebo Scout -> /odometry + odom->base_footprint TF
SLAM/AMCL    -> map->odom TF
Nav2         -> /cmd_vel -> Gazebo Scout
```

주요 토픽은 `/points`, `/scan`, `/odometry`, `/imu/data`, `/map`, `/cmd_vel`,
`/workcell_markers`, `/wrist_camera/image_raw`, `/arm_joint_trajectory`입니다.

## UR3e 동작 확인

시뮬레이션이 실행 중인 다른 터미널에서 다음 안전 자세를 보낼 수 있습니다.

```bash
source /home/gyun/scout_sin_ws/install/setup.bash
ros2 run scout_warehouse_sim arm_pose_demo.py inspect
ros2 run scout_warehouse_sim arm_pose_demo.py home
```

`/arm_joint_trajectory`는 `trajectory_msgs/msg/JointTrajectory` 형식이며 UR3e의
6축을 제어합니다. 손목에 부착된 D435i RGB 영상과 보정 정보는 각각
`/wrist_camera/image_raw`, `/wrist_camera/camera_info`에서 확인할 수 있습니다.

## Pick-and-place extension

현재 UR3e 6축은 Gazebo Fortress의 trajectory controller로 움직입니다.
환경과 집기 물체는 이후 확장을 고려해 다음처럼 분리되어 있습니다.

- 작업대와 rack은 static entity입니다.
- 상자와 원통은 질량·관성·마찰이 있는 dynamic entity입니다.
- A–D 접근 pose는 `config/workcells.yaml`에 정의되어 있습니다.
- Robotiq는 실제 CAD 외형의 열린 자세이지만 손가락은 현재 강체입니다. Fortress 6가
  URDF mimic 관절을 안정적으로 처리하지 못하므로, 다음 단계에서 전용 그리퍼
  controller와 grasp/attach plugin을 추가해야 실제 집기가 가능합니다.
- MoveIt 2를 연결할 때는 현재 6축 joint 이름과 `/arm_joint_trajectory`를 그대로
  사용하거나 `ros2_control` 기반 controller로 교체할 수 있습니다.

처음부터 navigation과 manipulation을 동시에 튜닝하기보다, 저장한 맵에서 A–D
접근 pose까지의 주행을 먼저 안정화한 뒤 arm profile을 활성화하는 것을 권장합니다.
