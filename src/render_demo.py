"""Render an illustrative MP4 from the frozen v3 checkpoint-driven runtime.

The demo is qualitative only. Aggregate performance evidence remains the frozen
100-scenario held-out benchmark reported in the repository tables/README.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import imageio_ffmpeg
import matplotlib
matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np

from final_runtime import (
    RANDOM_ARENA_SIZE,
    SUCCESS_DISTANCE,
    simulate_random_trial_checkpoint,
)


def _fly_triangle(position: np.ndarray, heading: float, scale: float = 0.55) -> np.ndarray:
    """Return a small triangular body polygon pointing along the fly heading."""
    forward = np.array([np.cos(heading), np.sin(heading)])
    lateral = np.array([-np.sin(heading), np.cos(heading)])
    nose = position + scale * forward
    rear = position - 0.45 * scale * forward
    left = rear + 0.45 * scale * lateral
    right = rear - 0.45 * scale * lateral
    return np.vstack([nose, left, right])


def render_demo(
    seed: int,
    checkpoint: Path,
    output: Path,
    poster: Path,
    fps: int = 20,
) -> dict:
    """Run one frozen trial and save an illustrative MP4 plus poster PNG."""
    trial = simulate_random_trial_checkpoint(
        seed=int(seed),
        checkpoint_path=checkpoint,
        record_plume=True,
    )

    times = np.asarray(trial["times"], dtype=float)
    positions = np.asarray(trial["positions"], dtype=float)
    headings = np.asarray(trial["headings"], dtype=float)
    left_positions = np.asarray(trial["left_positions"], dtype=float)
    right_positions = np.asarray(trial["right_positions"], dtype=float)
    left_responses = np.asarray(trial["left_responses"], dtype=float)
    right_responses = np.asarray(trial["right_responses"], dtype=float)
    distances = np.asarray(trial["distances"], dtype=float)
    speeds = np.asarray(trial["speeds"], dtype=float)
    omegas = np.asarray(trial["omegas"], dtype=float)

    scenario = trial["scenario"]
    start = np.asarray(scenario["start"], dtype=float)
    goal = np.asarray(scenario["goal"], dtype=float)
    wind = np.asarray(scenario["wind_velocity"], dtype=float)

    output.parent.mkdir(parents=True, exist_ok=True)
    poster.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8.4, 8.0))
    ax.set_xlim(0, RANDOM_ARENA_SIZE)
    ax.set_ylim(0, RANDOM_ARENA_SIZE)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x position")
    ax.set_ylabel("y position")
    ax.set_title("Frozen v3 connectome-constrained odor navigation")

    ax.scatter(start[0], start[1], marker="x", s=80, label="start")
    ax.scatter(goal[0], goal[1], marker="*", s=180, label="odor source")
    source_circle = plt.Circle(goal, SUCCESS_DISTANCE, fill=False, linestyle="--", linewidth=1.2)
    ax.add_patch(source_circle)

    wind_scale = 4.0
    ax.arrow(
        goal[0], goal[1],
        wind[0] * wind_scale, wind[1] * wind_scale,
        width=0.04, head_width=0.55, length_includes_head=True,
    )
    ax.text(
        goal[0] + wind[0] * wind_scale,
        goal[1] + wind[1] * wind_scale,
        " wind",
        fontsize=9,
    )

    plume_scatter = ax.scatter([], [], s=[], alpha=0.18, label="plume filaments")
    trail_line, = ax.plot([], [], linewidth=1.5, label="trajectory")
    antenna_line, = ax.plot([], [], marker="o", markersize=3, linewidth=0.9)
    fly_patch = Polygon(_fly_triangle(positions[0], headings[0]), closed=True)
    ax.add_patch(fly_patch)

    info = ax.text(
        0.02,
        0.98,
        "",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.35", alpha=0.85),
    )
    note = ax.text(
        0.5,
        -0.10,
        "Illustrative frozen-v3 trial — not used as performance evidence",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=9,
    )
    ax.legend(loc="lower left", fontsize=8)

    puff_frames = trial["puff_positions"]
    age_frames = trial["puff_ages"]
    strength_frames = trial["puff_strengths"]

    def update(frame_idx: int):
        puff_positions = np.asarray(puff_frames[frame_idx], dtype=float)
        puff_ages = np.asarray(age_frames[frame_idx], dtype=float)
        puff_strengths = np.asarray(strength_frames[frame_idx], dtype=float)

        if len(puff_positions):
            plume_scatter.set_offsets(puff_positions)
            visual_strength = puff_strengths * np.exp(-puff_ages / 14.0)
            sizes = np.clip(5.0 + 18.0 * visual_strength, 4.0, 48.0)
            plume_scatter.set_sizes(sizes)
        else:
            plume_scatter.set_offsets(np.empty((0, 2)))
            plume_scatter.set_sizes([])

        trail_line.set_data(positions[: frame_idx + 1, 0], positions[: frame_idx + 1, 1])
        antenna_line.set_data(
            [left_positions[frame_idx, 0], positions[frame_idx, 0], right_positions[frame_idx, 0]],
            [left_positions[frame_idx, 1], positions[frame_idx, 1], right_positions[frame_idx, 1]],
        )
        fly_patch.set_xy(_fly_triangle(positions[frame_idx], headings[frame_idx]))

        status = "SUCCESS" if trial["success"] and frame_idx == len(times) - 1 else "running"
        info.set_text(
            f"t = {times[frame_idx]:.1f} s\n"
            f"distance = {distances[frame_idx]:.2f}\n"
            f"odor L/R = {left_responses[frame_idx]:.3f} / {right_responses[frame_idx]:.3f}\n"
            f"speed = {speeds[frame_idx]:.2f}\n"
            f"angular velocity = {omegas[frame_idx]:+.2f}\n"
            f"status = {status}"
        )
        return plume_scatter, trail_line, antenna_line, fly_patch, info, note

    ani = animation.FuncAnimation(
        fig,
        update,
        frames=len(times),
        interval=1000 / fps,
        blit=False,
        repeat=False,
    )

    matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
    writer = animation.FFMpegWriter(
        fps=fps,
        codec="libx264",
        bitrate=1800,
        extra_args=["-pix_fmt", "yuv420p"],
        metadata={
            "title": "Frozen v3 connectome-constrained odor navigation demo",
            "comment": "Illustrative trial only; aggregate benchmark results are reported separately.",
        },
    )
    ani.save(output, writer=writer, dpi=145)

    update(len(times) - 1)
    final_status = "SUCCESS" if trial["success"] else "FAILED / TIMEOUT"
    ax.set_title(f"Frozen v3 navigation demo — {final_status}")
    fig.savefig(poster, dpi=180, bbox_inches="tight")
    plt.close(fig)

    return trial


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an illustrative frozen-v3 navigation demo")
    parser.add_argument(
        "--seed",
        type=int,
        default=880000000,
        help=(
            "Scenario seed. The default is a known successful frozen held-out trial; "
            "the video is qualitative only and is not used as performance evidence."
        ),
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("artifacts/checkpoints/final_v3_connectome_controller.joblib"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/media/final_v3_navigation_demo.mp4"),
    )
    parser.add_argument(
        "--poster",
        type=Path,
        default=Path("artifacts/media/final_v3_navigation_demo_poster.png"),
    )
    parser.add_argument("--fps", type=int, default=20)
    args = parser.parse_args()

    trial = render_demo(
        seed=args.seed,
        checkpoint=args.checkpoint,
        output=args.output,
        poster=args.poster,
        fps=args.fps,
    )

    print(f"seed={trial['seed']}")
    print(f"success={trial['success']}")
    print(f"min_distance={float(np.min(trial['distances'])):.3f}")
    print(f"final_distance={float(trial['distances'][-1]):.3f}")
    print(f"video={args.output}")
    print(f"poster={args.poster}")
    print("NOTE: this video is illustrative and is not used as performance evidence.")


if __name__ == "__main__":
    main()
