"""Pin the canonical JSON that Python hashes and Rust rebuilds by hand.

The guest has no JSON encoder: every commitment is a format! string with the
keys typed out in sorted order. So the two sides agree only as long as someone
keeps the orders identical, and a mismatch does not surface until a prover
runs -- the reference passes, the guest asserts, and the run is already paid
for. These tests compare the encoder's output against the literal layout the
Rust format strings produce, which costs nothing and fails on the spot.

Update both sides together when a payload changes, and update the expected
string here so the diff shows the new bytes.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.relations.training_aggregation import config_hash_from_fragment_public
from zk_offline_dqn.relations.training_fragment import derive_sampler_seed
from zk_offline_dqn.relations.training_update import sha256_json

FRAGMENT_SHARED = ROOT / "zk_backend/training_fragment/sp1/shared/src/lib.rs"


def canonical(payload) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class SamplerSeedPayloadTests(unittest.TestCase):
    def test_payload_layout(self) -> None:
        payload = {
            "format": "training_fragment_sampler_seed_v1",
            "dataset_root": "ab",
            "global_step_start": 8,
        }
        self.assertEqual(
            canonical(payload),
            '{"dataset_root":"ab","format":"training_fragment_sampler_seed_v1",'
            '"global_step_start":8}',
        )

    def test_seed_is_the_low_64_bits_of_the_digest_mod_lcg_modulus(self) -> None:
        digest = sha256_json(
            {
                "format": "training_fragment_sampler_seed_v1",
                "dataset_root": "ab",
                "global_step_start": 8,
            }
        )
        self.assertEqual(derive_sampler_seed("ab", 8), int(digest[:16], 16) % 2**32)

    def test_the_guest_builds_the_same_payload(self) -> None:
        source = FRAGMENT_SHARED.read_text(encoding="utf-8")
        self.assertIn(
            r'{{\"dataset_root\":\"{}\",\"format\":\"training_fragment_sampler_seed_v1\",'
            r'\"global_step_start\":{}}}',
            source,
        )


class ChunkConfigPayloadTests(unittest.TestCase):
    def fragment_public(self):
        return {
            "batch_size": 1,
            "dataset_size": 128,
            "fixed_point_scale": 1000,
            "gamma": 990,
            "gradient_clip_fp": 10_000,
            "learning_rate": 10,
            "q_abs_max_fp": 2**52,
            "sampler_type": "lcg_mod_dataset_size",
            "target_sync_interval": 4,
            "target_sync_mode": "hard",
        }

    def test_config_hash_matches_the_expected_layout(self) -> None:
        expected_payload = {
            "batch_size": 1,
            "chunk_relation_id": "training_fragment_k8",
            "dataset_size": 128,
            "fixed_point_scale": 1000,
            "format": "training_aggregation_chunk_config_v2",
            "gamma": 990,
            "gradient_clip_fp": 10_000,
            "learning_rate": 10,
            "q_abs_max_fp": 2**52,
            "sampler_seed_rule": "derived_from_dataset_root_and_global_step_start",
            "sampler_type": "lcg_mod_dataset_size",
            "target_sync_interval": 4,
            "target_sync_mode": "hard",
        }
        self.assertEqual(
            config_hash_from_fragment_public(self.fragment_public(), chunk_size=8),
            sha256_json(expected_payload),
        )

    def test_the_seed_itself_is_not_hashed(self) -> None:
        # Chunks of one chain hold different seeds now, so hashing the seed
        # would make a chain's own chunks disagree on their shared config.
        base = self.fragment_public()
        first = config_hash_from_fragment_public({**base, "sampler_seed": 1}, chunk_size=8)
        second = config_hash_from_fragment_public({**base, "sampler_seed": 2}, chunk_size=8)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
