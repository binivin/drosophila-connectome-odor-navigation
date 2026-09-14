"""Recreate the frozen final held-out summary figure from recorded results."""

import numpy as np
import matplotlib.pyplot as plt

V3_RATE = 0.70
V6_RATE = 0.71
V3_CI = (0.604, 0.781)
V6_CI = (0.615, 0.790)
PAIRED_COUNTS = [60, 11, 10, 19]


def main():
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))

    rates = np.array([V3_RATE, V6_RATE])
    lower = np.array([V3_RATE - V3_CI[0], V6_RATE - V6_CI[0]])
    upper = np.array([V3_CI[1] - V3_RATE, V6_CI[1] - V6_RATE])

    bars = axes[0].bar(["v3 final", "v6 + casting"], rates)
    axes[0].errorbar(
        [0, 1], rates, yerr=np.vstack([lower, upper]), fmt="none", capsize=5
    )
    axes[0].set_ylim(0, 1)
    axes[0].set_ylabel("Success rate")
    axes[0].set_title("100 unseen random scenarios")
    for bar, label in zip(bars, ["70/100", "71/100"]):
        axes[0].text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.03,
            label,
            ha="center",
        )

    labels = ["Both success", "v3→v6 rescue", "v3→v6 regress", "Both fail"]
    axes[1].bar(labels, PAIRED_COUNTS)
    axes[1].set_ylabel("Trials")
    axes[1].set_title("Paired held-out outcomes")
    axes[1].tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig("artifacts/figures/final_heldout_results_recreated.svg", bbox_inches="tight")
    fig.savefig("artifacts/figures/final_heldout_results_recreated.png", dpi=220, bbox_inches="tight")


if __name__ == "__main__":
    main()
