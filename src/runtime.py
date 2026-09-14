"""Final checkpoint-driven runtime for connectome-constrained odor navigation.

This module reproduces the frozen v3 runtime described in the project README.
The odor-source coordinates are used only for stopping/evaluation and are never
provided to the controller.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib

import joblib
import numpy as np

RANDOM_ARENA_SIZE = 30.0
RANDOM_DT = 0.05
RANDOM_MAX_SECONDS = 45.0
RANDOM_FRAME_STRIDE = 2
SUCCESS_DISTANCE = 0.50
REFERENCE_WIND_SPEED = float(np.linalg.norm(np.array([-0.48, -0.42])))
ODOR_HALF_SATURATION = 2.0
EXPECTED_CHECKPOINT_SHA256 = "8d6b557bb592f29100fdf8d95cb3ccd91f608516f6862e3f772491461e983acc"


def wrap_angle_pi(angle: float) -> float:
    return float((angle + np.pi) % (2.0 * np.pi) - np.pi)


def body_theta_to_model_heading(body_theta: float) -> float:
    return float((float(body_theta) + np.pi / 2.0) % (2.0 * np.pi))


def odor_receptor_response(concentration, half_saturation: float = ODOR_HALF_SATURATION):
    concentration = np.maximum(np.asarray(concentration, dtype=float), 0.0)
    return concentration / (concentration + half_saturation)


@dataclass
class FlyState:
    position: np.ndarray
    heading: float


def get_antenna_positions(fly: FlyState, forward_offset: float = 0.32, lateral_offset: float = 0.13):
    theta = float(fly.heading)
    forward = np.array([np.cos(theta), np.sin(theta)])
    left_vector = np.array([np.sin(theta), -np.cos(theta)])
    head_center = np.asarray(fly.position, dtype=float) + forward * forward_offset
    return (
        head_center + left_vector * lateral_offset,
        head_center - left_vector * lateral_offset,
    )


class FastIntermittentFilamentPlume2D:
    def __init__(self, source_position, wind_velocity=(-0.48, -0.42), emission_rate=4.0,
                 initial_sigma=0.035, diffusion_rate=0.0018, decay_time=14.0,
                 crosswind_noise=0.16, crosswind_memory=0.985,
                 strength_log_sd=0.45, seed=20260915):
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
        self.wind_unit = self.wind_velocity / wind_speed
        self.crosswind_unit = np.array([-self.wind_unit[1], self.wind_unit[0]])
        self.time = 0.0
        self._emission_accumulator = 0.0
        self.positions = np.empty((0, 2), dtype=float)
        self.ages = np.empty(0, dtype=float)
        self.cross_speeds = np.empty(0, dtype=float)
        self.strengths = np.empty(0, dtype=float)

    @property
    def puffs(self):
        return range(len(self.ages))

    def _emit_one(self):
        source_jitter = self.rng.normal(0.0, 0.025, size=2)
        strength = float(self.rng.lognormal(mean=0.0, sigma=self.strength_log_sd))
        cross_speed = float(self.rng.normal(0.0, self.crosswind_noise))
        self.positions = np.vstack([self.positions, self.source_position + source_jitter])
        self.ages = np.append(self.ages, 0.0)
        self.cross_speeds = np.append(self.cross_speeds, cross_speed)
        self.strengths = np.append(self.strengths, strength)

    def step(self, dt):
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
        noise_sd = self.crosswind_noise * np.sqrt(1.0 - self.crosswind_memory ** 2)
        self.cross_speeds = (
            self.crosswind_memory * self.cross_speeds
            + self.rng.normal(0.0, noise_sd, size=n)
        )
        velocities = self.wind_velocity[None, :] + self.cross_speeds[:, None] * self.crosswind_unit[None, :]
        self.positions += velocities * dt
        keep = self.ages < 3.5 * self.decay_time
        self.positions = self.positions[keep]
        self.ages = self.ages[keep]
        self.cross_speeds = self.cross_speeds[keep]
        self.strengths = self.strengths[keep]

    def concentration(self, position):
        if len(self.ages) == 0:
            return 0.0
        position = np.asarray(position, dtype=float)
        sigma2 = self.initial_sigma ** 2 + 2.0 * self.diffusion_rate * self.ages
        delta = self.positions - position[None, :]
        r2 = np.sum(delta ** 2, axis=1)
        decay = np.exp(-self.ages / self.decay_time)
        amplitude = self.strengths * decay / (2.0 * np.pi * sigma2)
        values = amplitude * np.exp(-0.5 * r2 / sigma2)
        return float(np.sum(values))


class FrozenV3CheckpointController:
    """Disk-loaded frozen v3 controller.

    The checkpoint contains the recurrent matrix, PFN metadata, FB5AB indices,
    PFL readout indices, trained scalers/MLP, and motor-output bounds.
    """
    def __init__(self, checkpoint_path="artifacts/checkpoints/final_v3_connectome_controller.joblib", verify_hash=True):
        self.checkpoint_path = Path(checkpoint_path)
        if verify_hash:
            digest = hashlib.sha256(self.checkpoint_path.read_bytes()).hexdigest()
            if digest != EXPECTED_CHECKPOINT_SHA256:
                raise RuntimeError(f"Checkpoint SHA256 mismatch: {digest}")
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
        self.pfn_metadata = self.data["pfn_input_metadata_v2"].copy()
        self.side_wind_preference = dict(self.data["SIDE_WIND_PREFERENCE"])
        self.readout_indices = np.asarray(self.data["readout_indices"], dtype=int)
        self.x_scaler = self.data["motor_x_scaler"]
        self.y_scaler = self.data["motor_y_scaler"]
        self.mlp = self.data["motor_mlp"]
        bounds = self.data["motor_output_bounds"]
        self.v_min, self.v_max = map(float, bounds["forward_speed"])
        self.omega_min, self.omega_max = map(float, bounds["angular_velocity"])
        self.state = np.zeros(self.N, dtype=float)

    def reset(self):
        self.state.fill(0.0)

    def _encode_odor_bilateral(self, left_odor, right_odor):
        external = np.zeros(self.N, dtype=float)
        external[self.fb5ab_indices[0]] = float(left_odor)
        external[self.fb5ab_indices[1]] = float(right_odor)
        return external

    def _encode_pfn(self, wind_flow_angle, fly_heading_angle):
        heading_angle = body_theta_to_model_heading(fly_heading_angle)
        model_wind_angle = (float(wind_flow_angle) + np.pi / 2.0) % (2.0 * np.pi)
        relative_wind = (model_wind_angle - heading_angle) % (2.0 * np.pi)
        pfn_input = np.zeros(self.N, dtype=float)
        for _, row in self.pfn_metadata.iterrows():
            body_id = int(row["bodyId"])
            if body_id not in self.neuron_index:
                continue
            side = row.get("side", row.get("input_side", None))
            if side not in self.side_wind_preference:
                side = row.get("input_side", None)
            if side not in self.side_wind_preference:
                continue
            phase_angle = float(row["phase_angle"])
            preferred_wind = float(self.side_wind_preference[side])
            heading_error = wrap_angle_pi(phase_angle - heading_angle)
            wind_error = wrap_angle_pi(relative_wind - preferred_wind)
            heading_tuning = (1.0 + np.cos(heading_error)) / 2.0
            wind_tuning = (1.0 + np.cos(wind_error)) / 2.0
            pfn_input[self.neuron_index[body_id]] = heading_tuning * wind_tuning
        return pfn_input

    def decode_motor(self):
        features = np.asarray(self.state[self.readout_indices], dtype=float).reshape(1, -1)
        x_scaled = self.x_scaler.transform(features)
        y_scaled = self.mlp.predict(x_scaled)
        y = self.y_scaler.inverse_transform(y_scaled)[0]
        v = float(np.clip(y[0], self.v_min, self.v_max))
        omega = float(np.clip(y[1], self.omega_min, self.omega_max))
        return v, omega

    def step(self, left_odor, right_odor, wind_angle, fly_heading):
        odor_input = self._encode_odor_bilateral(left_odor, right_odor)
        pfn_input = self._encode_pfn(wind_angle, fly_heading)
        external = self.odor_gain * odor_input + self.wind_gain * pfn_input
        candidate = np.tanh(self.W.dot(self.state) + external)
        self.state = (1.0 - self.leak) * self.state + self.leak * candidate
        v, omega = self.decode_motor()
        return v, omega, self.state.copy()


def sample_random_start_goal(rng: np.random.Generator):
    for _ in range(10000):
        goal = rng.uniform(5.0, 25.0, size=2)
        start = rng.uniform(3.0, 27.0, size=2)
        distance = float(np.linalg.norm(start - goal))
        if 9.0 <= distance <= 14.0:
            break
    else:
        raise RuntimeError("Could not sample valid start/goal geometry.")
    source_to_start_angle = float(np.arctan2(start[1] - goal[1], start[0] - goal[0]))
    wind_angle = source_to_start_angle + rng.uniform(np.deg2rad(-10.0), np.deg2rad(10.0))
    wind_velocity = REFERENCE_WIND_SPEED * np.array([np.cos(wind_angle), np.sin(wind_angle)])
    initial_heading = float(rng.uniform(-np.pi, np.pi))
    return {
        "start": start,
        "goal": goal,
        "wind_angle": wind_angle,
        "wind_velocity": wind_velocity,
        "initial_heading": initial_heading,
    }


def simulate_random_trial_checkpoint(seed: int, checkpoint_path="artifacts/checkpoints/final_v3_connectome_controller.joblib", record_puffs=True):
    seed = int(seed)
    rng = np.random.default_rng(seed)
    scenario = sample_random_start_goal(rng)
    start = scenario["start"]
    goal = scenario["goal"]
    wind_velocity = scenario["wind_velocity"]
    wind_angle = scenario["wind_angle"]
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
    fly = FlyState(position=start.copy(), heading=float(scenario["initial_heading"]))
    controller = FrozenV3CheckpointController(checkpoint_path)
    controller.reset()
    body_radius = 0.18
    records: dict[str, list[Any]] = {k: [] for k in [
        "times", "positions", "headings", "left_positions", "right_positions",
        "left_responses", "right_responses", "distances", "speeds", "omegas",
        "puff_positions", "puff_ages", "puff_strengths"
    ]}
    success = False
    boundary_contacts = 0
    max_steps = int(RANDOM_MAX_SECONDS / RANDOM_DT)
    for step_i in range(max_steps):
        left_pos, right_pos = get_antenna_positions(fly)
        left_response = float(odor_receptor_response(plume.concentration(left_pos)))
        right_response = float(odor_receptor_response(plume.concentration(right_pos)))
        forward_speed, angular_speed, _ = controller.step(
            left_response, right_response, wind_angle, fly.heading
        )
        fly.heading = wrap_angle_pi(fly.heading + angular_speed * RANDOM_DT)
        heading_vector = np.array([np.cos(fly.heading), np.sin(fly.heading)])
        proposed_position = fly.position + forward_speed * RANDOM_DT * heading_vector
        clipped_position = np.clip(proposed_position, body_radius, RANDOM_ARENA_SIZE - body_radius)
        if not np.allclose(proposed_position, clipped_position):
            boundary_contacts += 1
        fly.position = clipped_position
        plume.step(RANDOM_DT)
        distance = float(np.linalg.norm(fly.position - goal))
        if step_i % RANDOM_FRAME_STRIDE == 0:
            visual_left, visual_right = get_antenna_positions(fly)
            records["times"].append(step_i * RANDOM_DT)
            records["positions"].append(fly.position.copy())
            records["headings"].append(fly.heading)
            records["left_positions"].append(visual_left.copy())
            records["right_positions"].append(visual_right.copy())
            records["left_responses"].append(left_response)
            records["right_responses"].append(right_response)
            records["distances"].append(distance)
            records["speeds"].append(forward_speed)
            records["omegas"].append(angular_speed)
            if record_puffs:
                records["puff_positions"].append(plume.positions.copy())
                records["puff_ages"].append(plume.ages.copy())
                records["puff_strengths"].append(plume.strengths.copy())
        if distance <= SUCCESS_DISTANCE:
            success = True
            break
    result = {
        "seed": seed,
        "scenario": scenario,
        "success": bool(success),
        "boundary_contacts": int(boundary_contacts),
    }
    for key, values in records.items():
        if key.startswith("puff_"):
            result[key] = values
        else:
            result[key] = np.asarray(values)
    return result
