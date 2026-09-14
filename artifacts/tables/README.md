# Result tables

These CSV files contain the frozen summary values used in the final GitHub documentation and figures.

| File | Contents |
|---|---|
| `final_heldout_summary.csv` | v3 vs v6 performance on 100 completely unseen random scenarios |
| `final_paired_outcomes.csv` | Matched held-out outcomes used for the paired comparison |
| `final_paired_statistics.csv` | Paired success difference, bootstrap interval, McNemar p-value, and minimum-distance difference |
| `crosswind_control_summary.csv` | Intact / contrast-removed / odor-removed crosswind control results |
| `development_controller_summary.csv` | Development-set comparison of v3, v4, v5.1, v6, and v6.1 |

The 30-scenario development set was repeatedly consulted during model development and is not treated as the final held-out test. The 100-scenario benchmark in `final_heldout_summary.csv` was evaluated only after the final controller-selection stage.
