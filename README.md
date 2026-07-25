# AgileX Scout 실기기 실행 가이드

이 문서는 AgileX Scout의 CAN 통신 확인, Velodyne VLP-16 점검, Scout 드라이버 실행, SLAM 지도 생성·저장, Nav2 자율주행 순서를 정리한 가이드입니다.

## 실행 전 필수 사항

- 모든 작업은 `/home/gyun/ros2_ws`에서 진행합니다.
- **새 터미널을 열 때마다 반드시 `ccb`를 먼저 실행합니다.**
- `ccb`가 끝난 뒤 다음 명령을 실행하고, 각 노드가 정상적으로 올라온 것을 확인한 후 다음 단계로 넘어갑니다.
- 한 번에 여러 명령을 빠르게 실행하지 말고, 로그와 토픽을 천천히 확인합니다.
- 아래에서 종료하라고 안내하기 전까지 실행 중인 터미널을 닫지 않습니다.
- Scout 주변을 정리하고 비상 정지 장치를 바로 사용할 수 있는 상태에서 진행합니다.

모든 새 터미널의 공통 준비 명령:

```bash
cd /home/gyun/ros2_ws
ccb
source install/setup.bash
```

> `ccb`는 이 PC의 사용자 정의 빌드 명령입니다. 터미널에서 `ccb: command not found`가 나오면 먼저 해당 명령 또는 alias 설정을 확인해야 합니다.

## 전체 실행 순서

1. CAN 통신 확인
2. Velodyne LiDAR 단독 점검
3. Scout 및 LiDAR 통합 드라이버 실행
4. SLAM 실행
5. 지도 저장
6. SLAM 종료
7. AMCL 기반 Nav2 실행
8. RViz2에서 초기 위치와 목적지 설정

## 1. CAN 통신 확인

### 터미널 1 — CAN 인터페이스 활성화

공통 준비 명령을 실행한 후:

```bash
cd src/ugv_sdk/scripts
bash bringup_can2usb_500k.bash
```

`can0` 인터페이스가 정상적으로 활성화되었는지 확인합니다.

### 터미널 2 — CAN 데이터 확인

새 터미널에서 공통 준비 명령을 실행한 후:

```bash
candump can0
```

CAN 프레임이 계속 출력되면 통신이 정상입니다. 아무 데이터도 나오지 않으면 USB-CAN 연결, Scout 전원, `can0` 상태 및 bitrate `500 kbit/s`를 확인합니다.

확인이 끝나면 `Ctrl+C`로 `candump`만 종료합니다. 활성화된 `can0` 인터페이스는 이후 Scout 드라이버에서 사용하므로 유지합니다.

## 2. Velodyne LiDAR 단독 점검

LiDAR는 **드라이버를 먼저 실행한 뒤** pointcloud 변환 노드를 실행합니다.

### 터미널 3 — Velodyne 드라이버

새 터미널에서 공통 준비 명령을 실행한 후:

```bash
ros2 launch velodyne_driver velodyne_driver_node-VLP16-launch.py
```

에러 없이 패킷을 수신하는지 확인하고 이 터미널을 유지합니다.

### 터미널 4 — PointCloud 변환

새 터미널에서 공통 준비 명령을 실행한 후:

```bash
ros2 launch velodyne_pointcloud velodyne_transform_node-VLP16-launch.py
```

PointCloud 토픽을 확인하려면:

```bash
ros2 topic hz /velodyne_points
```

필요하면 RViz2에서 `PointCloud2` 디스플레이를 추가하고 `/velodyne_points` 토픽을 선택합니다.

### 단독 점검 후 전환

LiDAR 데이터가 정상임을 확인했으면 다음과 같이 전환합니다.

1. Velodyne 드라이버를 실행한 터미널 3만 `Ctrl+C`로 종료합니다.
2. PointCloud 변환 노드를 실행한 터미널 4는 계속 유지합니다.
3. 다음 단계의 통합 launch를 터미널 3에서 실행합니다.

> `scout_robot_lidar.launch.py`는 Velodyne 패킷 드라이버를 자체적으로 실행하지만, 패킷을 `/velodyne_points`로 변환하는 `velodyne_transform_node`는 포함하지 않습니다. 따라서 드라이버 중복을 피하기 위해 단독 드라이버만 종료하고, 터미널 4의 PointCloud 변환 노드는 유지해야 합니다.

## 3. Scout 및 LiDAR 통합 드라이버 실행

### 터미널 3 — 통합 bringup

새 터미널에서 공통 준비 명령을 실행한 후:

```bash
ros2 launch agilex_scout scout_robot_lidar.launch.py
```

이 launch는 다음 기능을 함께 실행합니다.

- Scout base 드라이버
- Scout robot state publisher
- Velodyne VLP-16 패킷 드라이버
- 터미널 4에서 생성한 `/velodyne_points`를 `/scan`으로 변환하는 노드
- RViz2

다음 토픽이 정상적으로 갱신되는지 확인합니다.

```bash
ros2 topic hz /velodyne_points
ros2 topic hz /scan
ros2 topic hz /odometry
```

확인 후 통합 bringup 터미널은 계속 유지합니다.

## 4. SLAM 실행

### 터미널 5 — Mapping

