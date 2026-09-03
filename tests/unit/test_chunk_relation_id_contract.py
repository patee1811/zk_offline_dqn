"""The chunk relation id is part of config_hash, so both languages must agree.

config_hash is a public input built from a canonical JSON that names the
fragment relation a chunk cites. Python builds it with sha256_json; the guest
rebuilds it with a hand-written format string in
zk_backend/training_aggregation/sp1/shared/src/lib.rs. A one-byte drift between
them is only caught inside the guest, at prove time, on a rented machine. These
tests pin the Python side and the literal the Rust side has to match.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from zk_offline_dqn.relations.training_fragment import generate_case as generate_fragment_case
from zk_offline_dqn.relations.training_aggregation import (
    CHUNK_RELATION_ID,
    chunk_relation_id,
    config_hash_from_fragment_public,
    generate_case,
    verify_vector,
)

ROOT = Path(__file__).resolve().parents[2]
SHARED_RS = ROOT / "zk_backend" / "training_aggregation" / "sp1" / "shared" / "src" / "lib.rs"


class ChunkRelationIdTests(unittest.TestCase):
    def test_relation_id_names_the_fragment_the_chunk_cites(self) -> None:
        self.assertEqual(chunk_relation_id(8), "training_fragment_k8")
        self.assertEqual(chunk_relation_id(128), "training_fragment_k128")

    def test_default_matches_the_legacy_constant(self) -> None:
        self.assertEqual(chunk_relation_id(8), CHUNK_RELATION_ID)

    def test_config_hash_changes_with_chunk_size(self) -> None:
        fragment_public = generate_fragment_case(8)["public_inputs"]
        self.assertNotEqual(
            config_hash_from_fragment_public(fragment_public, chunk_size=8),
            config_hash_from_fragment_public(fragment_public, chunk_size=128),
        )

    def test_guest_format_string_matches_the_python_field_order(self) -> None:
        # The guest builds the same JSON by hand. If the key order or the
        # relation-id template drifts, config_hash silently diverges.
        lines = [
            line
            for line in SHARED_RS.read_text(encoding="utf-8").splitlines()
            if "training_aggregation_chunk_config_v1" in line
        ]
        self.assertEqual(len(lines), 1, "expected exactly one guest config-hash literal")
        literal = lines[0]
        self.assertIn(r'\"chunk_relation_id\":\"training_fragment_k{}\"', literal)
        expected_order = [
            "batch_size",
            "chunk_relation_id",
            "dataset_size",
            "fixed_point_scale",
            "format",
            "gamma",
            "learning_rate",
            "sampler_seed",
            "sampler_type",
            "target_sync_interval",
            "target_sync_mode",
        ]
        found = re.findall(r'\\"([a-z_]+)\\":', literal)
        self.assertEqual(found, expected_order)


class ChunkSizeCaseTests(unittest.TestCase):
    def test_cases_verify_at_every_proof_backed_chunk_size(self) -> None:
        for chunk_size in (8, 16, 32, 128):
            with self.subTest(chunk_size=chunk_size):
                case = generate_case(chunk_size * 4, chunk_size=chunk_size)
                verify_vector(case)
                public = case["public_inputs"]
                self.assertEqual(public["chunk_size"], chunk_size)
                self.assertEqual(public["chunk_relation_id"], chunk_relation_id(chunk_size))
                self.assertEqual(public["chunk_count"], 4)

    def test_chunk_spans_follow_chunk_size(self) -> None:
        case = generate_case(512, chunk_size=128)
        for chunk in case["private_witness"]["chunks"]:
            self.assertEqual(chunk["step_end"] - chunk["step_start"], 128)
            self.assertEqual(chunk["relation_id"], "training_fragment_k128")

    def test_non_positive_chunk_size_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            generate_case(32, chunk_size=0)


if __name__ == "__main__":
    unittest.main()
