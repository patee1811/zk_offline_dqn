# zk_offline_dqn/sampling_rules.py

import random
from typing import List


SAMPLING_RULE_CONTIGUOUS_DETERMINISTIC = "contiguous_deterministic"
SAMPLING_RULE_SEEDED_PERMUTATION = "seeded_permutation"

SUPPORTED_SAMPLING_RULES = {
    SAMPLING_RULE_CONTIGUOUS_DETERMINISTIC,
    SAMPLING_RULE_SEEDED_PERMUTATION,
}


def expected_contiguous_batch_indices(
    step_idx: int,
    batch_size: int,
    start_offset: int = 0,
) -> List[int]:
    if batch_size <= 0:
        raise ValueError("batch_size must be > 0")

    if step_idx < 0:
        raise ValueError("step_idx must be >= 0")

    start = start_offset + step_idx * batch_size
    return list(range(start, start + batch_size))


def seeded_permutation_indices(
    dataset_size: int,
    sampling_seed: int,
) -> List[int]:
    if dataset_size <= 0:
        raise ValueError("dataset_size must be > 0")

    rng = random.Random(int(sampling_seed))
    indices = list(range(dataset_size))
    rng.shuffle(indices)

    return indices


def expected_seeded_permutation_batch_indices(
    step_idx: int,
    batch_size: int,
    dataset_size: int,
    sampling_seed: int,
) -> List[int]:
    if batch_size <= 0:
        raise ValueError("batch_size must be > 0")

    if step_idx < 0:
        raise ValueError("step_idx must be >= 0")

    total_required = (step_idx + 1) * batch_size

    if total_required > dataset_size:
        raise ValueError(
            "seeded_permutation does not currently support wrap-around. "
            f"Need {(step_idx + 1) * batch_size} samples, "
            f"but dataset_size={dataset_size}."
        )

    permutation = seeded_permutation_indices(
        dataset_size=dataset_size,
        sampling_seed=sampling_seed,
    )

    start = step_idx * batch_size
    end = start + batch_size

    return permutation[start:end]


def expected_batch_indices_for_rule(
    sampling_rule_type: str,
    step_idx: int,
    batch_size: int,
    start_offset: int = 0,
    dataset_size: int | None = None,
    sampling_seed: int | None = None,
) -> List[int]:
    if sampling_rule_type == SAMPLING_RULE_CONTIGUOUS_DETERMINISTIC:
        return expected_contiguous_batch_indices(
            step_idx=step_idx,
            batch_size=batch_size,
            start_offset=start_offset,
        )

    if sampling_rule_type == SAMPLING_RULE_SEEDED_PERMUTATION:
        if dataset_size is None:
            raise ValueError("dataset_size is required for seeded_permutation")

        if sampling_seed is None:
            raise ValueError("sampling_seed is required for seeded_permutation")

        return expected_seeded_permutation_batch_indices(
            step_idx=step_idx,
            batch_size=batch_size,
            dataset_size=dataset_size,
            sampling_seed=sampling_seed,
        )

    raise ValueError(
        f"Unsupported sampling_rule_type={sampling_rule_type!r}. "
        f"Supported rules: {sorted(SUPPORTED_SAMPLING_RULES)}"
    )