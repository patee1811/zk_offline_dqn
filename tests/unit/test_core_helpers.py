import unittest

from zk_offline_dqn.core import merkle, td_arithmetic


class CoreHelperTests(unittest.TestCase):
    def test_fixed_point_td_helpers_are_deterministic(self):
        reward_fp = td_arithmetic.encode_fp(1.0)
        q_target_max_fp = td_arithmetic.encode_fp(0.769)

        self.assertEqual(td_arithmetic.compute_bootstrapped_fp(q_target_max_fp), 761)
        self.assertEqual(
            td_arithmetic.compute_td_target_fp(
                reward_fp=reward_fp,
                done=0,
                q_target_max_fp=q_target_max_fp,
            ),
            1761,
        )
        self.assertEqual(
            td_arithmetic.compute_td_target_fp(
                reward_fp=reward_fp,
                done=1,
                q_target_max_fp=q_target_max_fp,
            ),
            reward_fp,
        )

    def test_merkle_helpers_accept_and_reject_deterministic_path(self):
        leaves = [
            [1000, 0, -250, 1],
            [2000, 1, 500, 0],
            [-3000, 0, 125, 1],
            [4000, 1, -750, 0],
        ]
        leaf_hashes = [merkle.hash_leaf(leaf) for leaf in leaves]
        levels = merkle.build_merkle_levels(leaf_hashes)
        path = merkle.build_merkle_path(levels, 2)
        expected_root = levels[-1][0]

        ok, recomputed_root = merkle.verify_merkle_path(
            leaf_hashes[2],
            path,
            expected_root,
        )
        self.assertTrue(ok)
        self.assertEqual(recomputed_root, expected_root)

        bad_ok, _ = merkle.verify_merkle_path(
            leaf_hashes[1],
            path,
            expected_root,
        )
        self.assertFalse(bad_ok)


if __name__ == "__main__":
    unittest.main()
