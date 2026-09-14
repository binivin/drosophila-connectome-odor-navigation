"""Final checkpoint-driven runtime for connectome-constrained odor navigation.

This module is a compact public release of the validated v3 runtime used in the
project notebook. It intentionally exposes the modeling conventions that are
required to reproduce the frozen controller.

The final checkpoint is expected at:
    artifacts/checkpoints/final_v3_connectome_controller.joblib

The checkpoint stores the recurrent connectome matrix, PFL readout model,
scalers, sensory metadata, motor bounds, and validation metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np


RANDOM_ARENA_SIZE = 30.0
RANDOM_DT = 0.05
RANDOM_MAX_SECONDS = 45.0
RANDOM_FRAME_STRIDE = 2
SUCCESS_DISTANCE = 0.50
ODOR_HALF_SATURATION = 2.0
REFERENCE_WIND_SPEED = float(np.linalg.norm(np.array([-0.48, -0.42])))


def wrap_pi(angle: float) -> float:
    """Wrap an angle to [-pi, pi)."""
    return float((angle + np.pi) % (2.0 * np.pi) - np.pi)


def body_theta_to_model_heading(body_theta: float) -> float:
    """Convert physical body angle to the internal PFN angular convention."""
    return float((float(body_theta) + np.pi / 2.0) % (2.0 * np.pi))


def odor_receptor_response(
    concentration: float | np.ndarray,
    half_saturation: float = ODOR_HALF_SATURATION,
):
    """Simple saturating concentration-response curve C / (C + K_half)."""
    concentration = np.maximum(np.asarray(concentration, dtype=float), 0.0)
    return concentration / (concentration + half_saturation)


@dataclass
class FlyState:
    """Minimal continuous fly state used by the final open-arena runtime."""

    position: np.ndarray
    heading: float


def get_antenna_positions(
    fly: FlyState,
    forward_offset: float = 0.32,
    lateral_offset: float = 0.13,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return continuous left and right antenna-tip coordinates."""
    theta = float(fly.heading)
    forward = np.array([np.cos(theta), np.sin(theta)])
    left_vector = np.array([np.sin(theta), -np.cos(theta)])
    head_center = np.asarray(fly.position, dtype=float) + forward * forward_offset
    left_antenna = head_center + left_vector * lateral_offset
    right_antenna = head_center - left_vector * lateral_offset
    return left_antenna, right_antenna


