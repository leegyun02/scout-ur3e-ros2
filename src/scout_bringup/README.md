# Scout Bringup

Scout 모바일 베이스, UR3e가 포함된 통합 URDF, Velodyne VLP-16을 이용해 실기 SLAM,
맵 저장, AMCL localization, Nav2 주행을 실행하는 ROS 2 Humble bringup 패키지입니다.

## 제공 범위

이 패키지의 launch 파일만으로 다음 구성요소를 함께 실행할 수 있습니다.

- Scout CAN 베이스 드라이버
- `scout_ur3e.xacro` 기반 `robot_state_publisher`
- Velodyne VLP-16 패킷 드라이버
- Velodyne 패킷의 `PointCloud2` 변환
- `/velodyne_points`의 2D `/scan` 변환
- SLAM Toolbox 기반 2D SLAM
- Nav2 map saver server
- Map server와 AMCL localization
- Nav2 planner, controller, behavior tree, velocity smoother
- Collision monitor
- RViz

다음 항목은 의도적으로 자동 실행하지 않습니다.

- 맵 작성 중 로봇 수동 조종
- 맵을 저장할 시점과 파일명 선택
- UR3e 실제 로봇 드라이버 및 MoveIt
- RealSense 실제 카메라 드라이버
- Scout의 `can0` 인터페이스 생성 및 활성화

SLAM과 Nav2에 필요한 LiDAR TF는 통합 URDF에서 발행되므로 UR3e 드라이버나
RealSense 드라이버를 실행하지 않아도 사용할 수 있습니다.

## 전체 구조

```text
VLP-16
  └─ velodyne_driver_node
       └─ /velodyne_packets
            └─ velodyne_transform_node
                 └─ /velodyne_points
                      └─ pointcloud_to_laserscan
                           └─ /scan

Scout CAN
  └─ scout_base_node
       ├─ /odometry
       ├─ odom -> base_link
       └─ /cmd_vel

robot_state_publisher
  └─ base_link -> velodyne_link
```

SLAM 중 TF:

```text
map -> odom              slam_toolbox
odom -> base_link        scout_base_node
base_link -> velodyne_link  robot_state_publisher
```

Localization 중 TF:

```text
map -> odom              AMCL
odom -> base_link        scout_base_node
base_link -> velodyne_link  robot_state_publisher
```

`map -> odom`은 SLAM Toolbox 또는 AMCL 중 하나만 발행해야 합니다.

## 현재 운용 설정

- `slam.launch.py`, `navigation.launch.py`, `system.launch.py`는 RViz를 항상 실행
- RViz LaserScan은 과거 프레임을 누적하지 않아 이동 시 잔상을 최소화
- Local costmap은 센서 관측을 누적하지 않고 `5 Hz`로 갱신 및 발행
- AMCL은 `5 cm` 이동 또는 `0.05 rad` 회전마다 자세 갱신
- AMCL 초기 자세는 맵 원점 `(x=0, y=0, yaw=0)`

로봇이 맵 원점에서 출발하지 않으면 RViz의 `2D Pose Estimate`로 실제 위치와
방향을 지정합니다.

## 실행 전 확인

### CAN

Scout에서 사용하는 CAN 인터페이스가 존재하고 UP 상태인지 확인합니다.

```bash
ip link show can0
```

인터페이스 이름이 다르면 launch 실행 시 `can_interface`를 지정합니다.

```bash
can_interface:=can1
```

### Velodyne

기본 LiDAR IP는 `192.168.1.201`입니다.

```bash
ping 192.168.1.201
```

주소가 다르면 launch 실행 시 지정합니다.

```bash
lidar_ip:=192.168.1.201
```

## Launch 파일

### `robot_bringup.launch.py`

Scout 베이스, 통합 URDF TF, Velodyne, PointCloud2, LaserScan을 실행합니다.
SLAM이나 Nav2 없이 하드웨어만 확인할 때 사용합니다.

```bash
ros2 launch scout_bringup robot_bringup.launch.py
```

주요 인자:

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `can_interface` | `can0` | Scout CAN 인터페이스 |
| `lidar_ip` | `192.168.1.201` | VLP-16 IP |
| `start_base` | `true` | Scout 베이스 드라이버 실행 |
| `start_lidar` | `true` | Velodyne 파이프라인 실행 |
| `use_sim_time` | `false` | 실기에서는 `false` |

### `localization.launch.py`

실기 bringup, map server, AMCL, RViz를 실행합니다. Nav2 주행 없이 localization만
검사할 때 사용합니다. `map`을 생략하면 패키지의 `maps/scout_map.yaml`을
사용합니다.

```bash
ros2 launch scout_bringup localization.launch.py
```

다른 맵을 지정하려면:

```bash
ros2 launch scout_bringup localization.launch.py \
  map:="$HOME/maps/scout_map.yaml"
```

AMCL은 기본적으로 맵 원점 `(0, 0, 0, yaw=0)`에서 시작합니다. 로봇이 맵
원점이 아닌 곳에 있으면 RViz의 `2D Pose Estimate`로 실제 위치와 방향을
다시 지정합니다.

### `navigation.launch.py`

