# 초파리 커넥톰 기반 냄새원 탐색 프로젝트 요약

## 연구 목표

이 프로젝트는 공개 MaleCNS 커넥톰에서 냄새원 탐색과 관련된 뉴런 집단을 추려, 실제 연결 구조를 제약조건으로 사용하는 recurrent controller를 만들고, 이를 2차원 가상 초파리에 탑재해 냄새원을 찾아가도록 할 수 있는지 확인한 연구이다.

최종 시스템은 **532개 뉴런으로 구성된 MaleCNS-derived navigation-related subcircuit**을 사용하며, 전체 초파리 뇌나 CNS를 그대로 재현한 시뮬레이션은 아니다.

## 최종 모델

최종 controller는 v3 버전으로 고정하였다.

- 532개 recurrent neuron
- 5,274개 recurrent edge
- bilateral odor input을 virtual FB5AB pair에 매핑
- wind direction과 externally supplied body heading을 PFN input으로 사용
- PFL2 + PFL3 총 36개 뉴런을 motor readout으로 사용
- frozen nonlinear MLP로 forward speed와 angular velocity 출력

목표 좌표는 controller에 직접 제공하지 않고, 성공 판정과 거리 계산에만 사용하였다.

## 가상 환경

가상 환경은 다음 요소로 구성된다.

- continuous 2-D position
- continuous heading
- bilateral antennae
- stochastic intermittent filament plume
- continuous forward/angular motor command
- finite arena boundary

최종 random benchmark는 start와 odor source를 무작위로 만들되, 초기 거리는 약 9–14 arena unit으로 제한하고 start가 대체로 odor source의 downwind 쪽에 위치하도록 생성하였다. 따라서 이는 임의 waypoint navigation이 아니라 **무작위 downwind 조건에서의 odor-source localization** 문제이다.

## 최종 held-out 결과

완전히 새로 생성한 100개 scenario에서 최종 v3 controller를 한 번 평가하였다.

| 지표 | 값 |
|---|---:|
| 성공 | 70 / 100 |
| 성공률 | 70% |
| Wilson 95% CI | 60.4%–78.1% |
| 평균 최소거리 | 1.136 |
| 중앙값 최소거리 | 0.489 |
| 평균 whiff fraction | 0.648 |
| 전체 boundary contact | 8 |

이 100개 scenario는 이전 30개 development scenario와 분리하였다.

## v6 casting 비교

odor loss 이후 외부 behavioral casting module을 추가한 v6와도 최종 비교하였다.

- v3: 70 / 100
- v6: 71 / 100
- v3 fail → v6 success: 11
- v3 success → v6 fail: 10
- paired bootstrap 95% CI: -8% ~ +10%
- McNemar p = 1.000

따라서 casting이 held-out 성능을 안정적으로 개선했다고 보기 어려웠고, 외부 behavioral module이 필요 없는 v3를 최종 controller로 선택하였다.

## 중요한 음성 결과

v4와 v5는 최종 모델보다 성능이 낮았다.

- v4 temporal-memory approach: 7 / 30
- v5.1 memory-free search: 1 / 30
- 같은 development set에서 v3: 20 / 30

이 결과는 offline decoder 성능이 높아도 embodied closed-loop 환경에서 반드시 좋은 navigation으로 이어지지는 않는다는 점을 보여준다.

## 재현성

최종 controller를 `final_v3_connectome_controller.joblib`로 저장하고 runtime parity를 검증하였다.

SHA256:

```text
8d6b557bb592f29100fdf8d95cb3ccd91f608516f6862e3f772491461e983acc
```

검증 결과:

- recurrent matrix parity: exact
- raw model parity: exact
- motor clipping parity: exact
- 500-step neural runtime parity: exact
- full physical trajectory parity: exact
- plume snapshot parity: exact

## 해석 범위

이 프로젝트는 다음을 주장하지 않는다.

- 전체 초파리 뇌 시뮬레이션
- receptor-level neurotransmitter dynamics의 정확한 재현
- 실제 antenna-to-FB5AB 직접 연결의 실험적 입증
- 내부 E-PG compass reconstruction
- biologically proven PFN phase tuning
- biologically derived PFL motor decoder
- 임의 목표 좌표로의 일반 navigation
- Navier–Stokes 수준의 odor transport
- 모델 perturbation 결과가 생체에서도 동일하게 나타난다는 증명

따라서 가장 정확한 표현은 **MaleCNS connectome-derived 532-neuron navigation-related subcircuit을 사용한 connectome-constrained odor-navigation controller**이다.
