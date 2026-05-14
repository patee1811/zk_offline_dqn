import importlib.util
import pathlib
import unittest

import zk_offline_dqn.commitments as old_commitments
import zk_offline_dqn.merkle as old_merkle
import zk_offline_dqn.zk_specs as old_zk_specs


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def load_src_module(relative_path, module_name):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CoreWrapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new_merkle = load_src_module(
            pathlib.Path("src/zk_offline_dqn/core/merkle.py"),
            "phase1a_core_merkle",
        )
        cls.new_td = load_src_module(
            pathlib.Path("src/zk_offline_dqn/core/td_arithmetic.py"),
            "phase1a_core_td_arithmetic",
        )
        cls.new_commitments = load_src_module(
            pathlib.Path("src/zk_offline_dqn/core/commitments.py"),
            "phase1a_core_commitments",
        )

    def test_merkle_wrapper_matches_old_module(self):
        leaves = [
            [1000, 0, -250, 1],
            [2000, 1, 500, 0],
            [-3000, 0, 125, 1],
        ]

        old_leaf_hashes = [old_merkle.hash_leaf(leaf) for leaf in leaves]
        new_leaf_hashes = [self.new_merkle.hash_leaf(leaf) for leaf in leaves]
        self.assertEqual(new_leaf_hashes, old_leaf_hashes)

        old_levels = old_merkle.build_merkle_levels(old_leaf_hashes)
        new_levels = self.new_merkle.build_merkle_levels(new_leaf_hashes)
        self.assertEqual(new_levels, old_levels)

        old_path = old_merkle.build_merkle_path(old_levels, 1)
        new_path = self.new_merkle.build_merkle_path(new_levels, 1)
        self.assertEqual(new_path, old_path)

        old_ok, old_root = old_merkle.verify_merkle_path(
            old_leaf_hashes[1], old_path, old_levels[-1][0]
        )
        new_ok, new_root = self.new_merkle.verify_merkle_path(
            new_leaf_hashes[1], new_path, new_levels[-1][0]
        )
        self.assertEqual((new_ok, new_root), (old_ok, old_root))

    def test_td_arithmetic_wrapper_matches_old_module(self):
        self.assertEqual(self.new_td.SPECS, old_zk_specs.SPECS)
        self.assertEqual(self.new_td.FP_SCALE, old_zk_specs.SPECS.FP_SCALE)
        self.assertEqual(self.new_td.GAMMA_FP, old_zk_specs.SPECS.GAMMA_FP)
        self.assertEqual(
            self.new_td.SMOOTH_L1_BETA_FP,
            old_zk_specs.SPECS.SMOOTH_L1_BETA_FP,
        )

        for value in [-1.25, 0.0, 0.333, 2.5]:
            self.assertEqual(self.new_td.encode_fp(value), old_zk_specs.encode_fp(value))
            encoded = old_zk_specs.encode_fp(value)
            self.assertEqual(self.new_td.decode_fp(encoded), old_zk_specs.decode_fp(encoded))

        td_cases = [
            (100, 0, 2000),
            (-250, 1, 3000),
            (0, 0, -1500),
        ]
        for reward_fp, done, q_target_max_fp in td_cases:
            self.assertEqual(
                self.new_td.compute_bootstrapped_fp(q_target_max_fp),
                old_zk_specs.compute_bootstrapped_fp(q_target_max_fp),
            )
            self.assertEqual(
                self.new_td.compute_td_target_fp(reward_fp, done, q_target_max_fp),
                old_zk_specs.compute_td_target_fp(reward_fp, done, q_target_max_fp),
            )

        loss_cases = [
            (1000, 990),
            (5000, -1000),
            (-100, 250),
        ]
        for q_online_fp, target_fp in loss_cases:
            self.assertEqual(
                self.new_td.compute_mse_loss_fp(q_online_fp, target_fp),
                old_zk_specs.compute_mse_loss_fp(q_online_fp, target_fp),
            )
            self.assertEqual(
                self.new_td.compute_smooth_l1_loss_fp(q_online_fp, target_fp),
                old_zk_specs.compute_smooth_l1_loss_fp(q_online_fp, target_fp),
            )

    def test_commitments_wrapper_imports_same_public_functions(self):
        self.assertIs(
            self.new_commitments.canonical_state_dict_sha256,
            old_commitments.canonical_state_dict_sha256,
        )
        self.assertIs(
            self.new_commitments.canonical_checkpoint_state_commitments,
            old_commitments.canonical_checkpoint_state_commitments,
        )


if __name__ == "__main__":
    unittest.main()
