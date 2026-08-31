from __future__ import annotations

from pathlib import Path
import sys
import unittest


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from toy_rssm import LatentState, ToyRSSM, evaluate, generate_trajectory  # noqa: E402


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
        self.assertGreater(first["open_loop_rmse"], first["filtering_rmse"])


if __name__ == "__main__":
    unittest.main()
