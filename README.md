# Drosophila Connectome-Constrained Odor Navigation

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Field](https://img.shields.io/badge/Field-Computational%20Neuroscience-green)](#)
[![Method](https://img.shields.io/badge/Method-Connectome--constrained%20RNN-purple)](#)
[![Status](https://img.shields.io/badge/Status-Final%20controller%20frozen-brightgreen)](#)

> Closed-loop odor-source navigation in a virtual *Drosophila* using a 532-neuron MaleCNS-derived recurrent subcircuit, modeled sensory inputs, and a learned PFL motor readout.

This repository contains a connectome-constrained embodied navigation project based on a navigation-related subset of the public MaleCNS connectome. The project asks whether a recurrent circuit whose wiring is constrained by connectome connectivity can support odor-source localization in a stochastic 2-D plume environment.

The final selected controller reached **70/100 successes on 100 completely unseen randomized scenarios**. The system should be interpreted as a **connectome-constrained controller**, not as a whole-brain or fully biophysical fruit-fly simulation.

---

## Highlights

- Constructed a **532-neuron MaleCNS-derived navigation-related subcircuit**.
- Retained **5,274 recurrent edges** after synapse-threshold filtering.
- Implemented recurrent dynamics using the connectome-derived weight matrix.
- Encoded bilateral odor input through a virtual FB5AB mapping.
- Encoded wind direction and externally supplied body heading through PFN-related inputs.
- Used **36 PFL2/PFL3 neurons** as the final motor-readout population.
- Embedded the controller in a continuous 2-D virtual fly with bilateral antennae and an intermittent filament plume.
- Evaluated the frozen v3 controller on **100 previously unused random scenarios**.
- Compared the final controller with an explicit odor-loss casting extension.
- Verified exact parity between the original validated runtime and the disk-loaded final checkpoint.
- Retained unsuccessful temporal-search extensions as negative results rather than hiding them.

---

## Research question

Can a navigation-related recurrent circuit derived from the *Drosophila* MaleCNS connectome support closed-loop odor-source localization when embedded in a continuous virtual environment with bilateral odor sensing and wind information?

---

## Final system

```text
Intermittent odor plume
  -> bilateral antenna sampling
  -> odor receptor response
  -> virtual FB5AB odor encoding

Wind direction + body heading
  -> PFN-related input encoding

Sensory inputs
  -> 532-neuron connectome-constrained recurrent circuit
  -> PFL2 + PFL3 state (36 neurons)
  -> frozen nonlinear motor readout
  -> forward speed + angular velocity
  -> continuous fly movement
  -> new antenna positions
  -> closed loop
```

The odor-source coordinates are used only for stopping and evaluation. They are **not supplied to the controller**.

---

## Connectome-derived circuit

The final recurrent model contains the following navigation-related families:

- FB5AB
- PFNa
- PFNp
- PFNm
- hDeltaC
- FC2B
- FC2C
- FB5N
- PFL2
- PFL3

Final circuit summary:

| Quantity | Value |
|---|---:|
| Neurons | 532 |
| Recurrent edges | 5,274 |
| PFL motor-readout neurons | 36 |
| Recurrent leak | 0.5 |
| Recurrent spectral-radius target | 0.9 |
| Forward-speed bounds | 0.0 to 0.85 |
| Angular-velocity bounds | -2.5 to 2.5 |

The connectome is used as a structural constraint on recurrent interactions. Neurotransmitter signs, input mappings, recurrent scaling, and several sensory conventions are simplified modeling assumptions and are documented below.

---

## Embodied virtual environment

The final environment contains:

- continuous 2-D fly position
- continuous body heading
- bilateral antenna locations
- stochastic intermittent filament plume
- continuous forward and angular motor commands
- finite arena boundaries
- randomized starting positions, source positions, wind direction, and initial heading

For the final random benchmark, start-to-source distance was constrained to approximately **9–14 arena units**, and the start was generated roughly downwind of the odor source. Therefore, this benchmark represents **odor-source localization from randomized downwind starting conditions**, not arbitrary waypoint navigation.

The plume is a phenomenological filament model rather than a Navier–Stokes CFD simulation.

---

## Main results

### 1. Final v3 controller generalized to unseen random scenarios

The final frozen v3 controller was evaluated once on **100 completely unused random scenarios**.

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

---

### 2. Explicit casting did not provide a reliable held-out improvement

A hybrid v6 controller added an explicit phenomenological casting behavior after odor loss. This behavioral module was outside the 532-neuron connectome-constrained circuit.

Final held-out comparison:

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

Because the casting extension did not demonstrate a reliable generalization advantage and introduced an external behavioral module, **v3 was retained as the final controller**.

---

### 3. Crosswind controls supported dependence on odor information

In an earlier controlled crosswind benchmark:

| Condition | Successes |
|---|---:|
| Intact controller | 9 / 20 |
| Bilateral contrast removed | 0 / 20 |
| Odor removed | 0 / 20 |

This result supports the importance of odor information and bilateral contrast in the implemented navigation policy.

However, the motor-training teacher itself contains a bilateral-contrast term. This experiment therefore should **not** be interpreted as an independent biological discovery about the living fly circuit.

---

### 4. Connectome perturbation and rewiring analyses supported a role for circuit structure

Fixed-state replay analyses showed that perturbing specific connectome populations, especially PFN-related populations, altered downstream readout features more strongly than size-matched random controls.

Degree-preserving rewiring controls also produced poorer decodability than the original connectome-derived topology.

These results support a functional contribution of the original wiring structure **within this model**, but do not establish identical causal relationships in vivo.

---

### 5. Temporal-search extensions produced informative negative results

Several attempts to improve odor-loss behavior were unsuccessful and are retained as part of the project record.

#### v4 temporal-memory approach

A lower-leak recurrent network extended state persistence, but a teacher policy using explicit time-since-odor and last-contrast variables was not reliably represented by the selected PFL36 readout.

Development-set closed-loop performance:

| Controller | Successes |
|---|---:|
| v3 | 20 / 30 |
| v4 | 7 / 30 |

#### v5 memory-free crosswind search

A memory-free odor-absent search policy could be learned offline, but closed-loop behavior often drove the fly away from the plume.

| Controller | Successes |
|---|---:|
| v3 | 20 / 30 |
| v5.1 | 1 / 30 |

These failures illustrate an important embodied-modeling lesson: **high offline decoder accuracy does not guarantee successful closed-loop navigation**.

---

## Reproducibility

The final neural controller was frozen and reloaded from disk before the final runtime was locked.

Final checkpoint:

```text
final_v3_connectome_controller.joblib
```

SHA256:

```text
8d6b557bb592f29100fdf8d95cb3ccd91f608516f6862e3f772491461e983acc
```

Exact parity checks showed:

- recurrent matrix parity: exact
- raw MLP/scaler parity: exact
- motor-runtime clipping parity: exact
- 500-step recurrent controller parity: exact
- full physical trajectory parity: exact for the validation seed
- plume snapshot parity: exact

The official final simulation runtime is checkpoint-driven rather than dependent on the original training objects.

---

## Interpretation

The project supports the following conclusion:

> A 532-neuron MaleCNS-derived navigation-related subcircuit, combined with modeled sensory encoding and a learned PFL motor readout, can support closed-loop odor-source localization in a stochastic virtual plume environment, reaching 70% success on 100 previously unseen randomized scenarios.

The main value of the project is not only the final success rate, but the separation between connectome-constrained recurrent dynamics, modeled sensory interfaces, a learned motor readout, embodied closed-loop testing, perturbation controls, rewiring controls, failed extensions, and final held-out validation.

---

## Repository structure

```text
drosophila-connectome-odor-navigation/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ src/                     # runtime and analysis code
├─ notebooks/               # final notebook(s)
├─ artifacts/
│  ├─ figures/              # final and supplementary figures
│  ├─ checkpoints/          # frozen controller checkpoint
│  └─ manifests/            # runtime metadata / hashes
├─ docs/
│  ├─ final_research_summary.md
│  ├─ project_summary_ko.md
│  └─ modeling_conventions.md
├─ kaggle/                  # Kaggle export files (added with public release)
└─ data/
   └─ README.md             # data-source and download instructions
```

Large raw MaleCNS files are not stored directly in GitHub. The repository is intended to store code, documentation, generated figures, manifests, and the compact frozen controller artifact.

---

## Data sources

The project uses public MaleCNS connectome data and public neuron annotations.

Required local inputs include:

```text
connectome-weights-male-cns-v1.0-minconf-0.5.feather
MaleCNS neuron annotation table
```

See `data/README.md` for the expected local layout and data-use notes.

---

## How to reproduce

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare public connectome inputs

Download the required MaleCNS connectome and annotation files and place them under the local data directory described in `data/README.md`.

### 3. Run the final notebook / runtime

The final public runtime will use the frozen checkpoint and reproduce the final checkpoint-driven controller. The notebook and source modules are being organized from the validated research notebook into a compact release structure.

---

## Modeling conventions and limitations

Important caveats include:

- This is a **532-neuron navigation-related subcircuit**, not the complete fly CNS or brain.
- Acetylcholine was modeled as excitatory and glutamate as inhibitory as a simplified sign convention.
- Connectome edges below the selected synapse threshold were removed.
- The recurrent weight matrix was spectrally rescaled for dynamical stability.
- PFN phase information and wind-side preferences are partly inferred or model-defined.
- Bilateral odor is virtually mapped onto the FB5AB pair; this is not claimed as established antenna-to-FB5AB anatomy.
- Body heading is supplied externally rather than generated by a reconstructed E-PG compass circuit.
- The PFL motor readout is learned from a designed local plume-tracking teacher.
- The plume is a stochastic filament model rather than full computational fluid dynamics.
- The random benchmark tests odor-source localization from approximately downwind initial conditions rather than general arbitrary-target navigation.
- Perturbation and rewiring effects are model-level results and do not prove identical biological causality in vivo.

See `docs/modeling_conventions.md` for additional detail.

---

## What should not be claimed

This project does not demonstrate:

- a full *Drosophila* brain simulation
- exact biological neurotransmitter or receptor dynamics
- experimentally established antenna-to-FB5AB connectivity
- a reconstructed internal heading compass
- biologically proven PFN phase tuning
- a biologically derived PFL motor decoder
- arbitrary waypoint navigation
- fluid-dynamically exact odor transport
- proof that model perturbation effects occur identically in living flies

---

## Project status

The controller, held-out benchmark, checkpoint, and runtime parity tests are frozen. Further tuning on the existing development or held-out sets is intentionally stopped.

The remaining work is release packaging, documentation, final figures, and the companion Kaggle notebook/dataset.