class FastIntermittentFilamentPlume2D:
    """Vectorized stochastic filament plume used by the final navigation test."""

    def __init__(
        self,
        source_position,
        wind_velocity=(-0.48, -0.42),
        emission_rate=4.0,
        initial_sigma=0.035,
        diffusion_rate=0.0018,
        decay_time=14.0,
        crosswind_noise=0.16,
        crosswind_memory=0.985,
        strength_log_sd=0.45,
        seed=20260915,
    ):
        self.source_position = np.asarray(source_position, dtype=float)
        self.wind_velocity = np.asarray(wind_velocity, dtype=float)
        self.emission_rate = float(emission_rate)
        self.initial_sigma = float(initial_sigma)
        self.diffusion_rate = float(diffusion_rate)
        self.decay_time = float(decay_time)
        self.crosswind_noise = float(crosswind_noise)
        self.crosswind_memory = float(crosswind_memory)
        self.strength_log_sd = float(strength_log_sd)
        self.rng = np.random.default_rng(seed)

        wind_speed = np.linalg.norm(self.wind_velocity)
        if wind_speed <= 0:
            raise ValueError("wind_velocity must have non-zero magnitude")

        self.wind_unit = self.wind_velocity / wind_speed
        self.crosswind_unit = np.array([-self.wind_unit[1], self.wind_unit[0]])

        self.time = 0.0
        self._emission_accumulator = 0.0
        self.positions = np.empty((0, 2), dtype=float)
        self.ages = np.empty(0, dtype=float)
        self.cross_speeds = np.empty(0, dtype=float)
        self.strengths = np.empty(0, dtype=float)

    def _emit_one(self) -> None:
        source_jitter = self.rng.normal(0.0, 0.025, size=2)
        strength = float(self.rng.lognormal(mean=0.0, sigma=self.strength_log_sd))
        cross_speed = float(self.rng.normal(0.0, self.crosswind_noise))

        self.positions = np.vstack([self.positions, self.source_position + source_jitter])
        self.ages = np.append(self.ages, 0.0)
        self.cross_speeds = np.append(self.cross_speeds, cross_speed)
        self.strengths = np.append(self.strengths, strength)

    def step(self, dt: float) -> None:
        dt = float(dt)
        self.time += dt
        self._emission_accumulator += self.emission_rate * dt

        while self._emission_accumulator >= 1.0:
            self._emit_one()
            self._emission_accumulator -= 1.0

        n = len(self.ages)
        if n == 0:
            return

        self.ages += dt
        noise_sd = self.crosswind_noise * np.sqrt(1.0 - self.crosswind_memory**2)
        self.cross_speeds = (
            self.crosswind_memory * self.cross_speeds
            + self.rng.normal(0.0, noise_sd, size=n)
        )

        velocities = (
            self.wind_velocity[None, :]
            + self.cross_speeds[:, None] * self.crosswind_unit[None, :]
        )
        self.positions += velocities * dt

        keep = self.ages < 3.5 * self.decay_time
        self.positions = self.positions[keep]
        self.ages = self.ages[keep]
        self.cross_speeds = self.cross_speeds[keep]
        self.strengths = self.strengths[keep]

    def concentration(self, position) -> float:
        if len(self.ages) == 0:
            return 0.0

        position = np.asarray(position, dtype=float)
        sigma2 = self.initial_sigma**2 + 2.0 * self.diffusion_rate * self.ages
        delta = self.positions - position[None, :]
        r2 = np.sum(delta**2, axis=1)
        decay = np.exp(-self.ages / self.decay_time)
        amplitude = self.strengths * decay / (2.0 * np.pi * sigma2)
        values = amplitude * np.exp(-0.5 * r2 / sigma2)
        return float(np.sum(values))


def sample_random_start_goal(rng: np.random.Generator) -> Dict[str, np.ndarray | float]:
    """Sample the final benchmark geometry used in the frozen evaluation."""
    for _ in range(10000):
        goal = rng.uniform(5.0, 25.0, size=2)
        start = rng.uniform(3.0, 27.0, size=2)
        distance = float(np.linalg.norm(start - goal))
        if 9.0 <= distance <= 14.0:
            break
    else:
        raise RuntimeError("Could not sample valid start/goal geometry")

    source_to_start_angle = float(
        np.arctan2(start[1] - goal[1], start[0] - goal[0])
    )
    wind_angle = source_to_start_angle + rng.uniform(
        np.deg2rad(-10.0), np.deg2rad(10.0)
    )
    wind_velocity = REFERENCE_WIND_SPEED * np.array(
        [np.cos(wind_angle), np.sin(wind_angle)]
    )
    initial_heading = float(rng.uniform(-np.pi, np.pi))

    return {
        "start": start,
        "goal": goal,
        "wind_angle": float(wind_angle),
        "wind_velocity": wind_velocity,
        "initial_heading": initial_heading,
    }


