# Scout SLAM, Localization, Nav2 파라미터 가이드

이 문서는 Scout + UR3e + Velodyne VLP-16 실기 환경에서 파라미터의 위치와
튜닝 기준을 설명합니다. 정상 동작 중에는 여러 값을 한 번에 변경하지 말고,
한 항목씩 바꾼 뒤 같은 장소와 속도로 재시험합니다.

## 사용되는 설정 파일

| 구분 | 파일 |
|---|---|
| Velodyne 드라이버 | `config/velodyne_driver.yaml` |
| Velodyne PointCloud 변환 | `config/velodyne_transform.yaml` |
| PointCloud → LaserScan | `config/pointcloud_to_laserscan.yaml` |
| 현재 bringup의 SLAM | `config/slam_toolbox.yaml` |
| AMCL 및 Nav2 | `../scout_nav2/scout_nav2/params/scout_amcl.yaml` |

`system.launch.py mode:=mapping`은 `config/slam_toolbox.yaml`을 사용합니다.
`scout_amcl.yaml` 아래쪽에도 기존 `scout_nav2` launch 호환용 `slam_toolbox`
블록이 있지만 현재 `scout_bringup`의 mapping 튜닝 대상은 아닙니다.

## 공통 센서와 TF

SLAM, AMCL, collision monitor는 `/scan`을 사용하고 local costmap은
`/velodyne_points`를 사용합니다. 다음 순서로 먼저 확인합니다.

1. URDF의 `base_link -> velodyne_link`가 실제 장착 위치와 일치하는지 확인
2. `/velodyne_points`가 약 10 Hz로 들어오는지 확인
3. `/scan`이 약 10 Hz로 들어오는지 확인
4. RViz에서 바닥과 로봇 본체가 `/scan`에 포함되는지 확인

### `pointcloud_to_laserscan.yaml`

| 파라미터 | 현재값 | 조정 기준 |
|---|---:|---|
| `target_frame` | `base_link` | URDF와 일치해야 함 |
| `min_height` | -0.15 m | 바닥이 찍히면 높임 |
| `max_height` | 0.75 m | 로봇 팔이나 상부 구조물이 찍히면 낮춤 |
| `range_min` | 0.3 m | 근거리 노이즈가 많으면 높임 |
| `range_max` | 20.0 m | 일반 실내에서는 15~20 m 권장 |
| `scan_time` | 0.1 s | VLP-16 600 RPM의 약 10 Hz와 일치 |

Velodyne PointCloud 변환의 `min_range`는 현재 0.9 m입니다. 따라서
`range_min`을 0.3 m로 설정해도 VLP-16 PointCloud의 실질적인 근거리 한계는
약 0.9 m입니다.

## SLAM

사용 파일은 `config/slam_toolbox.yaml`입니다.

| 파라미터 | 현재값 | 낮출 때 | 높일 때 |
|---|---:|---|---|
| `resolution` | 0.05 m | 더 정밀하지만 메모리·CPU 증가 | 가벼워지지만 지도 정밀도 감소 |
| `max_laser_range` | 20.0 m | 먼 거리 노이즈 제거 | 넓은 공간의 먼 벽 사용 |
| `minimum_time_interval` | 0.2 s | scan 처리 증가, 반응 향상 | CPU 부하 감소 |
| `minimum_travel_distance` | 0.2 m | 더 촘촘하게 scan 추가 | 중복 scan과 CPU 감소 |
| `minimum_travel_heading` | 0.2 rad | 회전 중 더 자주 갱신 | 중복 갱신 감소 |
| `map_update_interval` | 5.0 s | RViz 지도 표시가 빨라짐 | 화면 갱신 부하 감소 |
| `loop_search_maximum_distance` | 3.0 m | 잘못된 후보 감소 | 넓은 범위에서 loop 탐색 |

### 증상별 조정

- 지도가 늦게 따라오면:
  - `minimum_time_interval: 0.1`
  - `minimum_travel_distance: 0.1`
  - `minimum_travel_heading: 0.1`
  - `map_update_interval: 1.0~2.0`
- CPU 사용량이 높거나 scan queue가 밀리면:
  - `minimum_time_interval: 0.2~0.3`
  - `minimum_travel_distance: 0.2~0.3`
- 같은 장소를 다시 방문해도 지도가 연결되지 않으면:
  - 먼저 odometry와 LiDAR TF를 확인
  - 그다음 `loop_search_maximum_distance`를 조금씩 증가
- 서로 다른 통로가 잘못 합쳐지면:
  - `loop_match_minimum_response_coarse`
  - `loop_match_minimum_response_fine`
  - 위 두 값을 조금씩 높여 loop closure 조건을 엄격하게 설정

`solver_plugin`, Ceres 설정, correlation search 설정은 TF와 odometry가 정상인데도
문제가 남을 때 마지막으로 조정합니다.

## Localization — AMCL

사용 파일은 `scout_amcl.yaml`의 `amcl` 블록입니다.

| 파라미터 | 현재값 | 조정 기준 |
|---|---:|---|
| `update_min_d` | 0.05 m | 위치 갱신 거리. CPU가 높으면 증가 |
| `update_min_a` | 0.05 rad | 회전 갱신 각도. CPU가 높으면 증가 |
| `min_particles` | 500 | 수렴 안정성과 CPU의 하한 |
| `max_particles` | 2000 | 위치가 불안정하면 증가 |
| `max_beams` | 180 | 위치가 불안정하면 증가, CPU가 높으면 감소 |
| `laser_max_range` | 20.0 m | `/scan` 및 SLAM 범위와 동일 |
| `laser_likelihood_max_dist` | 2.0 m | 지도 장애물과 scan의 대응 허용 범위 |
| `set_initial_pose` | `true` | 시작 시 맵 원점으로 자동 초기화 |

