# Notebooks

The validated research workflow was developed in a Jupyter notebook. For the public release, the final notebook should be copied here after removing exploratory cells that are no longer needed for reproduction.

Recommended final filename:

```text
connectome_odor_navigation_final.ipynb
```

The public notebook should retain:

- connectome subset construction
- recurrent-controller definition
- sensory encoding
- plume and embodied-fly environment
- final v3 motor readout
- held-out evaluation summary
- checkpoint loading
- final checkpoint-driven simulator
- figure-generation cells

Historical exploratory branches such as v4/v5/v6 can remain documented in `docs/` rather than being required for the shortest reproduction path.
