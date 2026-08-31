"""Standard-library teaching model for the Chapter 6 RSSM data-flow smoke.

This is deliberately not a neural RSSM. It exposes the prior/posterior split
without downloading a framework, model weights, or data.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable


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

    if steps < 4:
        raise ValueError("steps must be at least 4")

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
    return math.sqrt(sum(value * value for value in values) / len(values))


def evaluate(model: ToyRSSM, trajectory: Trajectory) -> dict[str, float | int]:
    """Compare observation-corrected filtering and open-loop priors."""

    initial = LatentState(position=trajectory.observations[0], velocity=0.0)
    filtered = initial
    open_loop = initial

    filtering_errors: list[float] = []
    open_loop_errors: list[float] = []
    persistence_errors: list[float] = []

    for index, action in enumerate(trajectory.actions, start=1):
        filtered_prior = model.prior(filtered, action)
        filtered = model.posterior(filtered_prior, trajectory.observations[index])
        open_loop = model.prior(open_loop, action)

        truth = trajectory.positions[index]
        filtering_errors.append(filtered.position - truth)
        open_loop_errors.append(open_loop.position - truth)
        persistence_errors.append(trajectory.observations[index - 1] - truth)

    return {
        "steps": len(trajectory.positions),
        "filtering_rmse": rmse(filtering_errors),
        "open_loop_rmse": rmse(open_loop_errors),
        "persistence_rmse": rmse(persistence_errors),
    }
