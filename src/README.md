# Source code

The validated project was developed in a research notebook and is being separated into compact runtime modules for the public release.

The final public source layout is intended to contain modules for:

- connectome-controller loading and recurrent updates
- sensory encoding
- intermittent-plume environment
- embodied-fly dynamics
- checkpoint-driven simulation
- visualization and figure generation

Only code paths that reproduce the frozen v3 controller should be required for the final release. Historical v4/v5/v6 experiments are documented as research results but do not need to be part of the minimal runtime API.

The frozen checkpoint and its expected hash are documented in `artifacts/checkpoints/README.md` and `artifacts/manifests/final_runtime_manifest.json`.
