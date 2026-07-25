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

## 설치 및 빌드

저장소 루트에서 실행합니다.

```bash
cd ~/scout-ur3e-ros2

source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y

colcon build --symlink-install
source install/setup.bash
```

새 터미널을 열 때마다 다음을 실행합니다.

```bash
cd ~/scout-ur3e-ros2
source /opt/ros/humble/setup.bash
source install/setup.bash
```

선택적으로 `~/.bashrc`에 workspace setup을 추가할 수 있습니다.

```bash
echo 'source ~/scout-ur3e-ros2/install/setup.bash' >> ~/.bashrc
```

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

베이스 없이 LiDAR와 TF만 확인:

```bash
ros2 launch scout_bringup robot_bringup.launch.py start_base:=false
```

LiDAR 없이 Scout odometry만 확인:

```bash
ros2 launch scout_bringup robot_bringup.launch.py start_lidar:=false
```

### `slam.launch.py`

실기 bringup, SLAM Toolbox mapping, map saver server, RViz를 실행합니다.

```bash
ros2 launch scout_bringup slam.launch.py
```

하드웨어 bringup을 다른 터미널에서 이미 실행한 경우:

```bash
ros2 launch scout_bringup slam.launch.py start_robot:=false
```

### `localization.launch.py`

실기 bringup, map server, AMCL, RViz를 실행합니다. Nav2 주행 없이 localization만
검사할 때 사용합니다.

```bash
ros2 launch scout_bringup localization.launch.py \
  map:="$HOME/maps/scout_map.yaml"
```

RViz에서 `2D Pose Estimate`로 지도상의 초기 위치와 방향을 지정합니다.

### `navigation.launch.py`

실기 bringup, map server, AMCL, Nav2 전체 스택, collision monitor, RViz를
실행합니다.

```bash
ros2 launch scout_bringup navigation.launch.py \
  map:="$HOME/maps/scout_map.yaml"
```

초기 위치를 지정한 후 RViz의 `Nav2 Goal`을 사용합니다.

### `system.launch.py`

일반 운용에 권장하는 단일 진입점입니다.

SLAM:

```bash
ros2 launch scout_bringup system.launch.py mode:=mapping
```

Localization 및 Nav2:

```bash
ros2 launch scout_bringup system.launch.py \
  mode:=navigation \
  map:="$HOME/maps/scout_map.yaml"
```

공통 인자 사용 예:

```bash
ros2 launch scout_bringup system.launch.py \
  mode:=mapping \
  can_interface:=can0 \
  lidar_ip:=192.168.1.201 \
  use_rviz:=true
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

`teleop_twist_keyboard`가 설치되어 있지 않으면:

```bash
sudo apt install ros-humble-teleop-twist-keyboard
```

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

```bash
ros2 launch scout_bringup system.launch.py \
  mode:=navigation \
  map:="$HOME/maps/scout_map.yaml"
```

순서:

1. RViz에서 지도와 LaserScan이 정렬되는지 확인
2. `2D Pose Estimate`로 초기 위치 지정
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

## 문제 해결

### `/velodyne_packets`가 나오지 않음

- VLP-16 전원과 Ethernet 연결 확인
- PC와 VLP-16이 같은 subnet인지 확인
- `lidar_ip` 확인
- UDP 2368 포트 확인

### `/velodyne_points`가 나오지 않음

- `/velodyne_packets`가 먼저 발행되는지 확인
- `velodyne_transform_node`가 실행 중인지 확인
- VLP-16 calibration 파일이 설치됐는지 확인

### `/scan`이 나오지 않음

- `pointcloud_to_laserscan` 설치 확인
- `/velodyne_points` 발행 확인
- `base_link -> velodyne_link` TF 확인

### 맵이 흔들리거나 겹침

- `/odometry`와 `odom -> base_link` 확인
- LiDAR 장착 위치가 URDF의 `velodyne_joint`와 일치하는지 확인
- 너무 빠른 회전과 주행 속도 피하기
- `/scan`에 바닥이나 로봇 본체가 과도하게 포함되는지 RViz에서 확인
- 필요하면 `config/pointcloud_to_laserscan.yaml`의 높이 범위 조정

### Nav2가 움직이지 않음

- RViz에서 초기 위치를 지정했는지 확인
- `map -> odom -> base_link` TF가 모두 연결되는지 확인
- `/scan`이 collision monitor 영역 안에 로봇 자체를 장애물로 표시하는지 확인
- `/cmd_vel_nav`, `/cmd_vel_smoothed`, `/cmd_vel`을 차례로 확인

### `libdiagnostic_updater.so` 오류

```bash
sudo apt install --reinstall ros-humble-diagnostic-updater
```

## 설정 파일

- `config/velodyne_driver.yaml`: VLP-16 IP, frame, RPM, UDP 포트
- `config/velodyne_transform.yaml`: VLP-16 PointCloud 변환 범위
- `config/pointcloud_to_laserscan.yaml`: 2D scan 높이와 거리 필터
- `config/slam_toolbox.yaml`: SLAM Toolbox mapping 설정
- `scout_nav2/params/scout_amcl.yaml`: AMCL 및 Nav2 설정

모든 경로는 package share 또는 launch 인자로 처리하며 특정 사용자 홈 디렉터리를
코드에 하드코딩하지 않습니다.
