# Source code

This directory contains the compact public runtime and reproducibility utilities for the frozen v3 controller.

## Files

| File | Purpose |
|---|---|
| `final_runtime.py` | Checkpoint-driven continuous odor-navigation runtime |
| `render_demo.py` | Render an illustrative MP4/poster from the frozen v3 runtime |
| `verify_checkpoint.py` | SHA256 and checkpoint-metadata integrity checks |
| `plot_final_results.py` | Recreate the frozen held-out result summary from recorded values |

The public runtime intentionally excludes historical experimental branches that are not required to reproduce the selected final controller. v4/v5/v6 development results remain documented in `docs/final_research_summary.md` and `artifacts/tables/development_controller_summary.csv`.

## Run one frozen v3 trial

```bash
python src/final_runtime.py --seed 851042066
```

The runtime reconstructs bilateral FB5AB odor encoding and continuous PFN wind/body-heading encoding from metadata stored inside the frozen checkpoint. Goal/source coordinates are never passed to the controller; they are used only for stopping and evaluation.

## Render an illustrative simulation demo

```bash
python src/render_demo.py --seed 880000000
```

This generates:

```text
artifacts/media/final_v3_navigation_demo.mp4
artifacts/media/final_v3_navigation_demo_poster.png
```

The default seed is a known successful trial from the already-completed frozen held-out benchmark. The resulting video is **qualitative only** and is not used as performance evidence; quantitative claims remain based on the frozen 100-scenario held-out benchmark.

## Verify the checkpoint

```bash
python src/verify_checkpoint.py
```

Expected SHA256:

```text
8d6b557bb592f29100fdf8d95cb3ccd91f608516f6862e3f772491461e983acc
```

## Recreate the final held-out summary

```bash
python src/plot_final_results.py
```

This uses the already-frozen held-out results and does not re-tune or re-run the 100-trial benchmark.
