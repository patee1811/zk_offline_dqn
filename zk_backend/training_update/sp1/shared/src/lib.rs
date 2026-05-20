use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingUpdateInput {
    pub schema_version: String,
    pub public_inputs: TrainingUpdatePublicInputs,
    pub private_witness: TrainingUpdateWitness,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingUpdatePublicInputs {
    pub relation: String,
    pub case_id: String,
    pub dataset_id_hash: String,
    pub dataset_type: String,
    pub dataset_root: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: Option<String>,
    pub raw_trajectory_hash: String,
    pub leaf_hash: String,
    pub leaf_index: u64,
    pub checkpoint_hash_t: String,
    pub checkpoint_hash_t_plus_1: String,
    pub target_checkpoint_hash: String,
    pub batch_size: usize,
    pub fixed_point_scale: i64,
    pub gamma: i64,
    pub learning_rate: i64,
    pub claimed_q_online_action: i64,
    pub claimed_q_target_next: i64,
    pub claimed_td_target: i64,
    pub claimed_td_error: i64,
    pub claimed_loss: i64,
    pub claimed_gradient_hash: String,
    pub claimed_update_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingUpdateWitness {
    pub provenance: ProvenanceWitness,
    pub transition: Transition,
    pub merkle_path: Vec<MerklePathStep>,
    pub online_model_t: QuantizedMlp,
    pub target_model: QuantizedMlp,
    pub online_model_t_plus_1: QuantizedMlp,
    pub intermediates: TrainingIntermediates,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceWitness {
    pub dataset_id_hash: String,
    pub dataset_type: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: Option<String>,
    pub raw_trajectory_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transition {
    pub state: Vec<i64>,
    pub action: usize,
    pub reward: i64,
    pub next_state: Vec<i64>,
    pub terminated: bool,
    pub truncated: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MerklePathStep {
    pub level: u64,
    pub current_index: u64,
    pub sibling_index: u64,
    pub sibling_hash: String,
    pub current_is_left: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuantizedMlp {
    pub format: String,
    pub layer_sizes: Vec<usize>,
    pub fp_scale: i64,
    pub layers: Vec<QuantizedLayer>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct QuantizedLayer {
    pub weight: Vec<Vec<i64>>,
    pub bias: Vec<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingIntermediates {
    pub z1_online: Vec<i64>,
    pub h1_online: Vec<i64>,
    pub q_online: Vec<i64>,
    pub z1_target: Vec<i64>,
    pub h1_target: Vec<i64>,
    pub q_target: Vec<i64>,
    pub gradients: MlpUpdateTensors,
    pub deltas: MlpUpdateTensors,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MlpUpdateTensors {
    pub layers: Vec<QuantizedLayer>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TrainingUpdateOutput {
    pub schema_version: String,
    pub relation: String,
    pub case_id: String,
    pub dataset_id_hash: String,
    pub dataset_type: String,
    pub dataset_root: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: Option<String>,
    pub raw_trajectory_hash: String,
    pub leaf_hash: String,
    pub leaf_index: u64,
    pub checkpoint_hash_t: String,
    pub checkpoint_hash_t_plus_1: String,
    pub target_checkpoint_hash: String,
    pub batch_size: usize,
    pub fixed_point_scale: i64,
    pub gamma: i64,
    pub learning_rate: i64,
    pub q_online_action: i64,
    pub q_target_next: i64,
    pub td_target: i64,
    pub td_error: i64,
    pub loss: i64,
    pub gradient_hash: String,
    pub update_hash: String,
}

#[derive(Debug, Clone)]
struct ForwardCache {
    z1: Vec<i64>,
    h1: Vec<i64>,
    q: Vec<i64>,
}

pub fn verify_training_update(input: &TrainingUpdateInput) -> TrainingUpdateOutput {
    let public = &input.public_inputs;
    let witness = &input.private_witness;
    assert_eq!(
        input.schema_version, "sp1_training_update_case_v1",
        "unexpected schema_version"
    );
    assert_eq!(public.relation, "training_update", "unexpected relation");
    assert_eq!(public.batch_size, 1, "Phase 5 minimum backend supports batch size 1");
    assert_eq!(
        public.dataset_type, "self_collected_replay_audited",
        "training update fixture must be self-collected replay audited"
    );
    assert!(public.fixed_point_scale > 0, "fixed_point_scale must be positive");
    assert!(public.gamma >= 0, "gamma must be nonnegative");
    assert!(public.learning_rate > 0, "learning_rate must be positive");

    assert_provenance_matches(public, &witness.provenance);
    assert_hex_32(&public.dataset_id_hash, "dataset_id_hash");
    assert_hex_32(&public.dataset_root, "dataset_root");
    assert_hex_32(&public.manifest_hash, "manifest_hash");
    assert_hex_32(&public.audit_report_hash, "audit_report_hash");
    assert_hex_32(&public.raw_trajectory_hash, "raw_trajectory_hash");
    assert_hex_32(&public.leaf_hash, "leaf_hash");
    assert_hex_32(&public.checkpoint_hash_t, "checkpoint_hash_t");
    assert_hex_32(&public.checkpoint_hash_t_plus_1, "checkpoint_hash_t_plus_1");
    assert_hex_32(&public.target_checkpoint_hash, "target_checkpoint_hash");
    assert_hex_32(&public.claimed_gradient_hash, "claimed_gradient_hash");
    assert_hex_32(&public.claimed_update_hash, "claimed_update_hash");
    if let Some(value) = &public.collection_log_final_hash {
        assert_hex_32(value, "collection_log_final_hash");
    } else {
        panic!("self-collected replay-audited training update requires collection log hash");
    }

    let online = &witness.online_model_t;
    let target = &witness.target_model;
    let post = &witness.online_model_t_plus_1;
    assert_valid_tiny_model(online, public.fixed_point_scale);
    assert_valid_tiny_model(target, public.fixed_point_scale);
    assert_valid_tiny_model(post, public.fixed_point_scale);
    assert_eq!(
        model_commitment(online, public.fixed_point_scale),
        public.checkpoint_hash_t,
        "checkpoint_hash_t mismatch"
    );
    assert_eq!(
        model_commitment(target, public.fixed_point_scale),
        public.target_checkpoint_hash,
        "target_checkpoint_hash mismatch"
    );

    let leaf = serialize_transition_leaf(&witness.transition, online.layer_sizes[0], *online.layer_sizes.last().unwrap());
    let leaf_hash = hash_leaf(&leaf);
    assert_eq!(leaf_hash, public.leaf_hash, "leaf_hash mismatch");
    assert_path_metadata(&witness.merkle_path, public.leaf_index);
    let root = recompute_root_from_path(&leaf_hash, &witness.merkle_path);
    assert_eq!(root, public.dataset_root, "Merkle path does not authenticate to dataset_root");

    let online_forward = mlp_forward(online, &witness.transition.state, public.fixed_point_scale);
    let online_next = mlp_forward(online, &witness.transition.next_state, public.fixed_point_scale);
    let target_forward = mlp_forward(target, &witness.transition.next_state, public.fixed_point_scale);
    assert_eq!(witness.intermediates.z1_online, online_forward.z1, "z1_online mismatch");
    assert_eq!(witness.intermediates.h1_online, online_forward.h1, "h1_online mismatch");
    assert_eq!(witness.intermediates.q_online, online_forward.q, "q_online mismatch");
    assert_eq!(witness.intermediates.z1_target, target_forward.z1, "z1_target mismatch");
    assert_eq!(witness.intermediates.h1_target, target_forward.h1, "h1_target mismatch");
    assert_eq!(witness.intermediates.q_target, target_forward.q, "q_target mismatch");

    let action = witness.transition.action;
    assert!(action < online_forward.q.len(), "action out of range");
    let q_online_action = online_forward.q[action];
    let next_action = argmax_first(&online_next.q);
    let q_target_next = target_forward.q[next_action];
    let done = witness.transition.terminated || witness.transition.truncated;
    let td_target = if done {
        witness.transition.reward
    } else {
        witness.transition.reward + fixed_point_mul(public.gamma, q_target_next, public.fixed_point_scale)
    };
    let td_error = q_online_action - td_target;
    let loss = smooth_l1_loss_fp(td_error, public.fixed_point_scale);
    assert_eq!(public.claimed_q_online_action, q_online_action, "claimed_q_online_action mismatch");
    assert_eq!(public.claimed_q_target_next, q_target_next, "claimed_q_target_next mismatch");
    assert_eq!(public.claimed_td_target, td_target, "claimed_td_target mismatch");
    assert_eq!(public.claimed_td_error, td_error, "claimed_td_error mismatch");
    assert_eq!(public.claimed_loss, loss, "claimed_loss mismatch");

    let (gradients, deltas, expected_post) = compute_gradients_and_update(
        online,
        &witness.transition,
        td_error,
        public.learning_rate,
        public.fixed_point_scale,
    );
    assert_eq!(witness.intermediates.gradients, gradients, "gradient tensor mismatch");
    assert_eq!(witness.intermediates.deltas, deltas, "delta tensor mismatch");
    assert_model_eq(post, &expected_post, "online_model_t_plus_1");
    assert_eq!(
        model_commitment(post, public.fixed_point_scale),
        public.checkpoint_hash_t_plus_1,
        "checkpoint_hash_t_plus_1 mismatch"
    );
    let gradient_hash = gradient_commitment(&gradients);
    assert_eq!(gradient_hash, public.claimed_gradient_hash, "gradient hash mismatch");
    let update_hash = update_commitment(
        &public.checkpoint_hash_t,
        &public.checkpoint_hash_t_plus_1,
        &gradient_hash,
        public.learning_rate,
    );
    assert_eq!(update_hash, public.claimed_update_hash, "update hash mismatch");

    TrainingUpdateOutput {
        schema_version: "sp1_training_update_public_v1".to_owned(),
        relation: public.relation.clone(),
        case_id: public.case_id.clone(),
        dataset_id_hash: public.dataset_id_hash.clone(),
        dataset_type: public.dataset_type.clone(),
        dataset_root: public.dataset_root.clone(),
        manifest_hash: public.manifest_hash.clone(),
        audit_report_hash: public.audit_report_hash.clone(),
        collection_log_final_hash: public.collection_log_final_hash.clone(),
        raw_trajectory_hash: public.raw_trajectory_hash.clone(),
        leaf_hash: public.leaf_hash.clone(),
        leaf_index: public.leaf_index,
        checkpoint_hash_t: public.checkpoint_hash_t.clone(),
        checkpoint_hash_t_plus_1: public.checkpoint_hash_t_plus_1.clone(),
        target_checkpoint_hash: public.target_checkpoint_hash.clone(),
        batch_size: public.batch_size,
        fixed_point_scale: public.fixed_point_scale,
        gamma: public.gamma,
        learning_rate: public.learning_rate,
        q_online_action,
        q_target_next,
        td_target,
        td_error,
        loss,
        gradient_hash,
        update_hash,
    }
}

fn assert_provenance_matches(public: &TrainingUpdatePublicInputs, provenance: &ProvenanceWitness) {
    assert_eq!(public.dataset_id_hash, provenance.dataset_id_hash, "dataset_id_hash witness mismatch");
    assert_eq!(public.dataset_type, provenance.dataset_type, "dataset_type witness mismatch");
    assert_eq!(public.manifest_hash, provenance.manifest_hash, "manifest_hash witness mismatch");
    assert_eq!(public.audit_report_hash, provenance.audit_report_hash, "audit_report_hash witness mismatch");
    assert_eq!(public.collection_log_final_hash, provenance.collection_log_final_hash, "collection_log_final_hash witness mismatch");
    assert_eq!(public.raw_trajectory_hash, provenance.raw_trajectory_hash, "raw_trajectory_hash witness mismatch");
}

fn assert_valid_tiny_model(model: &QuantizedMlp, fp_scale: i64) {
    assert_eq!(model.format, "quantized_mlp_v1", "unexpected model format");
    assert_eq!(model.fp_scale, fp_scale, "model fp_scale mismatch");
    assert_eq!(model.layer_sizes.len(), 3, "training_update expects one hidden layer");
    assert_eq!(model.layers.len(), 2, "training_update expects two linear layers");
    for (idx, layer) in model.layers.iter().enumerate() {
        let in_dim = model.layer_sizes[idx];
        let out_dim = model.layer_sizes[idx + 1];
        assert_eq!(layer.weight.len(), out_dim, "weight out_dim mismatch");
        assert_eq!(layer.bias.len(), out_dim, "bias out_dim mismatch");
        for row in &layer.weight {
            assert_eq!(row.len(), in_dim, "weight in_dim mismatch");
        }
    }
}

fn mlp_forward(model: &QuantizedMlp, input_fp: &[i64], fp_scale: i64) -> ForwardCache {
    assert_eq!(input_fp.len(), model.layer_sizes[0], "input dimension mismatch");
    let hidden_layer = &model.layers[0];
    let output_layer = &model.layers[1];
    let mut z1 = Vec::with_capacity(hidden_layer.bias.len());
    for (row, bias_fp) in hidden_layer.weight.iter().zip(hidden_layer.bias.iter()) {
        let mut acc = *bias_fp;
        for (w_fp, x_fp) in row.iter().zip(input_fp.iter()) {
            acc += fixed_point_mul(*w_fp, *x_fp, fp_scale);
        }
        z1.push(acc);
    }
    let h1 = z1.iter().map(|value| if *value > 0 { *value } else { 0 }).collect::<Vec<_>>();
    let mut q = Vec::with_capacity(output_layer.bias.len());
    for (row, bias_fp) in output_layer.weight.iter().zip(output_layer.bias.iter()) {
        let mut acc = *bias_fp;
        for (w_fp, h_fp) in row.iter().zip(h1.iter()) {
            acc += fixed_point_mul(*w_fp, *h_fp, fp_scale);
        }
        q.push(acc);
    }
    ForwardCache { z1, h1, q }
}

fn compute_gradients_and_update(
    model: &QuantizedMlp,
    transition: &Transition,
    td_error: i64,
    learning_rate: i64,
    fp_scale: i64,
) -> (MlpUpdateTensors, MlpUpdateTensors, QuantizedMlp) {
    let forward = mlp_forward(model, &transition.state, fp_scale);
    let action = transition.action;
    let loss_grad = smooth_l1_grad_fp(td_error, fp_scale);
    let mut gradients = zero_update_tensors(&model.layer_sizes);
    gradients.layers[1].bias[action] = loss_grad;
    for hidden_idx in 0..forward.h1.len() {
        gradients.layers[1].weight[action][hidden_idx] =
            fixed_point_mul(loss_grad, forward.h1[hidden_idx], fp_scale);
    }
    let output_action_weights = &model.layers[1].weight[action];
    for hidden_idx in 0..forward.z1.len() {
        let grad_hidden = fixed_point_mul(loss_grad, output_action_weights[hidden_idx], fp_scale);
        let grad_z = if forward.z1[hidden_idx] > 0 { grad_hidden } else { 0 };
        gradients.layers[0].bias[hidden_idx] = grad_z;
        for input_idx in 0..transition.state.len() {
            gradients.layers[0].weight[hidden_idx][input_idx] =
                fixed_point_mul(grad_z, transition.state[input_idx], fp_scale);
        }
    }
    let (post, deltas) = apply_sgd_update(model, &gradients, learning_rate, fp_scale);
    (gradients, deltas, post)
}

fn zero_update_tensors(layer_sizes: &[usize]) -> MlpUpdateTensors {
    let mut layers = Vec::new();
    for idx in 0..(layer_sizes.len() - 1) {
        layers.push(QuantizedLayer {
            weight: vec![vec![0; layer_sizes[idx]]; layer_sizes[idx + 1]],
            bias: vec![0; layer_sizes[idx + 1]],
        });
    }
    MlpUpdateTensors { layers }
}

fn apply_sgd_update(
    pre_model: &QuantizedMlp,
    gradients: &MlpUpdateTensors,
    learning_rate: i64,
    fp_scale: i64,
) -> (QuantizedMlp, MlpUpdateTensors) {
    let mut post_model = QuantizedMlp {
        format: pre_model.format.clone(),
        layer_sizes: pre_model.layer_sizes.clone(),
        fp_scale: pre_model.fp_scale,
        layers: Vec::new(),
    };
    let mut deltas = zero_update_tensors(&pre_model.layer_sizes);
    for (layer_idx, layer) in pre_model.layers.iter().enumerate() {
        let grad_layer = &gradients.layers[layer_idx];
        let mut post_weight = Vec::with_capacity(layer.weight.len());
        for (row_idx, row) in layer.weight.iter().enumerate() {
            let mut post_row = Vec::with_capacity(row.len());
            for (col_idx, value) in row.iter().enumerate() {
                let delta = -fixed_point_mul(learning_rate, grad_layer.weight[row_idx][col_idx], fp_scale);
                deltas.layers[layer_idx].weight[row_idx][col_idx] = delta;
                post_row.push(*value + delta);
            }
            post_weight.push(post_row);
        }
        let mut post_bias = Vec::with_capacity(layer.bias.len());
        for (bias_idx, value) in layer.bias.iter().enumerate() {
            let delta = -fixed_point_mul(learning_rate, grad_layer.bias[bias_idx], fp_scale);
            deltas.layers[layer_idx].bias[bias_idx] = delta;
            post_bias.push(*value + delta);
        }
        post_model.layers.push(QuantizedLayer { weight: post_weight, bias: post_bias });
    }
    (post_model, deltas)
}

fn serialize_transition_leaf(transition: &Transition, obs_dim: usize, action_dim: usize) -> Vec<i64> {
    assert_eq!(transition.state.len(), obs_dim, "state dimension mismatch");
    assert_eq!(transition.next_state.len(), obs_dim, "next_state dimension mismatch");
    assert!(transition.action < action_dim, "action out of range");
    let mut leaf = Vec::with_capacity(2 * obs_dim + 3);
    leaf.extend_from_slice(&transition.state);
    leaf.push(transition.action as i64);
    leaf.push(transition.reward);
    leaf.extend_from_slice(&transition.next_state);
    leaf.push(if transition.terminated || transition.truncated { 1 } else { 0 });
    leaf
}

fn hash_leaf(leaf: &[i64]) -> String {
    hex::encode(Sha256::digest(encode_leaf_for_hash(leaf).as_bytes()))
}

fn encode_leaf_for_hash(leaf: &[i64]) -> String {
    leaf.iter().map(|value| value.to_string()).collect::<Vec<_>>().join(",")
}

fn assert_path_metadata(path: &[MerklePathStep], leaf_index: u64) {
    if path.is_empty() {
        assert_eq!(leaf_index, 0, "single-leaf Merkle path requires leaf_index 0");
        return;
    }
    let mut expected_current = leaf_index;
    for (expected_level, step) in path.iter().enumerate() {
        assert_eq!(step.level, expected_level as u64, "Merkle path level metadata mismatch");
        assert_eq!(step.current_index, expected_current, "Merkle path current_index metadata mismatch");
        if step.current_is_left {
            assert_eq!(expected_current % 2, 0, "left path step has odd index");
            assert!(step.sibling_index == expected_current || step.sibling_index == expected_current + 1, "left sibling_index mismatch");
        } else {
            assert_eq!(expected_current % 2, 1, "right path step has even index");
            assert_eq!(step.sibling_index, expected_current - 1, "right sibling_index mismatch");
        }
        assert_hex_32(&step.sibling_hash, "sibling_hash");
        expected_current /= 2;
    }
}

fn recompute_root_from_path(leaf_hash: &str, merkle_path: &[MerklePathStep]) -> String {
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

fn hash_internal_node(left_hex: &str, right_hex: &str) -> String {
    let left = decode_hex_32(left_hex, "left");
    let right = decode_hex_32(right_hex, "right");
    let mut bytes = Vec::with_capacity(64);
    bytes.extend_from_slice(&left);
    bytes.extend_from_slice(&right);
    hex::encode(Sha256::digest(bytes))
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

fn gradient_commitment(gradients: &MlpUpdateTensors) -> String {
    let payload = format!(
        "{{\"format\":\"training_update_gradients_v1\",\"layers\":{}}}",
        layers_json(&gradients.layers)
    );
    hex::encode(Sha256::digest(payload.as_bytes()))
}

fn update_commitment(
    checkpoint_hash_t: &str,
    checkpoint_hash_t_plus_1: &str,
    gradient_hash: &str,
    learning_rate: i64,
) -> String {
    let payload = format!(
        "{{\"checkpoint_hash_t\":\"{}\",\"checkpoint_hash_t_plus_1\":\"{}\",\"format\":\"training_update_update_v1\",\"gradient_hash\":\"{}\",\"learning_rate\":{}}}",
        checkpoint_hash_t, checkpoint_hash_t_plus_1, gradient_hash, learning_rate
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

fn fixed_point_mul(a_fp: i64, b_fp: i64, fp_scale: i64) -> i64 {
    (a_fp * b_fp) / fp_scale
}

fn smooth_l1_loss_fp(td_error_fp: i64, fp_scale: i64) -> i64 {
    let abs_x_fp = td_error_fp.abs();
    if abs_x_fp < fp_scale {
        (abs_x_fp * abs_x_fp) / (2 * fp_scale)
    } else {
        abs_x_fp - fp_scale / 2
    }
}

fn smooth_l1_grad_fp(td_error_fp: i64, fp_scale: i64) -> i64 {
    let abs_x_fp = td_error_fp.abs();
    if abs_x_fp < fp_scale {
        td_error_fp
    } else if td_error_fp > 0 {
        fp_scale
    } else {
        -fp_scale
    }
}

fn assert_model_eq(actual: &QuantizedMlp, expected: &QuantizedMlp, label: &str) {
    assert_eq!(actual.format, expected.format, "{label} format mismatch");
    assert_eq!(actual.layer_sizes, expected.layer_sizes, "{label} layer_sizes mismatch");
    assert_eq!(actual.fp_scale, expected.fp_scale, "{label} fp_scale mismatch");
    assert_eq!(actual.layers.len(), expected.layers.len(), "{label} layer count mismatch");
    for idx in 0..actual.layers.len() {
        assert_eq!(actual.layers[idx].weight, expected.layers[idx].weight, "{label} weight mismatch");
        assert_eq!(actual.layers[idx].bias, expected.layers[idx].bias, "{label} bias mismatch");
    }
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