실기 bringup, map server, AMCL, Nav2 전체 스택, collision monitor, RViz를
실행합니다. `map`을 생략하면 패키지의 `maps/scout_map.yaml`을 사용합니다.

```bash
ros2 launch scout_bringup navigation.launch.py
```

다른 맵을 지정하려면:

```bash
ros2 launch scout_bringup navigation.launch.py \
  map:="$HOME/maps/scout_map.yaml"
```

기본 원점 초기화가 실제 위치와 맞는지 확인한 후 RViz의 `Nav2 Goal`을
사용합니다. 위치가 다르면 먼저 `2D Pose Estimate`로 교정합니다.

### `system.launch.py`

일반 운용에 권장하는 단일 진입점입니다.

SLAM:

```bash
ros2 launch scout_bringup system.launch.py mode:=mapping
```

Localization 및 Nav2:

```bash
ros2 launch scout_bringup system.launch.py mode:=navigation
```

다른 맵을 지정하려면:

```bash
ros2 launch scout_bringup system.launch.py \
  mode:=navigation \
  map:="$HOME/maps/another_map.yaml"
```

공통 인자 사용 예:

```bash
ros2 launch scout_bringup system.launch.py \
  mode:=mapping \
  can_interface:=can0 \
  lidar_ip:=192.168.1.201
```

## SLAM 및 맵 생성 절차

### 1. SLAM 실행

```bash
ros2 launch scout_bringup system.launch.py mode:=mapping
```

### 2. 센서와 TF 확인

다른 터미널에서:

```bash
source ~/scout-ur3e-ros2/install/setup.bash

ros2 topic hz /velodyne_packets
ros2 topic hz /velodyne_points
ros2 topic hz /scan
ros2 topic hz /odometry

ros2 run tf2_ros tf2_echo base_link velodyne_link
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo map odom
```

기대 결과:

- `/velodyne_packets`: VLP-16 패킷 수신
- `/velodyne_points`: 3D PointCloud2
- `/scan`: SLAM Toolbox가 사용하는 2D LaserScan
- `/odometry`: Scout wheel odometry
- `base_link -> velodyne_link`: URDF에 설정된 LiDAR 위치
- `map -> odom`: SLAM Toolbox가 발행하는 위치 보정

### 3. 로봇 수동 조종

조종 노드 실행:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

급회전과 빠른 가감속을 피하고, 이미 지나간 장소를 다시 방문하여 loop closure가
형성되도록 주행합니다.

### 4. 맵 저장

맵이 완성되면 별도 터미널에서:

```bash
mkdir -p "$HOME/maps"

ros2 run nav2_map_server map_saver_cli \
  -f "$HOME/maps/scout_map"
```

다음 두 파일이 생성됩니다.

```text
~/maps/scout_map.pgm
~/maps/scout_map.yaml
```

## 저장한 맵으로 Nav2 실행

SLAM launch를 완전히 종료한 후 실행합니다. SLAM Toolbox와 AMCL을 동시에 켜면
둘 다 `map -> odom`을 발행하여 TF가 충돌합니다.

패키지에 포함된 기본 `scout_map` 사용:

```bash
ros2 launch scout_bringup system.launch.py mode:=navigation
```

외부 맵 사용:

```bash
ros2 launch scout_bringup system.launch.py \
  mode:=navigation \
  map:="$HOME/maps/scout_map.yaml"
```

순서:

1. RViz에서 지도와 LaserScan이 정렬되는지 확인
2. 시작 위치가 맵 원점과 다르면 `2D Pose Estimate`로 위치 지정
3. AMCL particle cloud가 수렴하는지 확인
4. `Nav2 Goal`로 목적지 지정

Nav2 속도 명령 흐름:

```text
controller_server
  -> /cmd_vel_nav
  -> velocity_smoother
  -> /cmd_vel_smoothed
  -> collision_monitor
  -> /cmd_vel
  -> scout_base_node
```

## 주요 토픽

| 토픽 | 형식 | 설명 |
|---|---|---|
| `/velodyne_packets` | `velodyne_msgs/VelodyneScan` | VLP-16 원시 패킷 |
| `/velodyne_points` | `sensor_msgs/PointCloud2` | 변환된 3D 포인트 |
| `/scan` | `sensor_msgs/LaserScan` | SLAM, AMCL, collision monitor 입력 |
| `/odometry` | `nav_msgs/Odometry` | Scout wheel odometry |
| `/map` | `nav_msgs/OccupancyGrid` | SLAM 또는 map server 지도 |
| `/cmd_vel` | `geometry_msgs/Twist` | Scout 최종 속도 명령 |

## 설정 파일

- `config/velodyne_driver.yaml`: VLP-16 IP, frame, RPM, UDP 포트
- `config/velodyne_transform.yaml`: VLP-16 PointCloud 변환 범위
- `config/pointcloud_to_laserscan.yaml`: 2D scan 높이와 거리 필터
- `config/slam_toolbox.yaml`: SLAM Toolbox mapping 설정
- `scout_nav2/params/scout_amcl.yaml`: AMCL 및 Nav2 설정

모든 경로는 package share 또는 launch 인자로 처리하며 특정 사용자 홈 디렉터리를
코드에 하드코딩하지 않습니다.
