import importlib
import unittest

import zk_offline_dqn.commitments as old_commitments
import zk_offline_dqn.merkle as old_merkle
import zk_offline_dqn.zk_specs as old_zk_specs


class ActiveImportSurfaceTests(unittest.TestCase):
    def test_active_future_namespaces_import_normally(self):
        module_names = [
            "zk_offline_dqn.core.merkle",
            "zk_offline_dqn.core.td_arithmetic",
            "zk_offline_dqn.core.commitments",
            "zk_offline_dqn.relations",
            "zk_offline_dqn.verifiers",
            "zk_offline_dqn.artifacts",
            "zk_offline_dqn.exporters",
            "zk_offline_dqn.backends.sp1",
            "zk_offline_dqn.experiments",
            "zk_offline_dqn.cli",
        ]

        for module_name in module_names:
            with self.subTest(module_name=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_active_merkle_wrapper_matches_old_module(self):
        new_merkle = importlib.import_module("zk_offline_dqn.core.merkle")
        leaves = [
            [1000, 0, -250, 1],
            [2000, 1, 500, 0],
            [-3000, 0, 125, 1],
        ]

        old_leaf_hashes = [old_merkle.hash_leaf(leaf) for leaf in leaves]
        new_leaf_hashes = [new_merkle.hash_leaf(leaf) for leaf in leaves]
        self.assertEqual(new_leaf_hashes, old_leaf_hashes)

        old_levels = old_merkle.build_merkle_levels(old_leaf_hashes)
        new_levels = new_merkle.build_merkle_levels(new_leaf_hashes)
        self.assertEqual(new_levels, old_levels)

        old_path = old_merkle.build_merkle_path(old_levels, 1)
        new_path = new_merkle.build_merkle_path(new_levels, 1)
        self.assertEqual(new_path, old_path)

        old_ok, old_root = old_merkle.verify_merkle_path(
            old_leaf_hashes[1], old_path, old_levels[-1][0]
        )
        new_ok, new_root = new_merkle.verify_merkle_path(
            new_leaf_hashes[1], new_path, new_levels[-1][0]
        )
        self.assertEqual((new_ok, new_root), (old_ok, old_root))

    def test_active_td_arithmetic_wrapper_matches_old_module(self):
        new_td = importlib.import_module("zk_offline_dqn.core.td_arithmetic")

        self.assertEqual(new_td.SPECS, old_zk_specs.SPECS)
        self.assertEqual(new_td.FP_SCALE, old_zk_specs.SPECS.FP_SCALE)
        self.assertEqual(new_td.GAMMA_FP, old_zk_specs.SPECS.GAMMA_FP)
        self.assertEqual(
            new_td.SMOOTH_L1_BETA_FP,
            old_zk_specs.SPECS.SMOOTH_L1_BETA_FP,
        )

        for value in [-1.25, 0.0, 0.333, 2.5]:
            self.assertEqual(new_td.encode_fp(value), old_zk_specs.encode_fp(value))
            encoded = old_zk_specs.encode_fp(value)
            self.assertEqual(new_td.decode_fp(encoded), old_zk_specs.decode_fp(encoded))

        for reward_fp, done, q_target_max_fp in [(100, 0, 2000), (-250, 1, 3000)]:
            self.assertEqual(
                new_td.compute_bootstrapped_fp(q_target_max_fp),
                old_zk_specs.compute_bootstrapped_fp(q_target_max_fp),
            )
            self.assertEqual(
                new_td.compute_td_target_fp(reward_fp, done, q_target_max_fp),
                old_zk_specs.compute_td_target_fp(reward_fp, done, q_target_max_fp),
            )

        for q_online_fp, target_fp in [(1000, 990), (5000, -1000)]:
            self.assertEqual(
                new_td.compute_mse_loss_fp(q_online_fp, target_fp),
                old_zk_specs.compute_mse_loss_fp(q_online_fp, target_fp),
            )
            self.assertEqual(
                new_td.compute_smooth_l1_loss_fp(q_online_fp, target_fp),
                old_zk_specs.compute_smooth_l1_loss_fp(q_online_fp, target_fp),
            )

    def test_active_commitments_wrapper_exposes_old_public_functions(self):
        new_commitments = importlib.import_module("zk_offline_dqn.core.commitments")

        self.assertIs(
            new_commitments.canonical_state_dict_sha256,
            old_commitments.canonical_state_dict_sha256,
        )
        self.assertIs(
            new_commitments.canonical_checkpoint_state_commitments,
            old_commitments.canonical_checkpoint_state_commitments,
        )


if __name__ == "__main__":
    unittest.main()
