# Scout 창고 시뮬레이션

[메인 README로 돌아가기](./README.md)

ROS 2 Humble과 Gazebo Fortress에서 Scout 2.0, UR3e, Robotiq 2F-85,
Velodyne 형태의 3D LiDAR와 손목 RGB 카메라를 함께 시험하는 시뮬레이션입니다.

이 문서는 다음 작업을 순서대로 설명합니다.

~~~text
시뮬레이션 실행
→ 키보드 주행
→ SLAM과 맵 저장
→ 저장 지도에서 Nav2 주행
→ UR3e와 손목 카메라 확인
~~~

## Demo

| SLAM Mapping | Nav2 자율주행 |
|---|---|
| <img src="./gif/sim_slam_small.gif" width="430" alt="Scout warehouse simulation SLAM mapping"> | <img src="./gif/sim_nav2_small.gif" width="430" alt="Scout warehouse simulation Nav2 autonomous navigation"> |

## Simulation Overview

- Gazebo Fortress(`ign gazebo`)
- AgileX Scout 2.0 차동구동 베이스
- UR 공식 CAD 형상의 UR3e와 6개 회전 관절
- 열린 자세로 고정된 Robotiq 2F-85 외형
- UR3e 손목의 RGB 카메라
- Scout 전방의 VLP-16 형태 3D LiDAR
- IMU와 ground-truth odometry
- 23 × 17 m 창고와 A/B/C/D 작업 구역

### Workcells

| 구역 | 색상 | 작업대 중심 `(x, y, z)` | 접근 pose `(x, y, yaw)` |
|---|---|---:|---:|
| A | 빨강 | `(-8.0, 5.0, 0.57)` | `(-6.85, 5.0, 3.14159)` |
| B | 파랑 | `(-8.0, -5.0, 0.57)` | `(-6.85, -5.0, 3.14159)` |
| C | 초록 | `(8.0, 5.0, 0.57)` | `(6.85, 5.0, 0.0)` |
| D | 주황 | `(8.0, -5.0, 0.57)` | `(6.85, -5.0, 0.0)` |

접근 pose의 기준 좌표계는 `map`입니다. 값은
[`workcells.yaml`](./src/scout_warehouse_sim/config/workcells.yaml)에 정의되어
있습니다.

### Data Flow

~~~mermaid
flowchart LR
    GZ[Gazebo VLP-16] -->|/points PointCloud2| P2L[velodyne_to_scan]
    P2L -->|/scan LaserScan| SLAM[SLAM Toolbox / AMCL]
    P2L -->|/scan| GC[Global Costmap]
    GZ -->|/points| LC[Local Costmap VoxelLayer]

    GZ -->|/odometry + odom TF| TF[TF Tree]
    SLAM -->|map → odom| TF

    GC --> NAVFN[NavFn Dijkstra]
    NAVFN -->|Global Path| DWB[DWB Controller]
    LC --> DWB
    DWB -->|/cmd_vel_nav| VS[Velocity Smoother]
    VS -->|/cmd_vel| GZ
~~~

현재 시뮬레이션 Nav2 설정은 다음 조합입니다.

| 영역 | 설정 |
|---|---|
| Global Planner | `NavfnPlanner`, `use_astar: false` (Dijkstra) |
| Controller | `dwb_core::DWBLocalPlanner` |
| Local Costmap | `/points` → `VoxelLayer` |
| Global Costmap | `/scan` → `ObstacleLayer` |
| Mapping | SLAM Toolbox |
| Localization | AMCL |

알고리즘 설명은 [Nav2 학습 자료](./nav2_study/README.md)를 참고합니다.

## Build

~~~bash
source /opt/ros/humble/setup.bash
cd /path/to/scout_sin_ws
export ROS2_WS="$PWD"

colcon build --packages-up-to scout_warehouse_sim --symlink-install
source install/setup.bash
~~~

새 터미널에서는 다음 환경을 다시 불러옵니다.

~~~bash
source /opt/ros/humble/setup.bash
source "$ROS2_WS/install/setup.bash"
~~~

## Launch Modes

세 모드는 동시에 실행하지 않습니다. 다른 모드로 바꿀 때 기존 launch와 Gazebo를
`Ctrl+C`로 완전히 종료합니다.