class FrozenV3CheckpointController:
    """Disk-loaded final v3 controller reconstructed from checkpoint metadata."""

    def __init__(self, checkpoint_path: str | Path):
        self.checkpoint_path = Path(checkpoint_path)
        self.data = joblib.load(self.checkpoint_path)

        self.N = int(self.data["N"])
        self.W = self.data["W_recurrent_sparse"]
        metadata = self.data["metadata"]
        self.leak = float(metadata["recurrent_leak"])
        self.odor_gain = float(metadata["odor_gain"])
        self.wind_gain = float(metadata["wind_gain"])

        self.neuron_ids = np.asarray(self.data["neuron_ids"])
        self.neuron_index = {int(body_id): i for i, body_id in enumerate(self.neuron_ids)}
        self.fb5ab_indices = np.asarray(self.data["fb5ab_indices"], dtype=int)
        if len(self.fb5ab_indices) != 2:
            raise ValueError("Checkpoint must contain exactly two FB5AB indices")

        self.pfn_metadata = self.data["pfn_input_metadata_v2"]
        self.side_wind_preference = dict(self.data["SIDE_WIND_PREFERENCE"])

        self.readout_indices = np.asarray(self.data["readout_indices"], dtype=int)
        self.x_scaler = self.data["motor_x_scaler"]
        self.y_scaler = self.data["motor_y_scaler"]
        self.mlp = self.data["motor_mlp"]

        bounds = self.data["motor_output_bounds"]
        self.v_min, self.v_max = map(float, bounds["forward_speed"])
        self.omega_min, self.omega_max = map(float, bounds["angular_velocity"])

        self.state = np.zeros(self.N, dtype=float)

    def reset(self) -> None:
        self.state.fill(0.0)

    def encode_odor_bilateral(self, left_odor: float, right_odor: float) -> np.ndarray:
        external = np.zeros(self.N, dtype=float)
        external[int(self.fb5ab_indices[0])] = float(left_odor)
        external[int(self.fb5ab_indices[1])] = float(right_odor)
        return external

    def encode_pfn_input_continuous_wind(
        self,
        physical_wind_angle: float,
        fly_heading_angle: float,
    ) -> np.ndarray:
        wind_angle = (float(physical_wind_angle) + np.pi / 2.0) % (2.0 * np.pi)
        heading_angle = body_theta_to_model_heading(fly_heading_angle)
        relative_wind = (wind_angle - heading_angle) % (2.0 * np.pi)
        pfn_input = np.zeros(self.N, dtype=float)

        for row in self.pfn_metadata.itertuples():
            heading_difference = np.angle(
                np.exp(1j * (float(row.phase_angle) - heading_angle))
            )
            heading_tuning = (1.0 + np.cos(heading_difference)) / 2.0

            preferred_wind = self.side_wind_preference[row.input_side]
            wind_difference = np.angle(
                np.exp(1j * (relative_wind - preferred_wind))
            )
            wind_tuning = (1.0 + np.cos(wind_difference)) / 2.0

            idx = self.neuron_index[int(row.bodyId)]
            pfn_input[idx] = heading_tuning * wind_tuning

        return pfn_input

    def decode_motor(self) -> Tuple[float, float]:
        features = np.asarray(
            self.state[self.readout_indices], dtype=float
        ).reshape(1, -1)
        x_scaled = self.x_scaler.transform(features)
        y_scaled = self.mlp.predict(x_scaled)
        y = self.y_scaler.inverse_transform(y_scaled)[0]

        v = float(np.clip(y[0], self.v_min, self.v_max))
        omega = float(np.clip(y[1], self.omega_min, self.omega_max))
        return v, omega

    def step(
        self,
        left_odor: float,
        right_odor: float,
        wind_angle: float,
        fly_heading: float,
    ) -> Tuple[float, float, np.ndarray]:
        odor_input = self.encode_odor_bilateral(left_odor, right_odor)
        pfn_input = self.encode_pfn_input_continuous_wind(wind_angle, fly_heading)
        external = self.odor_gain * odor_input + self.wind_gain * pfn_input
        candidate = np.tanh(self.W.dot(self.state) + external)
        self.state = (1.0 - self.leak) * self.state + self.leak * candidate
        v, omega = self.decode_motor()
        return v, omega, self.state.copy()


