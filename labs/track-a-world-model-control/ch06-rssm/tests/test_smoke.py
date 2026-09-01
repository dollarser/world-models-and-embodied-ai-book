from __future__ import annotations

from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from toy_rssm import (  # noqa: E402
    LatentState,
    ToyRSSM,
    categorical_kl,
    evaluate,
    generate_trajectory,
    kl_balance_diagnostic,
    rmse,
)


class ToyRSSMTest(unittest.TestCase):
    def test_prior_depends_on_action(self) -> None:
        model = ToyRSSM()
        state = LatentState(position=1.0, velocity=0.2)
        left = model.prior(state, action=-1.0)
        right = model.prior(state, action=1.0)
        self.assertNotEqual(left, right)
        self.assertLess(left.position, right.position)

    def test_posterior_moves_toward_observation(self) -> None:
        model = ToyRSSM()
        prior = LatentState(position=0.0, velocity=0.0)
        posterior = model.posterior(prior, observation=2.0)
        self.assertGreater(posterior.position, prior.position)
        self.assertLess(posterior.position, 2.0)

    def test_fixture_is_deterministic_and_exposes_rollout_gap(self) -> None:
        model = ToyRSSM()
        first = evaluate(model, generate_trajectory(steps=32, seed=7))
        second = evaluate(model, generate_trajectory(steps=32, seed=7))
        self.assertEqual(first, second)
        self.assertGreater(first["rollout"]["open_loop_rmse"], first["rollout"]["filtering_rmse"])

    def test_kl_is_zero_for_matching_categorical_states(self) -> None:
        self.assertAlmostEqual(categorical_kl((0.25, 0.75), (0.25, 0.75)), 0.0)

    def test_free_nats_clamps_small_but_not_large_mismatch(self) -> None:
        result = evaluate(ToyRSSM(), generate_trajectory())
        small = result["kl_balance"]["small_mismatch"]
        large = result["kl_balance"]["large_mismatch"]
        self.assertLess(small["raw_kl_nats"], small["free_nats"])
        self.assertEqual(small["dynamics_loss_nats"], 1.0)
        self.assertGreater(large["raw_kl_nats"], large["free_nats"])
        self.assertEqual(large["dynamics_loss_nats"], large["raw_kl_nats"])

    def test_stop_gradient_routes_share_forward_value_but_not_target(self) -> None:
        result = kl_balance_diagnostic((0.8, 0.2), (0.5, 0.5), free_nats=0.0)
        self.assertEqual(result["dynamics_loss_nats"], result["representation_loss_nats"])
        self.assertEqual(result["dynamics_gradient_target"], "prior")
        self.assertEqual(result["representation_gradient_target"], "posterior")

    def test_invalid_probability_vectors_are_rejected(self) -> None:
        for posterior, prior in (
            ((0.5, 0.5), (1.0,)),
            ((0.5, 0.4), (0.5, 0.5)),
            ((0.5, True), (0.5, 0.5)),
            ((0.5, 0.5), (0.0, 1.0)),
            ((0.5, 0.5), (float("nan"), 0.5)),
        ):
            with self.subTest(posterior=posterior, prior=prior), self.assertRaises(ValueError):
                categorical_kl(posterior, prior)

    def test_invalid_free_nats_and_scales_are_rejected(self) -> None:
        for kwargs in (
            {"free_nats": -1.0},
            {"free_nats": True},
            {"dynamics_scale": float("inf")},
            {"representation_scale": -0.1},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                kl_balance_diagnostic((0.5, 0.5), (0.5, 0.5), **kwargs)

    def test_invalid_gains_steps_seed_and_rmse_values_are_rejected(self) -> None:
        for kwargs in (
            {"observation_gain": True},
            {"observation_gain": float("nan")},
            {"velocity_gain": float("inf")},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ToyRSSM(**kwargs)
        for kwargs in ({"steps": True}, {"steps": 3.5}, {"seed": False}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                generate_trajectory(**kwargs)
        for values in ((), (True,), (float("nan"),)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                rmse(values)


if __name__ == "__main__":
    unittest.main()
