use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TdMvpInput {
    pub schema_version: String,
    pub public: PublicInputs,
    pub private: PrivateWitness,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PublicInputs {
    pub dataset_root: String,
    pub fp_scale: i64,
    pub gamma_fp: i64,
    pub loss_type: String,
    #[serde(default)]
    pub claimed_target_fp: Option<i64>,
    #[serde(default)]
    pub claimed_loss_fp: Option<i64>,
    #[serde(default)]
    pub leaf_index: Option<i64>,
    #[serde(default)]
    pub batch_size: Option<usize>,
    #[serde(default, alias = "batch_loss_fp")]
    pub claimed_batch_loss_fp: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PrivateWitness {
    #[serde(default)]
    pub transition: Option<Transition>,
    #[serde(default)]
    pub leaf: Option<Vec<i64>>,
    #[serde(default)]
    pub leaf_hash: Option<String>,
    #[serde(default)]
    pub merkle_path: Option<Vec<MerklePathStep>>,
    #[serde(default)]
    pub td_witness: Option<TdWitness>,
    #[serde(default)]
    pub items: Vec<TdMvpItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TdMvpItem {
    pub index: i64,
    pub transition: Transition,
    #[serde(alias = "serialized_leaf")]
    pub leaf: Vec<i64>,
    pub leaf_hash: String,
    pub merkle_path: Vec<MerklePathStep>,
    pub td_witness: TdWitness,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transition {
    pub obs: Vec<f64>,
    pub action: i64,
    pub reward: f64,
    pub next_obs: Vec<f64>,
    pub done: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MerklePathStep {
    pub level: i64,
    pub current_index: i64,
    pub sibling_index: i64,
    pub sibling_hash: String,
    pub current_is_left: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TdWitness {
    #[serde(default, alias = "q_online_fp")]
    pub q_online_action_fp: Option<i64>,
    #[serde(default)]
    pub next_action_online: Option<i64>,
    pub q_target_max_fp: i64,
    pub target_fp: i64,
    #[serde(default)]
    pub td_error_fp: Option<i64>,
    pub loss_fp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PublicOutput {
    pub schema_version: String,
    pub dataset_root: String,
    pub claimed_target_fp: Option<i64>,
    pub claimed_loss_fp: Option<i64>,
    pub leaf_index: Option<i64>,
    pub batch_size: Option<usize>,
    pub claimed_batch_loss_fp: Option<i64>,
    pub items: Vec<TdItemOutput>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TdItemOutput {
    pub index: i64,
    pub target_fp: i64,
    pub loss_fp: i64,
}

pub fn verify_td_mvp(input: &TdMvpInput) -> PublicOutput {
    assert!(
        input.schema_version == "td_mvp_test_vector_v1"
            || input.schema_version == "td_mvp_batch_test_vector_v1",
        "unexpected schema_version"
    );
    assert_eq!(input.public.loss_type, "smooth_l1", "unsupported loss_type");

    if input.private.items.is_empty() {
        verify_single_td_mvp(input)
    } else {
        verify_batch_td_mvp(input)
    }
}

fn verify_single_td_mvp(input: &TdMvpInput) -> PublicOutput {
    let item = TdMvpItem {
        index: input.public.leaf_index.expect("missing leaf_index"),
        transition: input
            .private
            .transition
            .clone()
            .expect("missing transition"),
        leaf: input.private.leaf.clone().expect("missing leaf"),
        leaf_hash: input.private.leaf_hash.clone().expect("missing leaf_hash"),
        merkle_path: input
            .private
            .merkle_path
            .clone()
            .expect("missing merkle_path"),
        td_witness: input
            .private
            .td_witness
            .clone()
            .expect("missing td_witness"),
    };

    let item_output = verify_td_item(&input.public, &item);
    assert_eq!(
        Some(item_output.target_fp),
        input.public.claimed_target_fp,
        "claimed_target_fp mismatch"
    );
    assert_eq!(
        Some(item_output.loss_fp),
        input.public.claimed_loss_fp,
        "claimed_loss_fp mismatch"
    );

    PublicOutput {
        schema_version: input.schema_version.clone(),
        dataset_root: input.public.dataset_root.clone(),
        claimed_target_fp: input.public.claimed_target_fp,
        claimed_loss_fp: input.public.claimed_loss_fp,
        leaf_index: input.public.leaf_index,
        batch_size: None,
        claimed_batch_loss_fp: None,
        items: vec![item_output],
    }
}

fn verify_batch_td_mvp(input: &TdMvpInput) -> PublicOutput {
    let batch_size = input.public.batch_size.expect("missing batch_size");
    assert_eq!(
        batch_size,
        input.private.items.len(),
        "batch_size does not match witness item count"
    );
    assert!(batch_size > 0, "batch_size must be positive");

    let mut total_loss_fp = 0i64;
    let mut outputs = Vec::with_capacity(input.private.items.len());

    for item in &input.private.items {
        let item_output = verify_td_item(&input.public, item);
        total_loss_fp += item_output.loss_fp;
        outputs.push(item_output);
    }

    let expected_batch_loss_fp = total_loss_fp / batch_size as i64;
    assert_eq!(
        Some(expected_batch_loss_fp),
        input.public.claimed_batch_loss_fp,
        "claimed_batch_loss_fp mismatch"
    );

    PublicOutput {
        schema_version: input.schema_version.clone(),
        dataset_root: input.public.dataset_root.clone(),
        claimed_target_fp: None,
        claimed_loss_fp: None,
        leaf_index: None,
        batch_size: Some(batch_size),
        claimed_batch_loss_fp: input.public.claimed_batch_loss_fp,
        items: outputs,
    }
}

fn verify_td_item(public: &PublicInputs, item: &TdMvpItem) -> TdItemOutput {
    if let Some(first_step) = item.merkle_path.first() {
        assert_eq!(
            first_step.current_index, item.index,
            "first Merkle path current_index does not match item index"
        );
    }

    let recomputed_leaf = serialize_transition_leaf(&item.transition, public.fp_scale);
    assert_eq!(
        item.leaf, recomputed_leaf,
        "leaf does not match canonical transition serialization"
    );

    let recomputed_leaf_hash = hash_leaf(&recomputed_leaf);
    assert_eq!(
        item.leaf_hash, recomputed_leaf_hash,
        "leaf_hash does not match canonical leaf hash"
    );

    let recomputed_root = recompute_root_from_path(&recomputed_leaf_hash, &item.merkle_path);
    assert_eq!(
        recomputed_root, public.dataset_root,
        "Merkle path does not authenticate to dataset_root"
    );

    let reward_fp = encode_fp(item.transition.reward, public.fp_scale);
    let done = item.transition.done;
    assert!(done == 0 || done == 1, "done must be 0 or 1");

    let expected_target_fp = if done == 1 {
        reward_fp
    } else {
        reward_fp
            + fixed_point_mul(
                public.gamma_fp,
                item.td_witness.q_target_max_fp,
                public.fp_scale,
            )
    };
    assert_eq!(
        item.td_witness.target_fp, expected_target_fp,
        "target_fp mismatch"
    );

    let q_online_action_fp = item
        .td_witness
        .q_online_action_fp
        .expect("missing q_online_action_fp");
    let expected_td_error_fp = q_online_action_fp - expected_target_fp;
    if let Some(td_error_fp) = item.td_witness.td_error_fp {
        assert_eq!(td_error_fp, expected_td_error_fp, "td_error_fp mismatch");
    }

    let expected_loss_fp = smooth_l1_loss_fp(expected_td_error_fp, public.fp_scale);
    assert_eq!(
        item.td_witness.loss_fp, expected_loss_fp,
        "loss_fp mismatch"
    );

    TdItemOutput {
        index: item.index,
        target_fp: item.td_witness.target_fp,
        loss_fp: item.td_witness.loss_fp,
    }
}

pub fn serialize_transition_leaf(transition: &Transition, fp_scale: i64) -> Vec<i64> {
    assert_eq!(transition.obs.len(), 4, "obs must have length 4");
    assert_eq!(transition.next_obs.len(), 4, "next_obs must have length 4");
    assert!(
        transition.action == 0 || transition.action == 1,
        "action must be 0 or 1"
    );
    assert!(
        transition.done == 0 || transition.done == 1,
        "done must be 0 or 1"
    );

    let mut leaf = Vec::with_capacity(11);
    for value in &transition.obs {
        leaf.push(encode_fp(*value, fp_scale));
    }
    leaf.push(transition.action);
    leaf.push(encode_fp(transition.reward, fp_scale));
    for value in &transition.next_obs {
        leaf.push(encode_fp(*value, fp_scale));
    }
    leaf.push(transition.done);
    leaf
}

pub fn encode_fp(value: f64, fp_scale: i64) -> i64 {
    (value * fp_scale as f64).round() as i64
}

pub fn fixed_point_mul(a_fp: i64, b_fp: i64, fp_scale: i64) -> i64 {
    (a_fp * b_fp) / fp_scale
}

pub fn smooth_l1_loss_fp(td_error_fp: i64, fp_scale: i64) -> i64 {
    let abs_x_fp = td_error_fp.abs();
    if abs_x_fp < fp_scale {
        (abs_x_fp * abs_x_fp) / (2 * fp_scale)
    } else {
        abs_x_fp - fp_scale / 2
    }
}

pub fn hash_leaf(leaf: &[i64]) -> String {
    let encoded = encode_leaf_for_hash(leaf);
    hex::encode(Sha256::digest(encoded.as_bytes()))
}

pub fn encode_leaf_for_hash(leaf: &[i64]) -> String {
    leaf.iter()
        .map(|value| value.to_string())
        .collect::<Vec<_>>()
        .join(",")
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
    let left = decode_hex_32(left_hex);
    let right = decode_hex_32(right_hex);
    let mut bytes = Vec::with_capacity(64);
    bytes.extend_from_slice(&left);
    bytes.extend_from_slice(&right);
    hex::encode(Sha256::digest(bytes))
}

fn decode_hex_32(value: &str) -> [u8; 32] {
    let bytes = hex::decode(value).expect("invalid hex");
    assert_eq!(bytes.len(), 32, "expected 32-byte hex value");
    let mut out = [0u8; 32];
    out.copy_from_slice(&bytes);
    out
}