| 목적 | Launch | 포함되는 기능 |
|---|---|---|
| 센서·주행·UR3e 시험 | `simulation.launch.py` | Gazebo, bridge, RViz |
| 새 지도 작성 | `slam.launch.py` | Simulation + SLAM Toolbox + Nav2 |
| 저장 지도 자율주행 | `navigation.launch.py` | Simulation + map server + AMCL + Nav2 |

### Simulation Only

~~~bash
ros2 launch scout_warehouse_sim simulation.launch.py
~~~

화면 표시를 선택할 수 있습니다.

~~~bash
# Gazebo와 RViz를 모두 표시하지 않음
ros2 launch scout_warehouse_sim simulation.launch.py gui:=false rviz:=false

# Gazebo만 표시
ros2 launch scout_warehouse_sim simulation.launch.py rviz:=false
~~~

시작 pose도 변경할 수 있습니다.

~~~bash
ros2 launch scout_warehouse_sim simulation.launch.py \
  x:=1.0 y:=2.0 yaw:=1.5708
~~~

`z` 기본값 `0.2346`은 정상 스폰 높이이므로 특별한 이유가 없으면 변경하지
않습니다.

### SLAM Mapping

~~~bash
ros2 launch scout_warehouse_sim slam.launch.py
~~~

GUI 없이 실행:

~~~bash
ros2 launch scout_warehouse_sim slam.launch.py gui:=false rviz:=false
~~~

### Saved-map Navigation

SLAM launch를 종료한 뒤 저장된 map YAML을 지정합니다.

~~~bash
ros2 launch scout_warehouse_sim navigation.launch.py \
  map:="$ROS2_WS/src/scout_warehouse_sim/maps/warehouse.yaml"
~~~

GUI 없이 실행:

~~~bash
ros2 launch scout_warehouse_sim navigation.launch.py \
  map:="$ROS2_WS/src/scout_warehouse_sim/maps/warehouse.yaml" \
  gui:=false rviz:=false
~~~

## Keyboard Driving

키보드 터미널을 클릭하고 영문 입력 상태에서 사용합니다.

### Simulation Only

~~~bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
~~~

이 모드에서는 명령이 `/cmd_vel`로 바로 전달됩니다.

### SLAM 또는 Navigation 실행 중

~~~bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r cmd_vel:=cmd_vel_nav
~~~

Nav2가 사용하는 velocity pipeline과 충돌하지 않도록 `/cmd_vel_nav`로 보냅니다.
Nav2 goal을 수행 중일 때는 teleop을 동시에 사용하지 않습니다.

~~~text
u    i    o
j    k    l
m    ,    .
~~~

- `i` / `,`: 전진 / 후진
- `j` / `l`: 제자리 좌회전 / 우회전
- `u`, `o`, `m`, `.`: 전후진하며 회전
- `k`: 정지
- `q` / `z`: 전체 속도 10% 증가 / 감소
- `w` / `x`: 선속도 10% 증가 / 감소
- `e` / `c`: 각속도 10% 증가 / 감소

Scout는 차동구동이므로 Shift 조합의 좌우 평행이동은 지원하지 않습니다. SLAM
중에는 급회전을 피하고 처음에는 약 `0.2~0.3 m/s`로 천천히 주행합니다.

## Mapping Workflow

1. `slam.launch.py`를 실행합니다.
2. RViz에서 `/scan`, TF와 로봇 위치를 확인합니다.
3. 중앙 통로를 천천히 한 바퀴 돕니다.
4. A, B, C, D 구역을 방문합니다.
5. 이미 지나간 구간으로 돌아와 loop closure를 유도합니다.
6. 벽과 랙이 이중으로 보이지 않는지 확인한 뒤 맵을 저장합니다.

### Map과 TF 확인

~~~bash
ros2 topic hz /map
ros2 topic echo /map --once --field info
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_footprint
~~~

### Map 저장

~~~bash
mkdir -p "$ROS2_WS/src/scout_warehouse_sim/maps"
ros2 run nav2_map_server map_saver_cli \
  -f "$ROS2_WS/src/scout_warehouse_sim/maps/warehouse"
~~~

`warehouse.yaml`과 `warehouse.pgm`이 생성됩니다. 같은 이름은 기존 파일을
덮어쓸 수 있으므로 보존할 맵은 `warehouse_v1`처럼 다른 이름으로 저장합니다.