### 증상별 조정

- particle이 잘 수렴하지 않으면:
  - `max_particles: 2500~3000`
  - `max_beams: 200~240`
- AMCL CPU 사용량이 높으면:
  - `max_particles: 1000~1500`
  - `max_beams: 90~120`
- 휠 미끄러짐이 많고 odometry 신뢰도가 낮으면:
  - `alpha1`~`alpha4`를 0.2에서 0.3 정도로 조금씩 증가
- 사람이나 이동 장애물이 많은 장소에서 scan 일부가 자주 어긋나면:
  - `do_beamskip: true`를 시험

로봇이 맵 원점에서 시작하지 않으면 파라미터의 초기 자세를 임의로 바꾸기보다
RViz의 `2D Pose Estimate`로 실제 위치와 방향을 지정합니다.

## Nav2

사용 파일은 `scout_amcl.yaml`의 controller, costmap, planner,
velocity smoother, collision monitor 블록입니다.

### Footprint

현재 footprint는 다음과 같습니다.

```yaml
footprint: "[ [0.45, 0.35], [0.45, -0.35], [-0.45, -0.35], [-0.45, 0.35] ]"
```

Scout 본체뿐 아니라 돌출된 장비를 포함한 실제 외곽을 측정해 설정합니다.
너무 크면 좁은 통로를 통과하지 못하고 너무 작으면 충돌 위험이 있습니다.

### 속도 제한

MPPI와 velocity smoother의 제한은 동일하게 맞춥니다.

```yaml
# MPPI
vx_max: 0.5
vx_min: -0.3
vy_max: 0.0
wz_max: 0.5

# velocity_smoother
max_velocity: [0.5, 0.0, 0.5]
min_velocity: [-0.3, 0.0, -0.5]
```

실기 첫 시험은 더 낮은 속도에서 시작하고 안전이 확인된 뒤 조금씩 높입니다.
가감속이 너무 급하면 `max_accel`과 `max_decel`의 절댓값을 낮춥니다.

### Local costmap

| 파라미터 | 현재값 | 조정 기준 |
|---|---:|---|
| `update_frequency` | 5.0 Hz | 센서 반영 주기 |
| `publish_frequency` | 5.0 Hz | RViz 표시 주기 |
| `observation_persistence` | 0.0 s | 최신 관측만 사용하여 잔상 방지 |
| `expected_update_rate` | 0.2 s | Hz가 아니라 허용 갱신 간격 |
| `inflation_radius` | 0.5 m | 좁은 통로에서는 감소, 안전 여유는 증가 |
| `cost_scaling_factor` | 2.0 | 높이면 장애물 비용이 더 빠르게 감소 |
| `obstacle_max_range` | 12.0 m | 장애물 표시 최대 거리 |
| `raytrace_max_range` | 15.0 m | 빈 공간 clearing 최대 거리 |

`expected_update_rate`는 주파수가 아니라 초 단위입니다. VLP-16이 약 10 Hz로
들어오므로 0.1초보다 약간 여유 있는 0.2초를 사용합니다.

### Planner와 목표 허용 오차

| 파라미터 | 현재값 | 조정 기준 |
|---|---:|---|
| `tolerance` | 0.25 m | 목표 근처 경로 생성 허용 오차 |
| `minimum_turning_radius` | 0.2 m | 좁은 회전 계획이 안 되면 감소 |
| `xy_goal_tolerance` | 0.15 m | 더 정밀한 정차는 감소 |
| `yaw_goal_tolerance` | 0.15 rad | 더 정밀한 방향은 감소 |

목표 근처에서 계속 앞뒤로 움직이면 goal tolerance를 조금 높입니다. 좁은
장소에서 경로가 생성되지 않으면 footprint와 inflation radius를 먼저 확인한 뒤
planner 설정을 조정합니다.

### Collision monitor

- `FootprintStop`: 장애물이 들어오면 정지
- `FootprintSlowdown`: 장애물이 들어오면 감속
- `FootprintApproach`: 현재 비활성화
- 입력 센서: `/scan`

VLP-16 PointCloud의 근거리 한계가 약 0.9 m이므로 현재 0.48 m Stop 영역을
VLP-16만으로 완전히 보장할 수 없습니다. 0.9 m 이내 안전 검출이 필요하면
RealSense, 초음파, 범퍼 등의 근거리 센서를 추가해야 합니다. 물리적인 사각은
costmap이나 collision monitor 파라미터만으로 해결할 수 없습니다.

## 변경 후 확인

```bash
ros2 topic hz /velodyne_points
ros2 topic hz /scan
ros2 topic hz /odometry

ros2 run tf2_ros tf2_echo base_link velodyne_link
ros2 run tf2_ros tf2_echo odom base_link
```

Nav2 실행 후에는 다음을 확인합니다.

```bash
ros2 topic hz /local_costmap/costmap
ros2 topic echo /collision_monitor_state
```

튜닝 기록에는 날짜, 장소, 변경 전 값, 변경 후 값, 주행 속도, 결과를 함께
남깁니다.

| 날짜 | 장소 | 파라미터 | 변경 전 | 변경 후 | 결과 |
|---|---|---|---:|---:|---|
| YYYY-MM-DD | 테스트 장소 | 예: `inflation_radius` | 0.5 | 0.4 | 통로 통과 여부 |
