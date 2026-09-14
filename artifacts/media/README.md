# Simulation demo media

This directory contains the final qualitative simulation demo generated from the frozen v3 checkpoint-driven runtime.

Public files:

```text
final_v3_navigation_demo.mp4
final_v3_navigation_demo_poster.png
```

Generate them from the repository root with:

```bash
python src/render_demo.py --seed 880000000
```

The default seed is a known successful trial from the already-completed frozen held-out benchmark. The resulting video is included only as an **illustrative qualitative example** of the embodied closed-loop behavior.

It must not be used as evidence for model performance. Quantitative performance evidence remains the frozen 100-scenario benchmark reported in `artifacts/tables/final_heldout_summary.csv` and the main README.

The demo shows the intermittent plume, odor source, wind direction, fly trajectory, body heading, bilateral antenna positions, odor responses, distance to source, and continuous motor outputs.

The companion Kaggle notebook can also generate fresh post-freeze random trials using the frozen v3 checkpoint. Those new trials are qualitative demonstrations only and remain separate from the reported benchmark statistics.