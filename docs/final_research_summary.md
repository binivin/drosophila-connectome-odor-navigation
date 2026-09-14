# Final Research Summary

## Objective

This project tested whether a navigation-related subcircuit derived from the male *Drosophila* CNS connectome could support closed-loop odor-source localization when embedded in a continuous virtual fly with bilateral odor sensing and wind information.

The final system is a **connectome-constrained controller**, not a whole-brain simulation.

## Final circuit

The frozen v3 controller contains:

- 532 MaleCNS-derived neurons
- 5,274 recurrent connections after thresholding
- bilateral odor input mapped virtually to FB5AB
- PFN-related wind and body-heading input
- 36 PFL2/PFL3 motor-readout neurons
- a frozen nonlinear MLP producing forward and angular motor commands

The recurrent matrix was spectrally rescaled for stable dynamics. Body heading is supplied externally. Goal/source coordinates are never provided to the controller.

## Embodied environment

The final environment contains a continuous 2-D fly, bilateral antennae, an intermittent stochastic filament plume, continuous forward/angular motion, and finite arena boundaries.

The final random benchmark samples randomized starts and odor sources with an initial distance of roughly 9–14 arena units and places the start approximately downwind of the odor source. The benchmark therefore tests odor-source localization from randomized downwind conditions rather than arbitrary waypoint navigation.

## Final held-out performance

The frozen v3 controller was evaluated once on 100 previously unused random scenarios.

| Metric | Value |
|---|---:|
| Successes | 70 / 100 |
| Success rate | 70% |
| Wilson 95% CI | 60.4%–78.1% |
| Mean minimum source distance | 1.136 |
| Median minimum source distance | 0.489 |
| Mean whiff fraction | 0.648 |
| Boundary contacts | 8 |

The earlier 30-scenario set was treated as development data and was not reused as the final held-out benchmark.

## Explicit casting comparison

A hybrid v6 controller added an explicit odor-loss casting rule outside the connectome-constrained circuit.

| Controller | Successes |
|---|---:|
| v3 | 70 / 100 |
| v6 | 71 / 100 |

Paired outcomes were 60 both-success, 11 v3-fail/v6-success, 10 v3-success/v6-fail, and 19 both-fail. The paired success-rate difference was +1 percentage point with a bootstrap 95% CI of -8% to +10% and exact McNemar p = 1.000.

Because the hybrid extension did not show a reliable generalization advantage and required an external behavioral module, v3 was retained as the final controller.

## Crosswind controls

In a controlled crosswind benchmark:

- intact: 9 / 20 successes
- bilateral odor contrast removed: 0 / 20
- odor removed: 0 / 20

This supports dependence on odor information and bilateral contrast within the implemented policy. It should not be treated as an independent biological discovery because the motor-training teacher itself includes a bilateral-contrast term.

## Connectome perturbation and rewiring

Fixed-state replay analyses showed strong sensitivity to perturbation of specific connectome populations, particularly PFN-related populations, compared with size-matched random controls. Degree-preserving rewiring controls also reduced downstream decodability relative to the original topology.

These are model-level results and do not establish identical causal relationships in vivo.

## Negative results

Attempts to extend odor-loss behavior were retained as negative results.

- v4 temporal-memory approach: 7 / 30 successes
- v5.1 memory-free search: 1 / 30 successes
- v3 on the same development set: 20 / 30 successes

The failed extensions demonstrate that high offline decoder accuracy does not guarantee successful embodied closed-loop behavior.

## Frozen checkpoint and reproducibility

Final checkpoint:

```text
final_v3_connectome_controller.joblib
```

SHA256:

```text
8d6b557bb592f29100fdf8d95cb3ccd91f608516f6862e3f772491461e983acc
```

Validation established exact parity for:

- recurrent matrix
- raw MLP/scaler inference
- motor clipping
- 500 recurrent controller steps
- a complete physical trajectory
- plume snapshots

The final runtime is therefore checkpoint-driven rather than dependent on the original training objects.

## Supported interpretation

> A 532-neuron MaleCNS-derived navigation-related subcircuit, combined with modeled sensory encoding and a learned PFL motor readout, can support closed-loop odor-source localization in a stochastic virtual plume environment, reaching 70% success on 100 previously unseen randomized scenarios.

## Scope and limitations

The project does not demonstrate a full fly-brain simulation, exact receptor-level neurotransmitter dynamics, experimentally established antenna-to-FB5AB anatomy, an internally reconstructed compass, biologically proven PFN tuning, a biologically derived PFL motor decoder, arbitrary waypoint navigation, or fluid-dynamically exact odor transport.

See `modeling_conventions.md` for the full list of assumptions and interpretation limits.