def simulate_random_trial_checkpoint(
    seed: int,
    checkpoint_path: str | Path,
    record_plume: bool = True,
) -> Dict[str, object]:
    """Run one final v3 closed-loop navigation trial."""
    seed = int(seed)
    rng = np.random.default_rng(seed)
    scenario = sample_random_start_goal(rng)

    start = np.asarray(scenario["start"], dtype=float)
    goal = np.asarray(scenario["goal"], dtype=float)
    wind_velocity = np.asarray(scenario["wind_velocity"], dtype=float)
    wind_angle = float(scenario["wind_angle"])
    initial_heading = float(scenario["initial_heading"])

    plume = FastIntermittentFilamentPlume2D(
        source_position=goal,
        wind_velocity=tuple(wind_velocity),
        emission_rate=4.0,
        initial_sigma=0.035,
        diffusion_rate=0.0018,
        decay_time=14.0,
        crosswind_noise=0.16,
        crosswind_memory=0.985,
        strength_log_sd=0.45,
        seed=seed + 100000,
    )

    for _ in range(int(35.0 / RANDOM_DT)):
        plume.step(RANDOM_DT)

    fly = FlyState(position=start.copy(), heading=initial_heading)
    body_radius = 0.18
    controller = FrozenV3CheckpointController(checkpoint_path)
    controller.reset()

    times: List[float] = []
    positions: List[np.ndarray] = []
    headings: List[float] = []
    left_positions: List[np.ndarray] = []
    right_positions: List[np.ndarray] = []
    left_responses: List[float] = []
    right_responses: List[float] = []
    distances: List[float] = []
    speeds: List[float] = []
    omegas: List[float] = []
    puff_positions_frames: List[np.ndarray] = []
    puff_ages_frames: List[np.ndarray] = []
    puff_strengths_frames: List[np.ndarray] = []

    success = False
    boundary_contacts = 0
    max_steps = int(RANDOM_MAX_SECONDS / RANDOM_DT)

    for step_i in range(max_steps):
        left_pos, right_pos = get_antenna_positions(fly)
        left_raw = plume.concentration(left_pos)
        right_raw = plume.concentration(right_pos)
        left_response = float(odor_receptor_response(left_raw))
        right_response = float(odor_receptor_response(right_raw))

        forward_speed, angular_speed, _ = controller.step(
            left_response,
            right_response,
            wind_angle,
            fly.heading,
        )

        fly.heading = wrap_pi(fly.heading + angular_speed * RANDOM_DT)
        heading_vector = np.array([np.cos(fly.heading), np.sin(fly.heading)])
        proposed_position = fly.position + forward_speed * RANDOM_DT * heading_vector
        clipped_position = np.clip(
            proposed_position,
            body_radius,
            RANDOM_ARENA_SIZE - body_radius,
        )
        if not np.allclose(proposed_position, clipped_position):
            boundary_contacts += 1
        fly.position = clipped_position

        plume.step(RANDOM_DT)
        distance = float(np.linalg.norm(fly.position - goal))

        if step_i % RANDOM_FRAME_STRIDE == 0:
            visual_left, visual_right = get_antenna_positions(fly)
            times.append(step_i * RANDOM_DT)
            positions.append(fly.position.copy())
            headings.append(float(fly.heading))
            left_positions.append(visual_left.copy())
            right_positions.append(visual_right.copy())
            left_responses.append(left_response)
            right_responses.append(right_response)
            distances.append(distance)
            speeds.append(float(forward_speed))
            omegas.append(float(angular_speed))

            if record_plume:
                puff_positions_frames.append(plume.positions.copy())
                puff_ages_frames.append(plume.ages.copy())
                puff_strengths_frames.append(plume.strengths.copy())

        if distance <= SUCCESS_DISTANCE:
            success = True
            break

    return {
        "seed": seed,
        "scenario": scenario,
        "success": bool(success),
        "boundary_contacts": int(boundary_contacts),
        "times": np.asarray(times),
        "positions": np.asarray(positions),
        "headings": np.asarray(headings),
        "left_positions": np.asarray(left_positions),
        "right_positions": np.asarray(right_positions),
        "left_responses": np.asarray(left_responses),
        "right_responses": np.asarray(right_responses),
        "distances": np.asarray(distances),
        "speeds": np.asarray(speeds),
        "omegas": np.asarray(omegas),
        "puff_positions": puff_positions_frames,
        "puff_ages": puff_ages_frames,
        "puff_strengths": puff_strengths_frames,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run one final v3 navigation trial")
    parser.add_argument("--seed", type=int, default=851042066)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("artifacts/checkpoints/final_v3_connectome_controller.joblib"),
    )
    args = parser.parse_args()

    trial = simulate_random_trial_checkpoint(
        seed=args.seed,
        checkpoint_path=args.checkpoint,
        record_plume=False,
    )
    print(f"seed={trial['seed']}")
    print(f"success={trial['success']}")
    print(f"min_distance={float(np.min(trial['distances'])):.3f}")
    print(f"final_distance={float(trial['distances'][-1]):.3f}")
    print(f"boundary_contacts={trial['boundary_contacts']}")


if __name__ == "__main__":
    main()
