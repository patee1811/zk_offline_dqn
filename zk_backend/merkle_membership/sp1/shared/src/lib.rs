use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MerkleMembershipInput {
    pub schema_version: String,
    pub public_inputs: MerkleMembershipPublicInputs,
    pub private_witness: MerkleMembershipWitness,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MerkleMembershipPublicInputs {
    pub dataset_id: String,
    pub dataset_type: String,
    pub dataset_root: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: Option<String>,
    pub raw_trajectory_hash: String,
    pub leaf_hash: String,
    pub leaf_index: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MerkleMembershipWitness {
    pub merkle_path: Vec<MerklePathStep>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MerklePathStep {
    pub level: u64,
    pub current_index: u64,
    pub sibling_index: u64,
    pub sibling_hash: String,
    pub current_is_left: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MerkleMembershipOutput {
    pub schema_version: String,
    pub dataset_id: String,
    pub dataset_type: String,
    pub dataset_root: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: Option<String>,
    pub raw_trajectory_hash: String,
    pub leaf_hash: String,
    pub leaf_index: u64,
}

pub fn verify_merkle_membership(input: &MerkleMembershipInput) -> MerkleMembershipOutput {
    assert_eq!(
        input.schema_version, "sp1_merkle_membership_case_v1",
        "unexpected schema_version"
    );
    assert!(
        input.public_inputs.dataset_type == "self_collected_replay_audited"
            || input.public_inputs.dataset_type == "public_benchmark",
        "unsupported dataset_type"
    );
    assert_hex_32(&input.public_inputs.dataset_root, "dataset_root");
    assert_hex_32(&input.public_inputs.manifest_hash, "manifest_hash");
    assert_hex_32(&input.public_inputs.audit_report_hash, "audit_report_hash");
    assert_hex_32(
        &input.public_inputs.raw_trajectory_hash,
        "raw_trajectory_hash",
    );
    assert_hex_32(&input.public_inputs.leaf_hash, "leaf_hash");
    if let Some(value) = &input.public_inputs.collection_log_final_hash {
        assert_hex_32(value, "collection_log_final_hash");
    }
    if input.public_inputs.dataset_type == "self_collected_replay_audited" {
        assert!(
            input.public_inputs.collection_log_final_hash.is_some(),
            "self-collected dataset requires collection_log_final_hash"
        );
    }
    if input.public_inputs.dataset_type == "public_benchmark" {
        assert!(
            input.public_inputs.collection_log_final_hash.is_none(),
            "public benchmark must not claim collection_log_final_hash"
        );
    }

    assert_path_metadata(
        &input.private_witness.merkle_path,
        input.public_inputs.leaf_index,
    );
    let root = recompute_root_from_path(
        &input.public_inputs.leaf_hash,
        &input.private_witness.merkle_path,
    );
    assert_eq!(
        root, input.public_inputs.dataset_root,
        "Merkle path does not authenticate to dataset_root"
    );

    MerkleMembershipOutput {
        schema_version: "sp1_merkle_membership_public_v1".to_owned(),
        dataset_id: input.public_inputs.dataset_id.clone(),
        dataset_type: input.public_inputs.dataset_type.clone(),
        dataset_root: input.public_inputs.dataset_root.clone(),
        manifest_hash: input.public_inputs.manifest_hash.clone(),
        audit_report_hash: input.public_inputs.audit_report_hash.clone(),
        collection_log_final_hash: input.public_inputs.collection_log_final_hash.clone(),
        raw_trajectory_hash: input.public_inputs.raw_trajectory_hash.clone(),
        leaf_hash: input.public_inputs.leaf_hash.clone(),
        leaf_index: input.public_inputs.leaf_index,
    }
}

pub fn expected_public_output(input: &MerkleMembershipInput) -> MerkleMembershipOutput {
    MerkleMembershipOutput {
        schema_version: "sp1_merkle_membership_public_v1".to_owned(),
        dataset_id: input.public_inputs.dataset_id.clone(),
        dataset_type: input.public_inputs.dataset_type.clone(),
        dataset_root: input.public_inputs.dataset_root.clone(),
        manifest_hash: input.public_inputs.manifest_hash.clone(),
        audit_report_hash: input.public_inputs.audit_report_hash.clone(),
        collection_log_final_hash: input.public_inputs.collection_log_final_hash.clone(),
        raw_trajectory_hash: input.public_inputs.raw_trajectory_hash.clone(),
        leaf_hash: input.public_inputs.leaf_hash.clone(),
        leaf_index: input.public_inputs.leaf_index,
    }
}

fn assert_path_metadata(path: &[MerklePathStep], leaf_index: u64) {
    let mut expected_current = leaf_index;
    for (expected_level, step) in path.iter().enumerate() {
        assert_eq!(
            step.level, expected_level as u64,
            "Merkle path level metadata mismatch"
        );
        assert_eq!(
            step.current_index, expected_current,
            "Merkle path current_index metadata mismatch"
        );
        if step.current_is_left {
            assert_eq!(expected_current % 2, 0, "left path step has odd index");
            assert!(
                step.sibling_index == expected_current
                    || step.sibling_index == expected_current + 1,
                "left path sibling_index metadata mismatch"
            );
        } else {
            assert_eq!(expected_current % 2, 1, "right path step has even index");
            assert_eq!(
                step.sibling_index,
                expected_current - 1,
                "right path sibling_index metadata mismatch"
            );
        }
        assert_hex_32(&step.sibling_hash, "sibling_hash");
        expected_current /= 2;
    }
}

pub fn recompute_root_from_path(leaf_hash: &str, merkle_path: &[MerklePathStep]) -> String {
    let mut current = leaf_hash.to_owned();
    for step in merkle_path {
        current = if step.current_is_left {
            hash_internal_node(&current, &step.sibling_hash)
        } else {
            hash_internal_node(&step.sibling_hash, &current)
        };
    }
    current
}

pub fn hash_internal_node(left_hex: &str, right_hex: &str) -> String {
    let left = decode_hex_32(left_hex, "left");
    let right = decode_hex_32(right_hex, "right");
    let mut bytes = Vec::with_capacity(64);
    bytes.extend_from_slice(&left);
    bytes.extend_from_slice(&right);
    hex::encode(Sha256::digest(bytes))
}

fn assert_hex_32(value: &str, label: &str) {
    let bytes = hex::decode(value).unwrap_or_else(|_| panic!("{label} is not valid hex"));
    assert_eq!(bytes.len(), 32, "{label} must be 32 bytes");
}

fn decode_hex_32(value: &str, label: &str) -> [u8; 32] {
    let bytes = hex::decode(value).unwrap_or_else(|_| panic!("{label} is not valid hex"));
    assert_eq!(bytes.len(), 32, "{label} must be 32 bytes");
    let mut out = [0u8; 32];
    out.copy_from_slice(&bytes);
    out
}
