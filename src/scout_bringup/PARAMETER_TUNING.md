# Scout 실기 SLAM·Localization·Nav2 튜닝 가이드

[워크스페이스 README로 돌아가기](../../README.md)

Scout + UR3e + Velodyne VLP-16 실기 환경의 현재 설정값과 안전한 튜닝 순서를
정리한 문서입니다. 시뮬레이션이 아니라
`scout_bringup system.launch.py`로 실행하는 실기 구성이 기준입니다.

> 튜닝은 잘못된 센서·TF 문제를 파라미터로 숨기는 작업이 아닙니다. 센서, TF,
> odometry가 정상임을 확인한 뒤 한 번에 한 항목만 변경합니다.

## 1. Active Configuration

### 실행 진입점

~~~bash
# Mapping
ros2 launch scout_bringup system.launch.py mode:=mapping

# 저장 지도 Navigation
ros2 launch scout_bringup system.launch.py mode:=navigation
~~~

두 모드가 실제로 읽는 파일은 다음과 같습니다.

| 영역 | 설정 파일 |
|---|---|
| Velodyne UDP driver | `config/velodyne_driver.yaml` |
| Packet → PointCloud2 | `config/velodyne_transform.yaml` |
| PointCloud2 → LaserScan | `config/pointcloud_to_laserscan.yaml` |
| Mapping | `config/slam_toolbox.yaml` |
| AMCL·Costmap·Planner·Controller | `../scout_nav2/scout_nav2/params/scout_amcl.yaml` |

`scout_amcl.yaml` 아래에도 별도의 `slam_toolbox` 블록이 남아 있지만 현재
`scout_bringup mode:=mapping`은 `config/slam_toolbox.yaml`을 사용합니다.
튜닝 대상 파일을 혼동하지 않습니다.

### 현재 실기 navigation 구성

~~~text
VLP-16
├─ /velodyne_points → Local Costmap VoxelLayer
└─ /scan
   ├─ SLAM Toolbox 또는 AMCL
   └─ Collision Monitor

Global Costmap → SmacPlannerHybrid → Global Path
Local Costmap + Global Path → MPPI → /cmd_vel_nav
→ Velocity Smoother → /cmd_vel_smoothed
→ Collision Monitor → /cmd_vel → scout_base
~~~

현재 등록된 Controller는 MPPI 하나입니다. DWB와 자동 전환하는 구성이 아닙니다.

## 2. Tuning Rules

1. 기존 YAML을 별도 이름으로 보관합니다.
2. 같은 장소, 같은 출발 pose, 비슷한 속도로 비교합니다.
3. 한 번에 한 파라미터 또는 서로 강하게 연결된 한 묶음만 바꿉니다.
4. YAML 변경 후 관련 launch를 재시작합니다.
5. 평균뿐 아니라 최악의 흔들림, 정지거리와 CPU 사용량을 기록합니다.
6. 실기 속도·충돌 관련 값은 넓은 공간에서 낮은 값부터 시험합니다.

권장 튜닝 순서:

~~~text
Sensor data
→ TF
→ Odometry
→ SLAM / AMCL
→ Footprint
→ Costmap marking·clearing
→ Planner
→ MPPI
→ Velocity Smoother
→ Collision Monitor
~~~

앞 단계가 틀리면 뒤 단계의 critic weight를 바꿔도 안정적으로 해결되지 않습니다.

## 3. Velodyne and LaserScan

### 현재 센서 값

| 구분 | 파라미터 | 현재값 |
|---|---|---:|
| Driver | `model` | `VLP16` |
| Driver | `rpm` | `600` |
| PointCloud | `min_range` | `0.9 m` |
| PointCloud | `max_range` | `100.0 m` |
| LaserScan | `target_frame` | `base_link` |
| LaserScan | `min_height` | `-0.15 m` |
| LaserScan | `max_height` | `0.75 m` |
| LaserScan | `range_min` | `0.3 m` |
| LaserScan | `range_max` | `20.0 m` |
| LaserScan | `scan_time` | `0.1 s` |

