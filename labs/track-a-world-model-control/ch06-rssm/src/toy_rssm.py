"""Standard-library teaching model for the Chapter 6 RSSM data-flow smoke.

This is deliberately not a neural RSSM. It exposes the prior/posterior split
without downloading a framework, model weights, or data.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable, Sequence


@dataclass(frozen=True)
class LatentState:
    """Toy belief state.

    `position` plays the role of a stochastic state corrected by observations;
    `velocity` plays the role of deterministic recurrent memory.
    """

    position: float
    velocity: float


@dataclass(frozen=True)
class Trajectory:
    actions: tuple[float, ...]
    positions: tuple[float, ...]
    observations: tuple[float, ...]


class ToyRSSM:
    """A tiny action-conditioned predict/correct state-space model."""

    def __init__(self, observation_gain: float = 0.65, velocity_gain: float = 0.18):
        if isinstance(observation_gain, bool) or not isinstance(observation_gain, (int, float)):
            raise ValueError("observation_gain must be a finite real number")
        if isinstance(velocity_gain, bool) or not isinstance(velocity_gain, (int, float)):
            raise ValueError("velocity_gain must be a finite real number")
        if not math.isfinite(observation_gain) or not math.isfinite(velocity_gain):
            raise ValueError("gains must be finite")
        if not 0.0 <= observation_gain <= 1.0:
            raise ValueError("observation_gain must be in [0, 1]")
        if not 0.0 <= velocity_gain <= 1.0:
            raise ValueError("velocity_gain must be in [0, 1]")
        self.observation_gain = observation_gain
        self.velocity_gain = velocity_gain

    def prior(self, state: LatentState, action: float) -> LatentState:
        """Predict the next state from history and action only."""

        next_velocity = 0.94 * state.velocity + 0.35 * action
        next_position = state.position + next_velocity
        return LatentState(position=next_position, velocity=next_velocity)

    def posterior(self, prior: LatentState, observation: float) -> LatentState:
        """Correct a prior state with the current observation."""

        innovation = observation - prior.position
        return LatentState(
            position=prior.position + self.observation_gain * innovation,
            velocity=prior.velocity + self.velocity_gain * innovation,
        )


def generate_trajectory(steps: int = 32, seed: int = 7) -> Trajectory:
    """Generate a tiny partially observed, action-conditioned trajectory."""

    if isinstance(steps, bool) or not isinstance(steps, int):
        raise ValueError("steps must be an integer")
    if steps < 4:
        raise ValueError("steps must be at least 4")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")

    rng = random.Random(seed)
    position = 0.0
    velocity = 0.0
    positions = [position]
    observations = [position + rng.gauss(0.0, 0.10)]
    actions: list[float] = []

    for index in range(steps - 1):
        action = 0.65 * math.sin(index / 3.0) + (0.25 if index % 9 < 3 else -0.10)
        velocity = 0.94 * velocity + 0.35 * action + rng.gauss(0.0, 0.025)
        position = position + velocity
        actions.append(action)
        positions.append(position)
        observations.append(position + rng.gauss(0.0, 0.10))

    return Trajectory(
        actions=tuple(actions),
        positions=tuple(positions),
        observations=tuple(observations),
    )


def rmse(errors: Iterable[float]) -> float:
    values = tuple(errors)
    if not values:
        raise ValueError("rmse requires at least one value")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ValueError("rmse values must be real numbers")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("rmse values must be finite")
    return math.sqrt(sum(value * value for value in values) / len(values))


def _probability_vector(values: Sequence[float], name: str) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a probability vector")
    try:
        vector = tuple(values)
    except TypeError as error:
        raise ValueError(f"{name} must be a probability vector") from error
    if len(vector) < 2:
        raise ValueError(f"{name} must contain at least two categories")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in vector):
        raise ValueError(f"{name} values must be real numbers")
    if not all(math.isfinite(value) and value > 0.0 for value in vector):
        raise ValueError(f"{name} values must be finite and strictly positive")
    if not math.isclose(sum(vector), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"{name} must sum to one")
    return tuple(float(value) for value in vector)


def categorical_kl(posterior: Sequence[float], prior: Sequence[float]) -> float:
    """Return KL(posterior || prior) in nats for a finite categorical state."""

    posterior_vector = _probability_vector(posterior, "posterior")
    prior_vector = _probability_vector(prior, "prior")
    if len(posterior_vector) != len(prior_vector):
        raise ValueError("posterior and prior must have the same number of categories")
    return sum(
        posterior_probability * math.log(posterior_probability / prior_probability)
        for posterior_probability, prior_probability in zip(posterior_vector, prior_vector)
    )


def kl_balance_diagnostic(
    prior: Sequence[float],
    posterior: Sequence[float],
    *,
    free_nats: float = 1.0,
    dynamics_scale: float = 1.0,
    representation_scale: float = 0.1,
) -> dict[str, float | str | bool]:
    """Expose Dreamer-style KL routing without pretending to compute gradients.

    Stop-gradient changes which parameters receive gradients, not the forward KL
    value. This fixture therefore reports the two gradient targets explicitly.
    """

    for name, value in (
        ("free_nats", free_nats),
        ("dynamics_scale", dynamics_scale),
        ("representation_scale", representation_scale),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a finite non-negative real number")
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be a finite non-negative real number")

    raw_kl = categorical_kl(posterior, prior)
    clamped_kl = max(raw_kl, float(free_nats))
    return {
        "raw_kl_nats": raw_kl,
        "free_nats": float(free_nats),
        "dynamics_loss_nats": clamped_kl,
        "representation_loss_nats": clamped_kl,
        "dynamics_scale": float(dynamics_scale),
        "representation_scale": float(representation_scale),
        "scaled_total_loss": dynamics_scale * clamped_kl + representation_scale * clamped_kl,
        "forward_values_equal": True,
        "dynamics_gradient_target": "prior",
        "representation_gradient_target": "posterior",
    }


def evaluate(model: ToyRSSM, trajectory: Trajectory) -> dict[str, object]:
    """Separate posterior filtering, posterior-anchored one-step prior, and open loop."""

    if not isinstance(model, ToyRSSM) or not isinstance(trajectory, Trajectory):
        raise ValueError("model and trajectory must use the declared fixture contract")
    if any(
        not isinstance(values, tuple)
        for values in (trajectory.actions, trajectory.positions, trajectory.observations)
    ):
        raise ValueError("trajectory actions, positions, and observations must be tuples")
    if (
        len(trajectory.positions) < 2
        or len(trajectory.observations) != len(trajectory.positions)
        or len(trajectory.actions) != len(trajectory.positions) - 1
    ):
        raise ValueError("trajectory lengths must describe adjacent state transitions")
    values = trajectory.actions + trajectory.positions + trajectory.observations
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ValueError("trajectory values must be real numbers")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("trajectory values must be finite")

    def rollout_metrics(observations: tuple[float, ...]) -> dict[str, object]:
        initial = LatentState(position=observations[0], velocity=0.0)
        filtered = initial
        open_loop = initial
        filtering_errors: list[float] = []
        posterior_anchored_prior_errors: list[float] = []
        open_loop_errors: list[float] = []
        persistence_errors: list[float] = []

        for index, action in enumerate(trajectory.actions, start=1):
            filtered_prior = model.prior(filtered, action)
            truth = trajectory.positions[index]
            posterior_anchored_prior_errors.append(filtered_prior.position - truth)
            filtered = model.posterior(filtered_prior, observations[index])
            open_loop = model.prior(open_loop, action)
            filtering_errors.append(filtered.position - truth)
            open_loop_errors.append(open_loop.position - truth)
            persistence_errors.append(observations[index - 1] - truth)

        horizons = tuple(
            horizon
            for horizon in (1, 4, 8, 16, len(open_loop_errors))
            if 1 <= horizon <= len(open_loop_errors)
        )
        return {
            "steps": len(trajectory.positions),
            "filtering_rmse": rmse(filtering_errors),
            "posterior_anchored_one_step_prior_rmse": rmse(posterior_anchored_prior_errors),
            "open_loop_rmse": rmse(open_loop_errors),
            "persistence_rmse": rmse(persistence_errors),
            "open_loop_absolute_error_by_horizon": {
                f"h{horizon}": abs(open_loop_errors[horizon - 1]) for horizon in dict.fromkeys(horizons)
            },
        }

    baseline = rollout_metrics(trajectory.observations)
    offset = 1.0
    shifted_observations = (
        trajectory.observations[0],
        *(value + offset for value in trajectory.observations[1:]),
    )
    shifted = rollout_metrics(shifted_observations)

    return {
        "rollout": baseline,
        "future_observation_visibility_audit": {
            "future_observation_offset": offset,
            "open_loop_rmse_baseline": baseline["open_loop_rmse"],
            "open_loop_rmse_shifted": shifted["open_loop_rmse"],
            "posterior_anchored_one_step_prior_rmse_baseline": baseline[
                "posterior_anchored_one_step_prior_rmse"
            ],
            "posterior_anchored_one_step_prior_rmse_shifted": shifted[
                "posterior_anchored_one_step_prior_rmse"
            ],
            "filtering_rmse_baseline": baseline["filtering_rmse"],
            "filtering_rmse_shifted": shifted["filtering_rmse"],
            "scope": (
                "authored offset to observations after initialization; proves metric visibility only, "
                "not learned posterior leakage frequency or model performance"
            ),
        },
        "kl_balance": {
            "small_mismatch": kl_balance_diagnostic((0.55, 0.45), (0.5, 0.5)),
            "large_mismatch": kl_balance_diagnostic((0.99, 0.01), (0.5, 0.5)),
        },
    }
