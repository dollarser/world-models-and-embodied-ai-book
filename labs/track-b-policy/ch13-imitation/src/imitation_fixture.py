"""Deterministic fixtures for imitation-learning evaluation contracts."""

from __future__ import annotations

from math import sqrt


def compounding_error(horizon: int = 20, action_bias: float = 0.02) -> dict[str, float]:
    """Compare teacher-forced action error with its integrated rollout effect."""
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    errors = [action_bias] * horizon
    state = sum(errors)
    return {
        "horizon": horizon,
        "open_loop_action_rmse": sqrt(sum(error * error for error in errors) / horizon),
        "closed_loop_final_state_error": abs(state),
        "amplification_factor": abs(state) / abs(action_bias) if action_bias else 0.0,
    }


def chunk_tradeoff(horizon: int = 16, chunk_sizes: tuple[int, ...] = (1, 4, 8)) -> list[dict[str, float]]:
    """Measure planning calls and stale-action delay for every perturbation time."""
    if horizon <= 1:
        raise ValueError("horizon must exceed one step")
    rows = []
    perturbation_steps = range(1, horizon)
    for chunk_size in chunk_sizes:
        if chunk_size <= 0:
            raise ValueError("chunk sizes must be positive")
        delays = [(chunk_size - (step % chunk_size)) % chunk_size for step in perturbation_steps]
        rows.append(
            {
                "chunk_size": chunk_size,
                "planning_calls": (horizon + chunk_size - 1) // chunk_size,
                "mean_reaction_delay_steps": sum(delays) / len(delays),
                "max_reaction_delay_steps": max(delays),
                "deadline_pass_rate": sum(delay <= 2 for delay in delays) / len(delays),
            }
        )
    return rows


def evaluate() -> dict[str, object]:
    return {
        "compounding_error": compounding_error(),
        "chunk_tradeoff": chunk_tradeoff(),
    }