PointCloud 변환이 `0.9 m`보다 가까운 점을 제거하므로 LaserScan의
`range_min: 0.3`만 낮춰도 0.9 m 안쪽 장애물이 새로 보이지 않습니다.

### 먼저 확인할 것

~~~bash
ros2 topic hz /velodyne_packets
ros2 topic hz /velodyne_points
ros2 topic hz /scan
ros2 topic echo /scan --once --field range_min
ros2 run tf2_ros tf2_echo base_link velodyne_link
~~~

RViz에서 다음을 확인합니다.

- 바닥 점이 scan 원으로 계속 나타나지 않는가?
- Scout 본체나 UR3e가 자기 장애물로 보이지 않는가?
- 실제 벽과 point cloud가 고정 TF에 맞게 겹치는가?
- 로봇을 정지했을 때 점군이 흔들리거나 회전하지 않는가?

### 높이와 거리 조정

- 바닥이 포함됨: `min_height`를 조금 높입니다.
- 테이블·박스가 빠짐: `max_height`를 높입니다.
- UR3e나 장비가 포함됨: 높이 범위보다 URDF 장착 TF와 self-filter 필요성을 먼저
  확인합니다.
- 근거리 노이즈가 많음: `range_min` 또는 PointCloud `min_range`를 높입니다.
- 먼 거리 반사가 맵을 망침: `range_max`와 SLAM `max_laser_range`를 함께
  줄입니다.

## 4. TF and Odometry

Mapping과 navigation의 TF 소유자는 다음과 같습니다.

| TF | Mapping | Navigation |
|---|---|---|
| `map → odom` | SLAM Toolbox | AMCL |
| `odom → base_link` | `scout_base` | `scout_base` |
| `base_link → velodyne_link` | `robot_state_publisher` | `robot_state_publisher` |

~~~bash
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link velodyne_link
ros2 topic hz /odometry
~~~

- 직진했는데 yaw가 크게 변함: wheel odometry와 좌우 wheel 상태를 확인합니다.
- 제자리 회전 후 위치가 크게 이동함: odometry scale, 미끄러짐과 base TF를
  확인합니다.
- 센서가 로봇과 따로 움직임: 고정 TF 또는 timestamp 문제입니다.
- SLAM과 AMCL을 동시에 실행하지 않습니다. 둘 다 `map → odom`을 발행할 수
  있습니다.

## 5. SLAM Toolbox

사용 파일은 `config/slam_toolbox.yaml`입니다.

| 파라미터 | 현재값 | 낮출 때 | 높일 때 |
|---|---:|---|---|
| `resolution` | `0.05 m` | 정밀도·메모리·CPU 증가 | 지도는 가벼워지지만 거칠어짐 |
| `max_laser_range` | `20.0 m` | 먼 반사 제거 | 넓은 공간의 먼 벽 활용 |
| `minimum_time_interval` | `0.2 s` | scan 처리 증가 | CPU 부하 감소 |
| `minimum_travel_distance` | `0.2 m` | scan node가 촘촘해짐 | 중복 처리 감소 |
| `minimum_travel_heading` | `0.2 rad` | 회전 중 자주 갱신 | 중복 처리 감소 |
| `map_update_interval` | `5.0 s` | RViz 지도 갱신이 빨라짐 | 표시 부하 감소 |
| `loop_search_maximum_distance` | `3.0 m` | 잘못된 후보 감소 | 더 먼 loop 후보 탐색 |

### 증상별 순서

#### 지도가 로봇보다 늦게 따라옴

1. `/scan`과 TF timestamp를 확인합니다.
2. `minimum_time_interval`을 `0.1~0.15`로 시험합니다.
3. 필요하면 `map_update_interval`을 `1.0~2.0`으로 줄입니다.

`map_update_interval`은 RViz에 map을 발행하는 주기와 관련되므로 scan matching
자체의 지연과 구분합니다.

#### CPU 또는 scan queue가 밀림

