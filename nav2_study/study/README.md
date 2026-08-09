# Scout Nav2 학습 노트

이 폴더는 Scout + Velodyne + ROS 2 + Nav2의 동작을 나중에 다시 찾아보기 위한
학습 문서다. 개념 설명과 현재 워크스페이스에서 확인한 설정을 함께 기록한다.

## 추천 학습 순서

1. [전체 흐름](00_nav2_overview.md)
2. [A*와 Global Planner](01_astar_global_planner.md)
3. [DWB Controller](02_dwb_controller.md)
4. [MPPI Controller](03_mppi_controller.md)

## 현재 프로젝트를 한 줄로 요약하면

실기 기본 navigation은 다음 조합을 사용한다.

```text
Velodyne VLP-16
→ /velodyne_points와 /scan
→ AMCL + Costmap
→ SmacPlannerHybrid
→ MPPIController
→ /cmd_vel_nav
→ Velocity Smoother
→ /cmd_vel_smoothed
→ Collision Monitor
→ /cmd_vel
→ scout_base
→ ugv_sdk / CAN
```

창고 시뮬레이션은 학습·비교용으로 다른 조합을 사용한다.

```text
NavFn(use_astar: false, 즉 Dijkstra 방식) + DWBLocalPlanner
```

따라서 이 저장소에서 A*, DWB, MPPI가 모두 보인다고 해서 세 알고리즘이
`A* → DWB → MPPI` 순서로 실행되는 것은 아니다. Global Planner 하나와
Controller 하나가 해당 설정에 따라 선택된다.

## 확인 기준 파일

- 실기 진입점: [`scout_bringup/launch/navigation.launch.py`](../../src/scout_bringup/launch/navigation.launch.py)
- 실기 Nav2 설정: [`scout_amcl.yaml`](../../src/scout_nav2/scout_nav2/params/scout_amcl.yaml)
- 실기 센서 bringup: [`robot_bringup.launch.py`](../../src/scout_bringup/launch/robot_bringup.launch.py)
- 창고 시뮬레이션 설정: [`nav2_params.yaml`](../../src/scout_warehouse_sim/config/nav2_params.yaml)
- Scout 명령 수신 코드: [`scout_messenger.hpp`](../../src/scout_ros2/scout_base/include/scout_base/scout_messenger.hpp)

> 이 문서는 정적 코드와 YAML을 분석한 기록이다. 실제 실행 시에는
> `ros2 node list`, `ros2 topic list`, `ros2 param dump`로 런타임 구성을 다시
> 확인해야 한다.
