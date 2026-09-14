# Final controller checkpoint

The frozen neural controller used by the final runtime is:

```text
final_v3_connectome_controller.joblib
```

Expected SHA256:

```text
8d6b557bb592f29100fdf8d95cb3ccd91f608516f6862e3f772491461e983acc
```

The checkpoint contains the compact frozen recurrent controller state needed for the validated v3 runtime, including the 532-neuron recurrent matrix, PFL36 motor readout, preprocessing objects, metadata, and runtime motor bounds.

The checkpoint was validated against the in-memory research runtime with exact parity for:

- recurrent weights
- raw MLP/scaler outputs
- motor clipping
- 500 recurrent controller steps
- one full physical closed-loop trajectory, including plume snapshots

The binary `.joblib` file must be copied into this directory for a complete release. The manifest in `../manifests/final_runtime_manifest.json` records the expected hash and final evaluation metadata.