- `minimum_time_interval: 0.2~0.3`
- `minimum_travel_distance: 0.2~0.3`
- `minimum_travel_heading` 증가

#### 재방문해도 loop closure가 안 됨

1. odometry와 LiDAR TF를 먼저 확인합니다.
2. 같은 장소를 반대 방향에서도 천천히 다시 관측합니다.
3. `loop_search_maximum_distance`를 조금씩 늘립니다.

#### 서로 다른 통로가 잘못 합쳐짐

`loop_match_minimum_response_coarse`와
`loop_match_minimum_response_fine`을 조금씩 높여 조건을 엄격하게 만듭니다.

`solver_plugin`, Ceres와 correlation search 값은 sensor/TF/odometry가 정상인데도
문제가 남을 때 마지막에 조정합니다.

## 6. AMCL

사용 파일은 `scout_amcl.yaml`의 `amcl` 블록입니다.

| 파라미터 | 현재값 | 조정 기준 |
|---|---:|---|
| `update_min_d` | `0.05 m` | 증가하면 위치 갱신 횟수와 CPU 감소 |
| `update_min_a` | `0.05 rad` | 증가하면 회전 갱신 횟수와 CPU 감소 |
| `min_particles` | `500` | particle 수 하한 |
| `max_particles` | `2000` | 증가하면 복구 가능성과 CPU 사용량 증가 |
| `max_beams` | `180` | 증가하면 scan 정보와 CPU 사용량 증가 |
| `laser_max_range` | `20.0 m` | `/scan` 및 SLAM 범위와 맞춤 |
| `laser_likelihood_max_dist` | `2.0 m` | map obstacle 대응 거리 |
| `do_beamskip` | `false` | 이동 장애물이 많을 때 시험 |
| `set_initial_pose` | `true` | 설정된 초기 pose 사용 |

### 증상별 순서

- particle이 수렴하지 않음:
  1. `2D Pose Estimate`, map/scan 정합과 TF를 확인합니다.
  2. `max_particles`를 `2500~3000`으로 시험합니다.
  3. 필요하면 `max_beams`를 늘립니다.
- CPU가 높음:
  - `max_particles`, `max_beams`을 줄이거나 update threshold를 높입니다.
- odometry 미끄러짐이 큼:
  - `alpha1~alpha4`를 `0.2`에서 조금씩 높여 odometry noise를 크게 모델링합니다.
- 사람 등 이동 장애물이 많음:
  - `do_beamskip: true`를 별도 시험합니다.

로봇이 map 원점에서 시작하지 않으면 YAML pose를 매번 고치기보다 RViz의
`2D Pose Estimate`로 실제 pose를 지정합니다.

## 7. Costmaps

### Footprint

현재 local/global footprint는 동일합니다.

~~~yaml
footprint: "[ [0.45, 0.35], [0.45, -0.35], [-0.45, -0.35], [-0.45, 0.35] ]"
footprint_padding: 0.02
~~~

돌출된 센서·arm을 포함한 실제 외곽을 측정합니다. footprint가 너무 작으면 충돌
위험이 있고 너무 크면 좁은 통로의 경로 생성과 회피가 불가능해질 수 있습니다.

### Local Costmap

로봇 중심 `8 × 8 m` rolling window이며 `/velodyne_points`를 사용합니다.

| 파라미터 | 현재값 | 의미 |
|---|---:|---|
| `update_frequency` | `5.0 Hz` | sensor 반영 주기 |
| `publish_frequency` | `5.0 Hz` | RViz 표시 주기 |
| `resolution` | `0.05 m` | 한 cell의 크기 |
| `observation_persistence` | `0.0 s` | 이전 관측을 누적하지 않음 |
| `expected_update_rate` | `0.2 s` | Hz가 아닌 허용 갱신 간격 |
| `min/max_obstacle_height` | `0.15 / 1.0 m` | obstacle로 사용할 높이 |
| `obstacle_max_range` | `12.0 m` | marking 최대 거리 |
| `raytrace_max_range` | `15.0 m` | clearing 최대 거리 |
| `inflation_radius` | `0.5 m` | obstacle 주변 비용 반경 |
| `cost_scaling_factor` | `2.0` | 증가하면 비용이 더 빠르게 감소 |