## Navigation Workflow

1. SLAM launch를 완전히 종료합니다.
2. `navigation.launch.py`에 저장한 map YAML을 전달합니다.
3. RViz의 `2D Pose Estimate`로 Gazebo 로봇의 초기 위치와 방향을 지정합니다.
4. 지도와 `/scan`이 일치하고 particle cloud가 수렴하는지 확인합니다.
5. `Nav2 Goal`로 목적지와 최종 방향을 지정합니다.

초기 pose가 틀리면 경로와 장애물 위치가 어긋납니다. 주행 중 수동 개입이 필요하면
Nav2 goal을 먼저 취소한 뒤 teleop을 사용합니다.

### A/B/C/D 접근 지점

아래 명령은 `map` 좌표계 기준입니다.

<details>
<summary>A–D 구역 NavigateToPose 명령 보기</summary>

#### A 구역

~~~bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
'{pose: {header: {frame_id: map}, pose: {position: {x: -6.85, y: 5.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 1.0, w: 0.0}}}}' \
--feedback
~~~

#### B 구역

~~~bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
'{pose: {header: {frame_id: map}, pose: {position: {x: -6.85, y: -5.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 1.0, w: 0.0}}}}' \
--feedback
~~~

#### C 구역

~~~bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
'{pose: {header: {frame_id: map}, pose: {position: {x: 6.85, y: 5.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}' \
--feedback
~~~

#### D 구역

~~~bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
'{pose: {header: {frame_id: map}, pose: {position: {x: 6.85, y: -5.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}' \
--feedback
~~~

</details>

## Sensor Check

~~~bash
# Simulation clock와 base
ros2 topic hz /clock
ros2 topic hz /odometry

# Velodyne와 변환된 scan
ros2 topic hz /points
ros2 topic hz /scan

# IMU, arm, camera
ros2 topic hz /imu/data
ros2 topic echo /joint_states --once
ros2 topic hz /wrist_camera/image_raw
~~~

Gazebo LiDAR는 3D `/points`를 생성합니다. 프로젝트의
[`pointcloud_to_laserscan.py`](./src/scout_warehouse_sim/scripts/pointcloud_to_laserscan.py)가
높이 `-0.28~1.20 m`, 거리 `0.40~50.0 m` 범위의 점을 선택해 `/scan`을
만듭니다.

## UR3e and Wrist Camera

Gazebo 시뮬레이션이 실행 중일 때 제공된 안전 자세를 전송할 수 있습니다.

~~~bash
# 점검 자세
ros2 run scout_warehouse_sim arm_pose_demo.py inspect

# 접힌 기본 자세
ros2 run scout_warehouse_sim arm_pose_demo.py home

# 5초 동안 점검 자세로 이동
ros2 run scout_warehouse_sim arm_pose_demo.py inspect --duration 5.0
~~~

실제 [`arm_pose_demo.py`](./src/scout_warehouse_sim/scripts/arm_pose_demo.py)에 정의된
`home` 자세는 다음과 같습니다.

| Joint | Position (rad) |
|---|---:|
| `ur3e_shoulder_pan_joint` | `0.0` |
| `ur3e_shoulder_lift_joint` | `-1.5708` |
| `ur3e_elbow_joint` | `1.5708` |
| `ur3e_wrist_1_joint` | `-1.5708` |
| `ur3e_wrist_2_joint` | `-1.5708` |
| `ur3e_wrist_3_joint` | `1.5708` |

관절과 카메라를 확인합니다.

~~~bash
ros2 topic echo /joint_states --once
ros2 topic hz /wrist_camera/image_raw
ros2 topic echo /wrist_camera/camera_info --once
ros2 run rqt_image_view rqt_image_view /wrist_camera/image_raw
~~~

- 관절값 단위는 radian입니다.
- 처음에는 제공된 `home`, `inspect` 자세만 사용합니다.
- arm이 움직이는 동안 Scout를 급격히 주행시키지 않습니다.
- 현재 Robotiq 손가락은 열린 자세의 강체이며 개폐 명령을 지원하지 않습니다.
- 실제 pick-and-place에는 MoveIt 2, gripper controller와 물체 attach/detach
  기능이 추가로 필요합니다.

## Topics and TF