새 터미널에서 공통 준비 명령을 실행한 후:

```bash
ros2 launch scout_nav2 nav2.launch.py simulation:=false slam:=true localization:=slam_toolbox
```

이 단계에서는 기존 맵 없이 `slam_toolbox`로 새로운 지도를 생성합니다. RViz2에서 지도가 정상적으로 생성되는지 확인하면서 Scout를 천천히 이동합니다.

> **중요:** 지도를 저장하기 전까지 SLAM 터미널과 통합 bringup 터미널을 절대로 종료하지 마세요.

## 5. 지도 저장

현재 실기기 Nav2 설정은 기본적으로 아래 파일을 읽습니다.

```text
/home/gyun/ros2_ws/src/scout_nav2/scout_nav2/maps/my_map.yaml
```

따라서 별도 설정 변경 없이 바로 Nav2를 사용하려면 지도 이름을 `my_map`으로 저장합니다.

### 터미널 6 — Map saver 실행

새 터미널에서 공통 준비 명령을 실행한 후:

```bash
ros2 launch nav2_map_server map_saver_server.launch.py
```

다른 터미널의 SLAM launch에서 map saver가 이미 실행되어 노드 또는 서비스 중복 오류가 발생한다면, 이 터미널은 종료하고 다음의 저장 서비스 호출만 진행합니다.

### 터미널 7 — 저장 서비스 호출

새 터미널에서 공통 준비 명령을 실행한 후:

```bash
ros2 service call /map_saver/save_map nav2_msgs/srv/SaveMap \
"{map_url: '/home/gyun/ros2_ws/src/scout_nav2/scout_nav2/maps/my_map', image_format: 'pgm', map_mode: 'trinary', free_thresh: 0.25, occupied_thresh: 0.65}"
```

저장이 완료되면 다음 파일이 생성되었는지 확인합니다.

```bash
ls -l src/scout_nav2/scout_nav2/maps/my_map.pgm \
      src/scout_nav2/scout_nav2/maps/my_map.yaml
```

서비스 응답이 성공이고 두 파일이 존재하는 것을 확인한 뒤에만 SLAM 터미널을 `Ctrl+C`로 종료합니다.

## 6. 다른 이름으로 지도 저장하기

`my_map` 대신 원하는 이름을 사용할 경우, 저장 명령의 `map_url` 마지막 부분을 변경합니다.

예를 들어 `lab_map`으로 저장하려면:

```bash
ros2 service call /map_saver/save_map nav2_msgs/srv/SaveMap \
"{map_url: '/home/gyun/ros2_ws/src/scout_nav2/scout_nav2/maps/lab_map', image_format: 'pgm', map_mode: 'trinary', free_thresh: 0.25, occupied_thresh: 0.65}"
```

현재 `nav2.launch.py`에는 실기기 맵 이름이 `my_map.yaml`로 지정되어 있습니다. 다른 맵을 사용하려면 아래 파일의 `map_file` 값을 저장한 YAML 파일명으로 변경합니다.

```text
src/scout_nav2/scout_nav2/launch/nav2.launch.py
```

변경 예시:

```python
map_file = "lab_map.yaml"
```

변경 후 새 터미널에서 공통 준비 명령을 다시 실행해 수정 사항을 빌드 환경에 반영합니다.

## 7. Nav2 실행

다음을 먼저 확인합니다.

- Scout 및 LiDAR 통합 bringup 터미널이 실행 중인지
- Velodyne PointCloud 변환 터미널이 실행 중인지
- 사용할 `.pgm` 및 `.yaml` 지도 파일이 모두 존재하는지
- `nav2.launch.py`의 `map_file`이 사용할 지도 YAML 이름과 일치하는지
- 이전 SLAM 및 map saver 프로세스가 종료되었는지

### 터미널 5 — AMCL Localization 및 Navigation

새 터미널에서 공통 준비 명령을 실행한 후:

```bash
ros2 launch scout_nav2 nav2.launch.py simulation:=false slam:=false localization:=amcl
```

`amcl`은 저장된 맵을 기준으로 현재 위치를 추정합니다.

## 8. RViz2에서 주행 명령

Nav2 실행과 함께 열린 RViz2에서 다음 순서로 진행합니다.

1. `2D Pose Estimate`를 선택합니다.
2. 지도 위의 실제 Scout 위치를 클릭하고, 로봇이 바라보는 방향으로 드래그합니다.
3. LaserScan과 지도가 충분히 겹치며 위치 추정이 안정되는지 확인합니다.
4. `Nav2 Goal`을 선택합니다.
5. 이동할 위치를 클릭하고 원하는 최종 방향으로 드래그합니다.
6. Scout 주변을 계속 확인하면서 저속으로 정상 주행하는지 관찰합니다.

## 종료 순서

각 터미널에서 `Ctrl+C`를 한 번 누르고, 프로세스가 정상적으로 종료될 때까지 기다립니다.

1. Nav2 또는 SLAM
2. Map saver
3. Scout 및 LiDAR 통합 bringup
4. Velodyne PointCloud 변환 노드
5. 남아 있는 점검용 터미널

강제 종료하기 전에 각 프로세스가 정상 종료될 시간을 충분히 줍니다.