`expected_update_rate: 0.2`는 0.2 Hz가 아니라 0.2초입니다.

### Global Costmap

현재 plugin은 `StaticLayer + DenoiseLayer + InflationLayer`입니다. 실시간
`/scan` 또는 `/velodyne_points`를 받는 ObstacleLayer가 없습니다. 따라서
동적 장애물 회피는 주로 Local Costmap과 MPPI가 담당합니다.

### 장애물 잔상 또는 clearing 문제

1. RViz에서 raw point cloud가 실제로 사라지는지 봅니다.
2. sensor timestamp와 TF를 확인합니다.
3. `raytrace_max_range > obstacle_max_range`인지 확인합니다.
4. 그다음 persistence, height와 range를 조정합니다.

### Inflation 조정

- `inflation_radius` 증가: 장애물 주변 비용 영역이 넓어집니다.
- `inflation_radius` 감소: 좁은 통로는 쉬워지지만 clearance가 줄어듭니다.
- `cost_scaling_factor` 증가: obstacle 밖의 비용이 더 빠르게 낮아집니다.

좁은 통로 문제는 inflation만 줄이기 전에 footprint, map resolution과 장애물
marking이 정확한지 확인합니다.

## 8. Global Planner and Smoother

현재 Planner는 `nav2_smac_planner/SmacPlannerHybrid`입니다.

| 파라미터 | 현재값 | 조정 기준 |
|---|---:|---|
| `motion_model_for_search` | `REEDS_SHEPP` | 전진·후진 motion을 허용 |
| `angle_quantization_bins` | `64` | 증가하면 방향 표현과 계산량 증가 |
| `minimum_turning_radius` | `0.2 m` | 증가하면 완만하지만 좁은 회전이 어려움 |
| `reverse_penalty` | `1.2` | 증가하면 후진을 덜 선택 |
| `non_straight_penalty` | `1.2` | 증가하면 곡선 motion 비용 증가 |
| `cost_penalty` | `2.0` | 증가하면 높은 cost 영역을 더 회피 |
| `tolerance` | `0.25 m` | exact goal 실패 시 허용 거리 |
| `max_planning_time` | `10.0 s` | planning 시간 상한 |

Scout는 제자리 회전 가능한 DiffDrive이지만 Planner에는 Reeds-Shepp 모델이
선택되어 있습니다. 현재 설정값이라는 사실과 실제 로봇에 최적인지는 구분해서
주행 결과를 평가합니다.

경로가 없을 때는 다음 순서로 확인합니다.

1. start/goal이 lethal 또는 unknown cell인지 확인
2. footprint와 inflation 확인
3. TF와 Global Costmap 확인
4. 그다음 turning radius, tolerance와 penalty 조정

Planner 뒤의 `ConstrainedSmoother`도 경로를 변경합니다. Planner 결과와 최종
smoothed path를 구분해 확인합니다.

## 9. MPPI Controller

현재 `FollowPath`는 `nav2_mppi_controller::MPPIController`입니다.

### Prediction and sampling

| 파라미터 | 현재값 | 조정 기준 |
|---|---:|---|
| `controller_frequency` | `10 Hz` | 실제 command 갱신 목표 |
| `time_steps` | `50` | 미래 sequence step 수 |
| `model_dt` | `0.1 s` | 한 step 시간 |
| `batch_size` | `1000` | cycle당 sample 수 |
| `iteration_count` | `1` | cycle당 update 횟수 |
| `temperature` | `0.3` | sample weight 집중도 |
| `vx_std` | `0.2` | 선속도 exploration 폭 |
| `wz_std` | `0.4` | 각속도 exploration 폭 |
| `prune_distance` | `1.5 m` | 뒤쪽 path 정리 거리 |
| `motion_model` | `DiffDrive` | Scout motion model |

