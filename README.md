# Drosophila Connectome-Constrained Odor Navigation

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Field](https://img.shields.io/badge/Field-Computational%20Neuroscience-green)](#)
[![Method](https://img.shields.io/badge/Method-Connectome--constrained%20RNN-purple)](#)
[![Status](https://img.shields.io/badge/Status-Final%20controller%20frozen-brightgreen)](#)

> Closed-loop odor-source navigation in a virtual *Drosophila* using a 532-neuron MaleCNS-derived recurrent subcircuit, modeled sensory inputs, and a learned PFL motor readout.

This repository contains a connectome-constrained embodied navigation project based on a navigation-related subset of the public MaleCNS connectome. The project asks whether recurrent dynamics constrained by connectome wiring can support odor-source localization in a stochastic 2-D plume environment.

The final selected controller reached **70/100 successes on 100 completely unseen randomized scenarios**. The system should be interpreted as a **connectome-constrained controller**, not as a whole-brain or fully biophysical fruit-fly simulation.

---

## Highlights

- Constructed a **532-neuron MaleCNS-derived navigation-related subcircuit**.
- Retained **5,274 recurrent edges** after synapse-threshold filtering.
- Implemented recurrent dynamics constrained by the connectome-derived weight matrix.
- Encoded bilateral odor input through a virtual FB5AB mapping.
- Encoded wind direction and externally supplied body heading through PFN-related inputs.
- Used **36 PFL2/PFL3 neurons** as the final motor-readout population.
- Embedded the controller in a continuous 2-D virtual fly with bilateral antennae and an intermittent filament plume.
- Evaluated the frozen v3 controller once on **100 previously unused random scenarios**.
- Compared v3 with a hybrid explicit-casting controller using matched held-out trials.
- Verified exact parity between the original validated runtime and the disk-loaded final checkpoint.
- Retained unsuccessful temporal-search extensions as negative results rather than hiding them.

---

## Graphical summary

![Final results summary](artifacts/figures/final_results_summary.svg)

The final v3 controller achieved 70% success on the held-out benchmark. The explicit casting extension reached 71%, but its matched improvement was not reliable: it rescued 11 trials while regressing 10, with exact McNemar p = 1.000.

---

## Research question

Can a navigation-related recurrent circuit derived from the *Drosophila* MaleCNS connectome support closed-loop odor-source localization when embedded in a continuous virtual environment with bilateral odor sensing and wind information?

---

## Project workflow

```text
Public MaleCNS connectome + neuron annotations
  -> navigation-related neuron-family selection
  -> synapse-thresholded signed recurrent matrix
  -> recurrent-state stabilization / scaling
  -> bilateral FB5AB odor encoding
  -> continuous PFN wind + body-heading encoding
  -> PFL2/PFL3 motor-readout training
  -> continuous embodied fly + intermittent plume
  -> controlled crosswind tests
  -> circuit perturbation / rewiring controls
  -> development-set controller comparisons
  -> frozen v3 selection
  -> 100-scenario untouched held-out evaluation
  -> checkpoint parity + full trajectory parity
  -> final checkpoint-driven runtime
```

---

## Final runtime architecture

![Final runtime architecture](artifacts/figures/final_runtime_architecture.svg)

The odor-source coordinates are used only for stopping, evaluation, and visualization. They are **not supplied to the neural controller**.

---

## Connectome-derived circuit

The final recurrent model contains navigation-related families including:

```text
FB5AB
PFNa
PFNp
PFNm
hDeltaC
FC2B
FC2C
FB5N
PFL2
PFL3
```

| Quantity | Value |
|---|---:|
| Neurons | 532 |
| Recurrent edges | 5,274 |
| PFL motor-readout neurons | 36 |
| Recurrent leak | 0.5 |
| Recurrent spectral-radius target | 0.9 |
| Forward-speed bounds | 0.0 to 0.85 |
| Angular-velocity bounds | -2.5 to 2.5 |

The connectome is used as a structural constraint on recurrent interactions. Neurotransmitter signs, sensory mappings, recurrent scaling, and several PFN conventions remain modeling assumptions rather than full biological reconstructions.

---

## Embodied virtual environment

The final environment contains:

- continuous 2-D fly position
- continuous body heading
- bilateral antenna positions
- stochastic intermittent filament plume
- continuous forward and angular motor commands
- finite arena boundaries
- randomized starting positions, odor-source positions, wind direction, and initial heading

For the final benchmark, start-to-source distance was constrained to approximately **9–14 arena units**, and the start was generated roughly downwind of the odor source. Therefore, the benchmark represents **odor-source localization from randomized downwind starting conditions**, not arbitrary waypoint navigation.

The plume is a phenomenological filament model rather than a Navier–Stokes CFD simulation.

---

## Main results

### 1. Final v3 controller generalized to unseen random scenarios

The frozen v3 controller was evaluated once on **100 completely unused random scenarios**.

| Metric | Final v3 |
|---|---:|
| Successes | 70 / 100 |
| Success rate | 70% |
| Wilson 95% CI | 60.4%–78.1% |
| Mean minimum source distance | 1.136 |
| Median minimum source distance | 0.489 |
| Mean whiff fraction | 0.648 |
| Total boundary contacts | 8 |

The 100-scenario set was kept separate from the earlier 30-scenario development set.

The frozen result table is available at `artifacts/tables/final_heldout_summary.csv`.

---

### 2. Explicit casting did not provide a reliable held-out improvement

A hybrid v6 controller added an explicit phenomenological casting behavior after odor loss. This behavioral module was outside the 532-neuron connectome-constrained circuit.

| Controller | Successes | Success rate |
|---|---:|---:|
| v3 connectome-constrained tracking | 70 / 100 | 70% |
| v6 tracking + explicit casting | 71 / 100 | 71% |

Paired outcomes:

| Outcome | Trials |
|---|---:|
| Both succeeded | 60 |
| v3 failed → v6 succeeded | 11 |
| v3 succeeded → v6 failed | 10 |
| Both failed | 19 |

The paired success-rate difference was **+1 percentage point**, with a paired bootstrap 95% CI of **-8% to +10%** and an exact McNemar p-value of **1.000**.

Because casting did not demonstrate a reliable generalization advantage and introduced an external behavioral module, **v3 was retained as the final controller**.

---

### 3. Crosswind controls supported dependence on odor information

In the controlled crosswind benchmark:

| Condition | Successes |
|---|---:|
| Intact controller | 9 / 20 |
| Bilateral contrast removed | 0 / 20 |
| Odor removed | 0 / 20 |

This supports the importance of odor information and bilateral contrast in the implemented navigation policy. However, the motor-training teacher itself contains a bilateral-contrast term, so this should **not** be interpreted as an independent biological discovery about living fly circuitry.

---

### 4. Connectome perturbation and rewiring analyses supported a role for circuit structure

Fixed-state replay analyses showed that perturbing specific connectome populations, particularly PFN-related populations, altered downstream readout features more strongly than size-matched random controls.

Degree-preserving rewiring controls also produced poorer decodability than the original connectome-derived topology.

These results support a functional contribution of the original wiring structure **within this model**, but do not establish identical causal relationships in vivo.

---

### 5. Temporal-search extensions produced informative negative results

Several attempts to improve odor-loss behavior were unsuccessful and are retained as part of the scientific record.

| Controller | Development successes | Interpretation |
|---|---:|---|
| v3 | 20 / 30 | final pure connectome-constrained tracker |
| v4 temporal memory | 7 / 30 | hidden-memory teacher did not transfer well to closed loop |
| v5.1 memory-free search | 1 / 30 | strong offline fit but poor embodied plume reacquisition |
| v6 explicit casting | 22 / 30 | hybrid behavioral extension; tested again on held-out set |
| v6.1 selective casting | 20 / 30 | selective gate did not improve development performance |

These failures illustrate an important embodied-modeling lesson: **high offline decoder accuracy does not guarantee successful closed-loop navigation**.

---

## Reproducibility

The final neural controller was frozen and reloaded from disk before the final runtime was locked.

Final checkpoint filename:

```text
final_v3_connectome_controller.joblib
```

Expected SHA256:

```text
8d6b557bb592f29100fdf8d95cb3ccd91f608516f6862e3f772491461e983acc
```

Exact parity checks showed:

- recurrent matrix parity: exact
- raw MLP/scaler parity: exact
- motor-runtime clipping parity: exact
- 500-step recurrent controller parity: exact
- full physical trajectory parity: exact for seed `851042066`
- plume snapshot parity: exact

The official runtime is checkpoint-driven rather than dependent on the original training objects.

---

## Repository structure

```text
drosophila-connectome-odor-navigation/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ src/
│  ├─ final_runtime.py
│  ├─ verify_checkpoint.py
│  ├─ plot_final_results.py
│  └─ README.md
├─ notebooks/
│  ├─ connectome_odor_navigation_final.ipynb
│  └─ README.md
├─ artifacts/
│  ├─ figures/
│  │  ├─ final_results_summary.svg
│  │  ├─ final_runtime_architecture.svg
│  │  └─ README.md
│  ├─ tables/
│  │  ├─ final_heldout_summary.csv
│  │  ├─ final_paired_outcomes.csv
│  │  ├─ crosswind_control_summary.csv
│  │  ├─ development_controller_summary.csv
│  │  └─ README.md
│  ├─ checkpoints/
│  │  └─ README.md
│  └─ manifests/
│     └─ final_runtime_manifest.json
├─ docs/
│  ├─ final_research_summary.md
│  ├─ project_summary_ko.md
│  └─ modeling_conventions.md
└─ data/
   └─ README.md
```

Raw MaleCNS connectome files are not redistributed through this repository. `data/README.md` documents the expected external inputs.

---

## Data sources

The project uses public MaleCNS connectome data and public neuron annotations.

Required local inputs for rebuilding the connectome stage include the MaleCNS connectivity Feather file and the corresponding neuron annotation table. Raw source files should be downloaded from their original public source rather than copied into this repository.

---

## How to reproduce

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify the frozen checkpoint

Place the validated checkpoint at:

```text
artifacts/checkpoints/final_v3_connectome_controller.joblib
```

Then run:

```bash
python src/verify_checkpoint.py
```

### 3. Run a deterministic final trial

```bash
python src/final_runtime.py --seed 851042066
```

A different integer seed generates a new randomized start/source/wind scenario under the same frozen runtime.

### 4. Recreate the held-out summary plot

```bash
python src/plot_final_results.py
```

This script visualizes the frozen result tables and does not re-tune the controller.

### 5. Open the final summary notebook

```text
notebooks/connectome_odor_navigation_final.ipynb
```

---

## Documentation

| Document | Description |
|---|---|
| `docs/final_research_summary.md` | Canonical English research summary |
| `docs/project_summary_ko.md` | Korean project summary |
| `docs/modeling_conventions.md` | Biological/modeling assumptions and claim boundaries |
| `artifacts/manifests/final_runtime_manifest.json` | Frozen runtime metadata and exact checkpoint hash |
| `artifacts/tables/` | Final held-out, control, and development result tables |

---

## Interpretation

The project supports the following conclusion:

> A 532-neuron MaleCNS-derived navigation-related subcircuit, combined with modeled sensory encoding and a learned PFL motor readout, can support closed-loop odor-source localization in a stochastic virtual plume environment, reaching 70% success on 100 previously unseen randomized scenarios.

The main value of the project is not only the final success rate, but the separation between connectome-constrained recurrent dynamics, modeled sensory interfaces, a learned motor readout, embodied closed-loop testing, perturbation controls, rewiring controls, failed extensions, and final held-out validation.

---

## Limitations

- This is a **532-neuron navigation-related subcircuit**, not the complete fly CNS or brain.
- Acetylcholine was modeled as excitatory and glutamate as inhibitory as a simplified sign convention.
- Connectome edges below the selected synapse threshold were removed.
- The recurrent weight matrix was spectrally rescaled for dynamical stability.
- PFN phase information and wind-side preferences are partly inferred or model-defined.
- Bilateral odor is virtually mapped onto the FB5AB pair; this is not claimed as established antenna-to-FB5AB anatomy.
- Body heading is supplied externally rather than generated by a reconstructed E-PG compass circuit.
- The PFL motor readout is learned from a designed local plume-tracking teacher.
- The plume is a stochastic filament model rather than full computational fluid dynamics.
- The random benchmark tests odor-source localization from approximately downwind initial conditions rather than arbitrary-target navigation.
- Perturbation and rewiring effects are model-level results and do not prove identical biological causality in vivo.

---

## Project status

The controller, held-out benchmark, checkpoint definition, and runtime parity tests are frozen. Further tuning on the existing development or held-out sets is intentionally stopped.

The GitHub core release is organized independently of the later companion Kaggle release; public Kaggle links will be added only after the Kaggle dataset and notebook are finalized.
