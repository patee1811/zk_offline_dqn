"""The SGD column of Table 1 has to be the configuration the relation proves.

Reporting Adam-only numbers would describe a training run the proof system
cannot express: `one_step_update` applies `post = pre - learning_rate * grad`
and checks `encode_fp(learning_rate) == learning_rate_fp`, so the rate has to
survive fixed-point encoding at FP_SCALE=1000.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.rl_benchmarks.agents import (
    PROVED_SGD_LEARNING_RATE,
    _make_optimizer,
)
from zk_offline_dqn.zk_specs import SPECS, decode_fp, encode_fp


class ProvedOptimizerAxisTests(unittest.TestCase):
    def test_proved_learning_rate_survives_fixed_point_encoding(self) -> None:
        encoded = encode_fp(PROVED_SGD_LEARNING_RATE)
        self.assertEqual(encoded, 10)
        self.assertEqual(decode_fp(encoded), PROVED_SGD_LEARNING_RATE)

    def test_adam_default_rate_cannot_be_expressed_at_all(self) -> None:
        # 3e-4 is the learning_rate default every baseline in Table 1 trains
        # under. It encodes to zero, which is why the Adam column reports a
        # configuration outside what the relation can verify.
        self.assertEqual(encode_fp(3e-4), 0)
        self.assertEqual(1.0 / SPECS.FP_SCALE, 0.001)

    def test_sgd_variant_is_plain_gradient_descent(self) -> None:
        parameters = [torch.zeros(2, requires_grad=True)]
        optimizer = _make_optimizer(parameters, "sgd", learning_rate=3e-4)
        self.assertIsInstance(optimizer, torch.optim.SGD)
        group = optimizer.param_groups[0]
        # The relation has no momentum, weight decay or Nesterov term to check
        # against, so an SGD carrying any of them would not be what it proves.
        self.assertEqual(group["lr"], PROVED_SGD_LEARNING_RATE)
        self.assertEqual(group["momentum"], 0)
        self.assertEqual(group["weight_decay"], 0)
        self.assertFalse(group["nesterov"])

    def test_adam_variant_still_honours_the_caller_rate(self) -> None:
        parameters = [torch.zeros(2, requires_grad=True)]
        optimizer = _make_optimizer(parameters, "adam", learning_rate=3e-4)
        self.assertIsInstance(optimizer, torch.optim.Adam)
        self.assertEqual(optimizer.param_groups[0]["lr"], 3e-4)

    def test_unknown_optimizer_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _make_optimizer([torch.zeros(1, requires_grad=True)], "rmsprop", 1e-3)


if __name__ == "__main__":
    unittest.main()