현재 prediction horizon:

~~~text
time_steps × model_dt = 50 × 0.1 = 5.0초
~~~

`batch_size`나 `time_steps`를 늘리기 전에 controller가 10 Hz 주기를 실제로
유지하는지 확인합니다. 계산이 늦으면 미래를 더 많이 보는 대신 오래된 command가
나갈 수 있습니다.

### Velocity limits

~~~yaml
# MPPI
vx_max: 0.5
vx_min: -0.3
vy_max: 0.0
wz_max: 0.5

# Velocity Smoother
max_velocity: [0.5, 0.0, 0.5]
min_velocity: [-0.3, 0.0, -0.5]
~~~

MPPI와 Velocity Smoother의 속도 제한을 서로 맞춥니다. `vy_max: 0.0`은
횡이동하지 않는 Scout DiffDrive 구성입니다.

### Active critics

| Critic | 현재 weight | 역할 |
|---|---:|---|
| `ConstraintCritic` | `4.0` | 운동학·속도 제약 |
| `ObstaclesCritic` | `repulsion 1.4` | obstacle 회피와 collision |
| `GoalCritic` | `20.0` | goal 위치 접근 |
| `GoalAngleCritic` | `5.0` | goal 최종 방향 |
| `PathAlignCritic` | `20.0` | Global Path 정렬 |
| `PathFollowCritic` | `4.0` | path 앞쪽으로 진행 |
| `PathAngleCritic` | `4.0` | path와 heading 차이 |
| `TwirlingCritic` | `10.0` | 불필요한 회전 억제 |

`PreferForwardCritic`은 설정 블록이 있어도 critics 목록에서 제외되고
`enabled: false`이므로 현재 비활성입니다.

### 증상별 확인

- path를 따라가지 않음:
  - TF, transformed plan과 Local Costmap을 먼저 확인
  - 그다음 PathFollow/PathAlign/PathAngle weight를 한 개씩 조정
- 장애물에 너무 가까움:
  - footprint, inflation과 obstacle marking 확인
  - 그다음 ObstaclesCritic의 repulsion/collision margin 조정
- 회전만 반복함:
  - odometry yaw, goal/path orientation 확인
  - Twirling, PathAngle과 GoalAngle의 균형 확인
- command가 끊김:
  - controller loop miss와 CPU 확인
  - `batch_size`, `time_steps`를 줄여 비교

## 10. Velocity Smoother

현재 설정:

| 파라미터 | 현재값 |
|---|---:|
| `smoothing_frequency` | `20 Hz` |
| `feedback` | `OPEN_LOOP` |
| `max_accel` | `[2.5, 0.0, 2.0]` |
| `max_decel` | `[-2.5, 0.0, -2.0]` |
| `velocity_timeout` | `1.0 s` |

실기 첫 시험에서는 속도뿐 아니라 가속도와 감속도의 절댓값도 낮게 시작합니다.

- 출발·정지가 거침: accel/decel 절댓값을 낮춥니다.
- controller 반응이 지나치게 둔함: smoother 제한이 MPPI보다 과도하게 낮지 않은지
  확인합니다.
- OPEN_LOOP은 출력 command를 기반으로 smoothing합니다. 실제 속도 피드백 기반
  동작과 혼동하지 않습니다.

## 11. Collision Monitor

명령 흐름:

~~~text
/cmd_vel_nav
→ Velocity Smoother
→ /cmd_vel_smoothed
→ Collision Monitor
→ /cmd_vel
→ scout_base
~~~

현재 zone:

| Zone | 범위 | 동작 | 상태 |
|---|---|---|---|
| `FootprintStop` | 약 `±0.48 × ±0.38 m` | 정지 | 활성 |
| `FootprintSlowdown` | 약 `±0.65 × ±0.55 m` | 50% 감속 | 활성 |
| `FootprintApproach` | 약 `±0.70 × ±0.60 m` | TTC 기반 접근 | 비활성 |