| Topic | Type | Role |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Gazebo Scout에 전달되는 최종 속도 |
| `/cmd_vel_nav` | `geometry_msgs/msg/Twist` | Nav2 velocity smoother 입력 |
| `/odometry` | `nav_msgs/msg/Odometry` | Gazebo Scout odometry |
| `/points` | `sensor_msgs/msg/PointCloud2` | Velodyne 3D point cloud |
| `/scan` | `sensor_msgs/msg/LaserScan` | SLAM, AMCL, Global Costmap 입력 |
| `/imu/data` | `sensor_msgs/msg/Imu` | Scout IMU |
| `/joint_states` | `sensor_msgs/msg/JointState` | Scout와 UR3e 관절 상태 |
| `/arm_joint_trajectory` | `trajectory_msgs/msg/JointTrajectory` | UR3e 자세 명령 |
| `/wrist_camera/image_raw` | `sensor_msgs/msg/Image` | 손목 RGB 영상 |
| `/map` | `nav_msgs/msg/OccupancyGrid` | SLAM 또는 map server 지도 |
| `/workcell_markers` | `visualization_msgs/msg/MarkerArray` | 작업 구역과 접근 방향 |

주요 TF 구조:

~~~text
map → odom → base_footprint → base_link/mobile_robot_base_link
                                      ├─ velodyne_link
                                      └─ UR3e links → wrist camera frames
~~~

- SLAM Toolbox 또는 AMCL: `map → odom`
- Gazebo odometry: `odom → base_footprint`
- `robot_state_publisher`: Scout, UR3e, LiDAR와 camera link

~~~bash
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo map base_footprint
ros2 topic info /cmd_vel -v
ros2 topic info /points -v
~~~

## Troubleshooting

### Scout가 움직이지 않음

- Gazebo가 Pause 상태인지 확인합니다.
- teleop 터미널의 포커스와 영문 입력 상태를 확인합니다.
- 실행 모드에 맞게 `/cmd_vel` 또는 `/cmd_vel_nav`를 사용합니다.
- `ros2 topic echo /cmd_vel`로 최종 명령을 확인합니다.

### `/map`이 나오지 않음

~~~bash
ros2 node list | grep slam
ros2 topic hz /scan
ros2 run tf2_ros tf2_echo odom base_footprint
~~~

`/scan`이나 odometry TF가 없으면 SLAM이 지도를 만들 수 없습니다.

### Nav2 Goal을 줘도 움직이지 않음

~~~bash
ros2 lifecycle nodes
ros2 action info /navigate_to_pose
ros2 topic hz /map
ros2 run tf2_ros tf2_echo map base_link
~~~

저장 지도 모드에서는 `2D Pose Estimate`가 먼저 필요합니다. Goal이 장애물이나
벽 안에 있지 않은지도 확인합니다.

### LiDAR 또는 camera 데이터가 없음

~~~bash
ros2 topic hz /clock
ros2 topic hz /points
ros2 topic hz /scan
ros2 topic hz /wrist_camera/image_raw
ros2 node list | grep scout_gz_bridge
~~~

Gazebo가 Pause 상태면 `/clock`과 sensor data도 멈춥니다.

### UR3e가 움직이지 않음

~~~bash
ros2 topic info /arm_joint_trajectory -v
ros2 topic hz /joint_states
ros2 run scout_warehouse_sim arm_pose_demo.py inspect --duration 5.0
~~~

`/arm_joint_trajectory`에 Gazebo bridge subscriber가 있는지 확인합니다.

## Stop

launch, teleop과 `rqt_image_view`를 각각 `Ctrl+C`로 종료합니다. 다른 모드를
실행하기 전에 기존 Gazebo와 launch가 완전히 종료됐는지 확인합니다.

## Project Files

~~~text
src/scout_warehouse_sim/
├── launch/
│   ├── simulation.launch.py
│   ├── slam.launch.py
│   └── navigation.launch.py
├── config/
│   ├── nav2_params.yaml
│   ├── slam_toolbox.yaml
│   ├── ros_gz_bridge.yaml
│   └── workcells.yaml
├── scripts/
│   ├── pointcloud_to_laserscan.py
│   ├── arm_pose_demo.py
│   └── workcell_markers.py
├── worlds/scout_pick_place_warehouse.sdf
├── urdf/scout_ur3e_velodyne.urdf.xacro
├── maps/
└── rviz/warehouse_nav2.rviz
~~~
