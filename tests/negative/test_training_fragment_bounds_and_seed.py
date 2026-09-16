"""The fragment relation must reject a chosen seed and an out-of-range Q.

Three constraints arrived together because each closes a hole the proof could
not see:

  * a prover who picks sampler_seed can grind it, running the fragment under
    many seeds and publishing the one whose transitions flatter the model --
    the proof stays valid, so what weakens is the claim, not the cryptography;
  * i64 overflow is what actually bounds a provable run, and aborting on it
    tells a verifier nothing about the range the fragment was meant to hold;
  * a declared bound wide enough to overflow gamma * q would give back exactly
    what the bound was added to remove.
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.relations.training_fragment import (
    DEFAULT_GRADIENT_CLIP_FP,
    I64_MAX,
    derive_sampler_seed,
    generate_case,
    verify_case,
)


def base_case(num_steps: int = 4):
    return generate_case(num_steps, case_id="bounds_probe_case_0")


class SamplerSeedBindingTests(unittest.TestCase):
    def test_generated_seed_is_the_derived_one(self) -> None:
        case = base_case()
        public = case["public_inputs"]
        self.assertEqual(
            int(public["sampler_seed"]),
            derive_sampler_seed(public["dataset_root"], public["global_step_start"]),
        )

    def test_a_chosen_seed_is_rejected(self) -> None:
        case = base_case()
        case["public_inputs"]["sampler_seed"] = 12_345
        result = verify_case(case)
        self.assertFalse(result.accepted)
        self.assertIn("sampler_seed", result.reason)

    def test_chunks_of_one_chain_draw_different_transitions(self) -> None:
        # The regression this guards: with a constant seed and a step index
        # local to the fragment, every chunk drew the same rows, so a
        # 1248-step chain was 156 repetitions over 8 transitions.
        first = generate_case(8, case_id="chain_c0_case_0", global_step_start=0)
        second = generate_case(8, case_id="chain_c1_case_0", global_step_start=8)
        drawn = [
            [step["sample_index"] for step in case["private_witness"]["steps"]]
            for case in (first, second)
        ]
        self.assertNotEqual(drawn[0], drawn[1])


class ValueBoundTests(unittest.TestCase):
    def test_a_q_value_over_the_declared_bound_is_rejected(self) -> None:
        case = base_case()
        # Squeeze the bound under the Q values this case already produced.
        peak = max(
            abs(int(step["intermediates"]["q_online_action"]))
            for step in case["private_witness"]["steps"]
        )
        case["public_inputs"]["q_abs_max_fp"] = max(peak - 1, 1)
        result = verify_case(case)
        self.assertFalse(result.accepted)

    def test_a_bound_that_admits_overflow_is_rejected(self) -> None:
        case = base_case()
        gamma = int(case["public_inputs"]["gamma"])
        case["public_inputs"]["q_abs_max_fp"] = I64_MAX // gamma + 1
        result = verify_case(case)
        self.assertFalse(result.accepted)
        self.assertIn("overflow", result.reason)

    def test_a_non_positive_bound_is_rejected(self) -> None:
        for bad in (0, -1):
            with self.subTest(bound=bad):
                case = base_case()
                case["public_inputs"]["q_abs_max_fp"] = bad
                self.assertFalse(verify_case(case).accepted)


class GradientClipTests(unittest.TestCase):
    def test_every_gradient_component_respects_the_clip(self) -> None:
        case = base_case()
        limit = int(case["public_inputs"]["gradient_clip_fp"])
        self.assertEqual(limit, DEFAULT_GRADIENT_CLIP_FP)
        for step in case["private_witness"]["steps"]:
            for layer in step["intermediates"]["gradients"]["layers"]:
                for row in layer["weight"]:
                    for value in row:
                        self.assertLessEqual(abs(int(value)), limit)
                for value in layer["bias"]:
                    self.assertLessEqual(abs(int(value)), limit)

    def test_a_tight_clip_changes_the_resulting_checkpoint(self) -> None:
        # A clip that never binds would leave the constraint decorative.
        loose = generate_case(4, case_id="clip_loose_case_0")
        tight = generate_case(4, case_id="clip_tight_case_0", gradient_clip_fp=1)
        self.assertNotEqual(
            loose["public_inputs"]["final_checkpoint_hash"],
            tight["public_inputs"]["final_checkpoint_hash"],
        )

    def test_a_non_positive_clip_is_rejected(self) -> None:
        case = base_case()
        case["public_inputs"]["gradient_clip_fp"] = 0
        self.assertFalse(verify_case(copy.deepcopy(case)).accepted)


if __name__ == "__main__":
    unittest.main()