입력은 `/scan`이며 PointCloud source는 비활성입니다.

### 중요: Humble 파라미터 이름 확인

현재 YAML zone에는 `min_points`가 적혀 있지만, 이 워크스페이스에서 확인한
로컬 Humble `nav2_collision_monitor` 예제와 header는 `max_points`를
사용합니다. 버전이 맞지 않으면 의도한 point threshold가 적용되지 않을 수
있습니다.

실기 안전 시험 전에 반드시 확인합니다.

~~~bash
ros2 param dump /collision_monitor
ros2 topic echo /collision_monitor_state
ros2 topic echo /polygon_stop
ros2 topic echo /polygon_slowdown
~~~

설치된 Humble API가 `max_points`를 요구한다면 YAML도 그 이름으로 수정하고
정지 시험을 다시 해야 합니다. 문서만 믿고 안전 기능이 적용됐다고 가정하지
않습니다.

### VLP-16 근거리 사각

PointCloud 변환의 `min_range`가 `0.9 m`인데 Stop/Slowdown zone은 대부분 그
안쪽입니다. VLP-16만으로 해당 근거리 zone의 장애물 검출을 완전히 보장할 수
없습니다.

0.9 m 안쪽 안전 검출이 필요하면 RealSense depth, 초음파, bumper 같은 근거리
sensor를 추가해야 합니다. 물리적인 sensor 사각은 Costmap이나 Collision Monitor
파라미터만으로 해결되지 않습니다.

## 12. Symptom Checklist

| 증상 | 먼저 확인 | 그다음 튜닝 |
|---|---|---|
| 지도 이중 벽 | LiDAR TF, odometry, 속도 | SLAM scan interval/loop 조건 |
| AMCL 튐 | initial pose, map/scan 정합 | particles, beams, odom alpha |
| 경로 생성 실패 | footprint, Global Costmap, goal cell | turning radius, tolerance |
| 장애물 잔상 | raw point, TF, clearing ray | persistence, range, height |
| 장애물에 너무 가까움 | footprint와 marking | inflation, ObstaclesCritic |
| 제자리 회전 반복 | yaw TF, path orientation | PathAngle, Twirling, goal tolerance |
| command 끊김 | CPU, controller loop | MPPI batch/horizon |
| 급출발·급정지 | 최종 `/cmd_vel` 비교 | smoother accel/decel |
| 근거리 정지 실패 | VLP-16 min range, threshold 이름 | 근거리 sensor 추가 |

## 13. Verification

### 센서와 TF

~~~bash
ros2 topic hz /velodyne_points
ros2 topic hz /scan
ros2 topic hz /odometry
ros2 run tf2_ros tf2_echo base_link velodyne_link
ros2 run tf2_ros tf2_echo odom base_link
~~~

### Nav2와 velocity pipeline

~~~bash
ros2 param get /planner_server planner_plugins
ros2 param get /controller_server controller_plugins
ros2 topic hz /local_costmap/costmap
ros2 topic echo /cmd_vel_nav
ros2 topic echo /cmd_vel_smoothed
ros2 topic echo /cmd_vel
ros2 topic echo /collision_monitor_state
~~~

세 velocity topic을 비교하면 MPPI, smoother와 Collision Monitor 중 어느 단계에서
명령이 변했는지 확인할 수 있습니다.

## 14. Tuning Log

| 날짜 | 장소·조건 | 파라미터 | 변경 전 | 변경 후 | 결과 |
|---|---|---|---:|---:|---|
| YYYY-MM-DD | 예: 직선 5 m, 마른 바닥 | `inflation_radius` | 0.5 | 0.55 | 최소 clearance |

기록에는 다음을 함께 남깁니다.

- map과 출발/goal pose
- 적재 상태와 arm 자세
- 평균·최대 속도
- CPU 사용률과 controller loop 유지 여부
- 최소 장애물 거리
- 성공/실패뿐 아니라 진동, 정지거리와 재현 횟수
