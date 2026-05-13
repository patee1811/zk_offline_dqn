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
    #[serde(default)]
    pub batch_mode: Option<String>,
    #[serde(default)]
    pub leaf_indices: Option<Vec<i64>>,
    #[serde(default, alias = "batch_loss_fp")]
    pub claimed_batch_loss_fp: Option<i64>,
    #[serde(default)]
    pub network_spec_hash: Option<String>,
    #[serde(default)]
    pub network_layer_sizes: Option<Vec<usize>>,
    #[serde(default)]
    pub online_model_commitment: Option<String>,
    #[serde(default)]
    pub target_model_commitment: Option<String>,
    #[serde(default)]
    pub claimed_item_losses_fp: Option<Vec<i64>>,
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
    #[serde(default)]
    pub online_model: Option<QuantizedMlp>,
    #[serde(default)]
    pub target_model: Option<QuantizedMlp>,
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
    #[serde(default)]
    pub forward_witness: Option<ForwardWitness>,
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
    pub leaf_indices: Option<Vec<i64>>,
    pub claimed_batch_loss_fp: Option<i64>,
    pub items: Vec<TdItemOutput>,
    pub network_spec_hash: Option<String>,
    pub online_model_commitment: Option<String>,
    pub target_model_commitment: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TdItemOutput {
    pub index: i64,
    pub target_fp: i64,
    pub loss_fp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuantizedMlp {
    pub format: String,
    pub layer_sizes: Vec<usize>,
    pub fp_scale: i64,
    pub layers: Vec<QuantizedLayer>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuantizedLayer {
    pub weight: Vec<Vec<i64>>,
    pub bias: Vec<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ForwardWitness {
    pub online_obs: ForwardTrace,
    pub online_next: ForwardTrace,
    pub target_next: ForwardTrace,
    pub q_online_action_fp: i64,
    pub next_action_online: i64,
    pub q_target_max_fp: i64,
    pub target_fp: i64,
    pub td_error_fp: i64,
    pub loss_fp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ForwardTrace {
    pub pre_activations: Vec<Vec<i64>>,
    pub relu_masks: Vec<Vec<i64>>,
    pub outputs: Vec<i64>,
}

pub fn verify_td_mvp(input: &TdMvpInput) -> PublicOutput {
    assert!(
        input.schema_version == "td_mvp_test_vector_v1"
            || input.schema_version == "td_mvp_batch_test_vector_v1"
            || input.schema_version == "forward_td_mlp_v1",
        "unexpected schema_version"
    );
    assert_eq!(input.public.loss_type, "smooth_l1", "unsupported loss_type");

    if input.schema_version == "forward_td_mlp_v1" {
        return verify_forward_td_mlp(input);
    }

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
        leaf_indices: None,
        claimed_batch_loss_fp: None,
        items: vec![item_output],
        network_spec_hash: None,
        online_model_commitment: None,
        target_model_commitment: None,
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

    if let Some(leaf_indices) = &input.public.leaf_indices {
        assert_eq!(
            leaf_indices.len(),
            batch_size,
            "leaf_indices length does not match batch_size"
        );
        assert_distinct_i64(leaf_indices);
    }

    let mut total_loss_fp = 0i64;
    let mut outputs = Vec::with_capacity(input.private.items.len());

    for (position, item) in input.private.items.iter().enumerate() {
        if let Some(leaf_indices) = &input.public.leaf_indices {
            assert_eq!(
                item.index, leaf_indices[position],
                "item index does not match public leaf_indices order"
            );
        }
        let item_output = verify_td_item(&input.public, item);
        total_loss_fp += item_output.loss_fp;
        outputs.push(item_output);
    }
    if input.public.batch_mode.as_deref() == Some("distinct") && input.public.leaf_indices.is_none()
    {
        let indices = input
            .private
            .items
            .iter()
            .map(|item| item.index)
            .collect::<Vec<_>>();
        assert_distinct_i64(&indices);
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
        leaf_indices: input.public.leaf_indices.clone(),
        claimed_batch_loss_fp: input.public.claimed_batch_loss_fp,
        items: outputs,
        network_spec_hash: None,
        online_model_commitment: None,
        target_model_commitment: None,
    }
}

fn verify_forward_td_mlp(input: &TdMvpInput) -> PublicOutput {
    let batch_size = input.public.batch_size.expect("missing batch_size");
    assert!(batch_size > 0, "batch_size must be positive");
    assert_eq!(
        batch_size,
        input.private.items.len(),
        "batch_size does not match witness item count"
    );

    let leaf_indices = input
        .public
        .leaf_indices
        .clone()
        .expect("missing leaf_indices");
    assert_eq!(
        leaf_indices.len(),
        batch_size,
        "leaf_indices length does not match batch_size"
    );
    assert_distinct_i64(&leaf_indices);

    let claimed_item_losses = input
        .public
        .claimed_item_losses_fp
        .clone()
        .expect("missing claimed_item_losses_fp");
    assert_eq!(
        claimed_item_losses.len(),
        batch_size,
        "claimed_item_losses_fp length mismatch"
    );

    let network_layer_sizes = input
        .public
        .network_layer_sizes
        .clone()
        .expect("missing network_layer_sizes");
    assert_eq!(
        Some(network_spec_hash(&network_layer_sizes, input.public.fp_scale)),
        input.public.network_spec_hash,
        "network_spec_hash mismatch"
    );

    let online_model = input
        .private
        .online_model
        .as_ref()
        .expect("missing online_model");
    let target_model = input
        .private
        .target_model
        .as_ref()
        .expect("missing target_model");
    assert_valid_model(online_model, &network_layer_sizes, input.public.fp_scale);
    assert_valid_model(target_model, &network_layer_sizes, input.public.fp_scale);
    assert_eq!(
        Some(model_commitment(online_model, input.public.fp_scale)),
        input.public.online_model_commitment,
        "online_model_commitment mismatch"
    );
    assert_eq!(
        Some(model_commitment(target_model, input.public.fp_scale)),
        input.public.target_model_commitment,
        "target_model_commitment mismatch"
    );

    let mut total_loss_fp = 0i64;
    let mut outputs = Vec::with_capacity(input.private.items.len());

    for (position, item) in input.private.items.iter().enumerate() {
        assert_eq!(
            item.index, leaf_indices[position],
            "item index does not match public leaf_indices order"
        );
        verify_membership_only(&input.public, item);
        let output = verify_forward_item(
            &input.public,
            item,
            online_model,
            target_model,
            claimed_item_losses[position],
        );
        total_loss_fp += output.loss_fp;
        outputs.push(output);
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
        leaf_indices: Some(leaf_indices),
        claimed_batch_loss_fp: input.public.claimed_batch_loss_fp,
        items: outputs,
        network_spec_hash: input.public.network_spec_hash.clone(),
        online_model_commitment: input.public.online_model_commitment.clone(),
        target_model_commitment: input.public.target_model_commitment.clone(),
    }
}

fn verify_membership_only(public: &PublicInputs, item: &TdMvpItem) {
    if let Some(first_step) = item.merkle_path.first() {
        assert_eq!(
            first_step.current_index, item.index,
            "first Merkle path current_index does not match item index"
        );
    }
    assert_merkle_path_metadata(&item.merkle_path, item.index);

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
}

fn verify_forward_item(
    public: &PublicInputs,
    item: &TdMvpItem,
    online_model: &QuantizedMlp,
    target_model: &QuantizedMlp,
    claimed_item_loss_fp: i64,
) -> TdItemOutput {
    let witness = item
        .forward_witness
        .as_ref()
        .expect("missing forward_witness");

    let obs_fp = item
        .transition
        .obs
        .iter()
        .map(|value| encode_fp(*value, public.fp_scale))
        .collect::<Vec<_>>();
    let next_obs_fp = item
        .transition
        .next_obs
        .iter()
        .map(|value| encode_fp(*value, public.fp_scale))
        .collect::<Vec<_>>();

    let online_obs = mlp_forward(online_model, &obs_fp, public.fp_scale);
    let online_next = mlp_forward(online_model, &next_obs_fp, public.fp_scale);
    let target_next = mlp_forward(target_model, &next_obs_fp, public.fp_scale);
    assert_trace_eq(&witness.online_obs, &online_obs, "online_obs");
    assert_trace_eq(&witness.online_next, &online_next, "online_next");
    assert_trace_eq(&witness.target_next, &target_next, "target_next");

    let action = item.transition.action as usize;
    assert!(action < online_obs.outputs.len(), "action out of range");
    let q_online_action_fp = online_obs.outputs[action];
    assert_eq!(
        witness.q_online_action_fp, q_online_action_fp,
        "q_online_action_fp mismatch"
    );

    let next_action_online = argmax_first(&online_next.outputs) as i64;
    assert_eq!(
        witness.next_action_online, next_action_online,
        "next_action_online mismatch"
    );

    let next_action_usize = next_action_online as usize;
    assert!(
        next_action_usize < target_next.outputs.len(),
        "next_action_online out of target output range"
    );
    let q_target_max_fp = target_next.outputs[next_action_usize];
    assert_eq!(
        witness.q_target_max_fp, q_target_max_fp,
        "q_target_max_fp mismatch"
    );

    let reward_fp = encode_fp(item.transition.reward, public.fp_scale);
    let done = item.transition.done;
    assert!(done == 0 || done == 1, "done must be 0 or 1");
    let expected_target_fp = if done == 1 {
        reward_fp
    } else {
        reward_fp + fixed_point_mul(public.gamma_fp, q_target_max_fp, public.fp_scale)
    };
    assert_eq!(
        witness.target_fp, expected_target_fp,
        "forward target_fp mismatch"
    );

    let td_error_fp = q_online_action_fp - expected_target_fp;
    assert_eq!(witness.td_error_fp, td_error_fp, "td_error_fp mismatch");
    let loss_fp = smooth_l1_loss_fp(td_error_fp, public.fp_scale);
    assert_eq!(witness.loss_fp, loss_fp, "loss_fp mismatch");
    assert_eq!(
        claimed_item_loss_fp, loss_fp,
        "claimed item loss does not match recomputation"
    );

    TdItemOutput {
        index: item.index,
        target_fp: expected_target_fp,
        loss_fp,
    }
}

fn verify_td_item(public: &PublicInputs, item: &TdMvpItem) -> TdItemOutput {
    if let Some(first_step) = item.merkle_path.first() {
        assert_eq!(
            first_step.current_index, item.index,
            "first Merkle path current_index does not match item index"
        );
    }
    assert_merkle_path_metadata(&item.merkle_path, item.index);

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

fn assert_distinct_i64(values: &[i64]) {
    for left in 0..values.len() {
        for right in (left + 1)..values.len() {
            assert_ne!(values[left], values[right], "duplicate leaf index");
        }
    }
}

fn assert_merkle_path_metadata(merkle_path: &[MerklePathStep], leaf_index: i64) {
    let mut expected_current_index = leaf_index;

    for (expected_level, step) in merkle_path.iter().enumerate() {
        assert_eq!(
            step.level, expected_level as i64,
            "Merkle path level metadata mismatch"
        );
        assert_eq!(
            step.current_index, expected_current_index,
            "Merkle path current_index metadata mismatch"
        );

        if step.current_is_left {
            assert_eq!(
                expected_current_index % 2,
                0,
                "left Merkle path step has odd current_index"
            );
            assert!(
                step.sibling_index == expected_current_index
                    || step.sibling_index == expected_current_index + 1,
                "left Merkle path sibling_index metadata mismatch"
            );
        } else {
            assert_eq!(
                expected_current_index % 2,
                1,
                "right Merkle path step has even current_index"
            );
            assert_eq!(
                step.sibling_index,
                expected_current_index - 1,
                "right Merkle path sibling_index metadata mismatch"
            );
        }

        expected_current_index /= 2;
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

fn assert_valid_model(model: &QuantizedMlp, layer_sizes: &[usize], fp_scale: i64) {
    assert_eq!(model.format, "quantized_mlp_v1", "unexpected model format");
    assert_eq!(model.fp_scale, fp_scale, "model fp_scale mismatch");
    assert_eq!(model.layer_sizes, layer_sizes, "model layer_sizes mismatch");
    assert_eq!(
        model.layers.len(),
        layer_sizes.len() - 1,
        "model layer count mismatch"
    );
    for (idx, layer) in model.layers.iter().enumerate() {
        let in_dim = layer_sizes[idx];
        let out_dim = layer_sizes[idx + 1];
        assert_eq!(layer.weight.len(), out_dim, "layer out_dim mismatch");
        assert_eq!(layer.bias.len(), out_dim, "layer bias length mismatch");
        for row in &layer.weight {
            assert_eq!(row.len(), in_dim, "layer in_dim mismatch");
        }
    }
}

fn mlp_forward(model: &QuantizedMlp, input_fp: &[i64], fp_scale: i64) -> ForwardTrace {
    assert_eq!(
        input_fp.len(),
        model.layer_sizes[0],
        "MLP input dimension mismatch"
    );
    let mut activations = input_fp.to_vec();
    let mut pre_activations = Vec::new();
    let mut relu_masks = Vec::new();

    for (layer_idx, layer) in model.layers.iter().enumerate() {
        let mut pre = Vec::with_capacity(layer.bias.len());
        for (row, bias_fp) in layer.weight.iter().zip(layer.bias.iter()) {
            let mut acc = *bias_fp;
            for (w_fp, x_fp) in row.iter().zip(activations.iter()) {
                acc += fixed_point_mul(*w_fp, *x_fp, fp_scale);
            }
            pre.push(acc);
        }

        let is_hidden = layer_idx + 1 < model.layers.len();
        if is_hidden {
            let mask = pre
                .iter()
                .map(|value| if *value > 0 { 1 } else { 0 })
                .collect::<Vec<_>>();
            activations = pre
                .iter()
                .map(|value| if *value > 0 { *value } else { 0 })
                .collect::<Vec<_>>();
            pre_activations.push(pre);
            relu_masks.push(mask);
        } else {
            activations = pre;
        }
    }

    ForwardTrace {
        pre_activations,
        relu_masks,
        outputs: activations,
    }
}

fn assert_trace_eq(claimed: &ForwardTrace, expected: &ForwardTrace, label: &str) {
    assert_eq!(
        claimed.pre_activations, expected.pre_activations,
        "{label} pre_activations mismatch"
    );
    assert_eq!(
        claimed.relu_masks, expected.relu_masks,
        "{label} relu_masks mismatch"
    );
    assert_eq!(claimed.outputs, expected.outputs, "{label} outputs mismatch");
}

fn argmax_first(values: &[i64]) -> usize {
    assert!(!values.is_empty(), "argmax requires at least one value");
    let mut best_idx = 0usize;
    let mut best_value = values[0];
    for (idx, value) in values.iter().enumerate().skip(1) {
        if *value > best_value {
            best_idx = idx;
            best_value = *value;
        }
    }
    best_idx
}

fn network_spec_hash(layer_sizes: &[usize], fp_scale: i64) -> String {
    let layer_sizes_json = usize_vec_json(layer_sizes);
    let payload = format!(
        "{{\"activation\":\"relu_hidden_identity_output\",\"format\":\"network_spec_v1\",\"fp_scale\":{},\"layer_sizes\":{}}}",
        fp_scale, layer_sizes_json
    );
    hex::encode(Sha256::digest(payload.as_bytes()))
}

fn model_commitment(model: &QuantizedMlp, fp_scale: i64) -> String {
    let payload = format!(
        "{{\"format\":\"quantized_mlp_v1\",\"fp_scale\":{},\"layer_sizes\":{},\"layers\":{}}}",
        fp_scale,
        usize_vec_json(&model.layer_sizes),
        layers_json(&model.layers)
    );
    hex::encode(Sha256::digest(payload.as_bytes()))
}

fn layers_json(layers: &[QuantizedLayer]) -> String {
    let mut out = String::from("[");
    for (idx, layer) in layers.iter().enumerate() {
        if idx > 0 {
            out.push(',');
        }
        out.push_str("{\"bias\":");
        out.push_str(&i64_vec_json(&layer.bias));
        out.push_str(",\"weight\":");
        out.push_str(&i64_matrix_json(&layer.weight));
        out.push('}');
    }
    out.push(']');
    out
}

fn i64_matrix_json(matrix: &[Vec<i64>]) -> String {
    let mut out = String::from("[");
    for (idx, row) in matrix.iter().enumerate() {
        if idx > 0 {
            out.push(',');
        }
        out.push_str(&i64_vec_json(row));
    }
    out.push(']');
    out
}

fn i64_vec_json(values: &[i64]) -> String {
    let mut out = String::from("[");
    for (idx, value) in values.iter().enumerate() {
        if idx > 0 {
            out.push(',');
        }
        out.push_str(&value.to_string());
    }
    out.push(']');
    out
}

fn usize_vec_json(values: &[usize]) -> String {
    let mut out = String::from("[");
    for (idx, value) in values.iter().enumerate() {
        if idx > 0 {
            out.push(',');
        }
        out.push_str(&value.to_string());
    }
    out.push(']');
    out
}
