use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

const LCG_A: u64 = 1_664_525;
const LCG_C: u64 = 1_013_904_223;
const LCG_M: u64 = 1u64 << 32;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingFragmentInput {
    pub schema_version: String,
    pub public_inputs: TrainingFragmentPublicInputs,
    pub private_witness: TrainingFragmentWitness,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingFragmentPublicInputs {
    pub relation: String,
    pub case_id: String,
    pub dataset_id_hash: String,
    pub dataset_type: String,
    pub dataset_root: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: String,
    pub raw_trajectory_hash: String,
    pub start_checkpoint_hash: String,
    pub final_checkpoint_hash: String,
    pub start_target_checkpoint_hash: String,
    pub final_target_checkpoint_hash: String,
    pub num_steps: usize,
    pub batch_size: usize,
    pub fixed_point_scale: i64,
    pub gamma: i64,
    pub learning_rate: i64,
    pub sampler_seed: u64,
    pub sampler_type: String,
    pub dataset_size: u64,
    pub target_sync_interval: u64,
    pub target_sync_mode: String,
    pub global_step_start: u64,
    pub trace_hash: String,
    pub checkpoint_chain_hash: String,
    pub minibatch_indices_hash: String,
    pub loss_trace_hash: String,
    pub gradient_trace_hash: String,
    pub update_trace_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingFragmentWitness {
    pub provenance: ProvenanceWitness,
    pub steps: Vec<TrainingFragmentStep>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProvenanceWitness {
    pub dataset_id_hash: String,
    pub dataset_type: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: String,
    pub raw_trajectory_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingFragmentStep {
    pub step_id: usize,
    pub global_step: u64,
    pub sample_index: u64,
    pub transition: Transition,
    pub leaf_hash: String,
    pub leaf_index: u64,
    pub merkle_path: Vec<MerklePathStep>,
    pub checkpoint_hash_before: String,
    pub checkpoint_hash_after: String,
    pub target_checkpoint_hash_before: String,
    pub target_checkpoint_hash_after: String,
    pub online_model_before: QuantizedMlp,
    pub target_model_before: QuantizedMlp,
    pub online_model_after: QuantizedMlp,
    pub target_model_after: QuantizedMlp,
    pub intermediates: TrainingFragmentIntermediates,
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
pub struct TrainingFragmentIntermediates {
    pub q_online_action: i64,
    pub q_target_next: i64,
    pub td_target: i64,
    pub td_error: i64,
    pub loss: i64,
    pub z1_online: Vec<i64>,
    pub h1_online: Vec<i64>,
    pub q_online: Vec<i64>,
    pub z1_target: Vec<i64>,
    pub h1_target: Vec<i64>,
    pub q_target: Vec<i64>,
    pub gradients: MlpUpdateTensors,
    pub deltas: MlpUpdateTensors,
    pub gradient_hash: String,
    pub update_hash: String,
    pub target_sync_applied: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MlpUpdateTensors {
    pub layers: Vec<QuantizedLayer>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TrainingFragmentOutput {
    pub schema_version: String,
    pub relation: String,
    pub case_id: String,
    pub dataset_id_hash: String,
    pub dataset_type: String,
    pub dataset_root: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: String,
    pub raw_trajectory_hash: String,
    pub start_checkpoint_hash: String,
    pub final_checkpoint_hash: String,
    pub start_target_checkpoint_hash: String,
    pub final_target_checkpoint_hash: String,
    pub num_steps: usize,
    pub batch_size: usize,
    pub fixed_point_scale: i64,
    pub gamma: i64,
    pub learning_rate: i64,
    pub sampler_seed: u64,
    pub sampler_type: String,
    pub dataset_size: u64,
    pub target_sync_interval: u64,
    pub target_sync_mode: String,
    pub trace_hash: String,
    pub checkpoint_chain_hash: String,
    pub minibatch_indices_hash: String,
    pub loss_trace_hash: String,
    pub gradient_trace_hash: String,
    pub update_trace_hash: String,
    pub target_sync_events: u64,
}

#[derive(Debug, Clone)]
struct ForwardCache {
    z1: Vec<i64>,
    h1: Vec<i64>,
    q: Vec<i64>,
}

#[derive(Debug, Clone)]
struct StepSummary {
    checkpoint_hash_before: String,
    checkpoint_hash_after: String,
    target_checkpoint_hash_before: String,
    target_checkpoint_hash_after: String,
    target_sync_applied: bool,
    sample_index: u64,
    q_online_action: i64,
    q_target_next: i64,
    td_target: i64,
    td_error: i64,
    loss: i64,
    gradient_hash: String,
    update_hash: String,
}

pub fn verify_training_fragment(input: &TrainingFragmentInput) -> TrainingFragmentOutput {
    let public = &input.public_inputs;
    let witness = &input.private_witness;
    assert_eq!(
        input.schema_version, "sp1_training_fragment_case_v1",
        "unexpected schema_version"
    );
    assert_eq!(public.relation, "training_fragment", "unexpected relation");
    assert_eq!(
        public.batch_size, 1,
        "Phase 6 fragment backend supports batch size 1"
    );
    assert_eq!(
        public.dataset_type, "self_collected_replay_audited",
        "unexpected dataset_type"
    );
    assert_eq!(
        public.sampler_type, "lcg_mod_dataset_size",
        "unexpected sampler_type"
    );
    assert_eq!(
        public.target_sync_mode, "hard",
        "unexpected target_sync_mode"
    );
    assert_eq!(public.num_steps, witness.steps.len(), "num_steps mismatch");
    assert!(
        public.fixed_point_scale > 0,
        "fixed_point_scale must be positive"
    );
    assert!(public.learning_rate > 0, "learning_rate must be positive");
    assert!(public.dataset_size > 0, "dataset_size must be positive");
    assert!(
        public.target_sync_interval > 0,
        "target_sync_interval must be positive"
    );

    assert_provenance_matches(public, &witness.provenance);
    for (value, label) in [
        (&public.dataset_id_hash, "dataset_id_hash"),
        (&public.dataset_root, "dataset_root"),
        (&public.manifest_hash, "manifest_hash"),
        (&public.audit_report_hash, "audit_report_hash"),
        (
            &public.collection_log_final_hash,
            "collection_log_final_hash",
        ),
        (&public.raw_trajectory_hash, "raw_trajectory_hash"),
        (&public.start_checkpoint_hash, "start_checkpoint_hash"),
        (&public.final_checkpoint_hash, "final_checkpoint_hash"),
        (
            &public.start_target_checkpoint_hash,
            "start_target_checkpoint_hash",
        ),
        (
            &public.final_target_checkpoint_hash,
            "final_target_checkpoint_hash",
        ),
        (&public.trace_hash, "trace_hash"),
        (&public.checkpoint_chain_hash, "checkpoint_chain_hash"),
        (&public.minibatch_indices_hash, "minibatch_indices_hash"),
        (&public.loss_trace_hash, "loss_trace_hash"),
        (&public.gradient_trace_hash, "gradient_trace_hash"),
        (&public.update_trace_hash, "update_trace_hash"),
    ] {
        assert_hex_32(value, label);
    }

    let mut expected_checkpoint_hash = public.start_checkpoint_hash.clone();
    let mut expected_target_hash = public.start_target_checkpoint_hash.clone();
    let mut summaries = Vec::with_capacity(public.num_steps);
    let mut target_sync_events = 0u64;

    for (idx, step) in witness.steps.iter().enumerate() {
        assert_eq!(step.step_id, idx, "step_id mismatch");
        assert_eq!(
            step.global_step,
            public.global_step_start + idx as u64,
            "global_step mismatch"
        );
        let expected_sample =
            lcg_sample_index(public.sampler_seed, idx as u64, public.dataset_size);
        assert_eq!(
            step.sample_index, expected_sample,
            "deterministic sample index mismatch"
        );
        assert_eq!(
            step.leaf_index, expected_sample,
            "leaf_index must match deterministic sample index"
        );

        assert_valid_tiny_model(&step.online_model_before, public.fixed_point_scale);
        assert_valid_tiny_model(&step.target_model_before, public.fixed_point_scale);
        assert_valid_tiny_model(&step.online_model_after, public.fixed_point_scale);
        assert_valid_tiny_model(&step.target_model_after, public.fixed_point_scale);

        let checkpoint_hash_before =
            model_commitment(&step.online_model_before, public.fixed_point_scale);
        let target_checkpoint_hash_before =
            model_commitment(&step.target_model_before, public.fixed_point_scale);
        assert_eq!(
            checkpoint_hash_before, step.checkpoint_hash_before,
            "checkpoint_hash_before mismatch"
        );
        assert_eq!(
            target_checkpoint_hash_before, step.target_checkpoint_hash_before,
            "target_checkpoint_hash_before mismatch"
        );
        assert_eq!(
            checkpoint_hash_before, expected_checkpoint_hash,
            "checkpoint chain mismatch"
        );
        assert_eq!(
            target_checkpoint_hash_before, expected_target_hash,
            "target checkpoint chain mismatch"
        );

        let leaf = serialize_transition_leaf(
            &step.transition,
            step.online_model_before.layer_sizes[0],
            *step.online_model_before.layer_sizes.last().unwrap(),
        );
        let leaf_hash = hash_leaf(&leaf);
        assert_eq!(leaf_hash, step.leaf_hash, "leaf_hash mismatch");
        assert_path_metadata(&step.merkle_path, step.leaf_index);
        let root = recompute_root_from_path(&leaf_hash, &step.merkle_path);
        assert_eq!(
            root, public.dataset_root,
            "Merkle path does not authenticate to dataset_root"
        );

        let online_forward = mlp_forward(
            &step.online_model_before,
            &step.transition.state,
            public.fixed_point_scale,
        );
        let online_next = mlp_forward(
            &step.online_model_before,
            &step.transition.next_state,
            public.fixed_point_scale,
        );
        let target_forward = mlp_forward(
            &step.target_model_before,
            &step.transition.next_state,
            public.fixed_point_scale,
        );
        assert_eq!(
            step.intermediates.z1_online, online_forward.z1,
            "z1_online mismatch"
        );
        assert_eq!(
            step.intermediates.h1_online, online_forward.h1,
            "h1_online mismatch"
        );
        assert_eq!(
            step.intermediates.q_online, online_forward.q,
            "q_online mismatch"
        );
        assert_eq!(
            step.intermediates.z1_target, target_forward.z1,
            "z1_target mismatch"
        );
        assert_eq!(
            step.intermediates.h1_target, target_forward.h1,
            "h1_target mismatch"
        );
        assert_eq!(
            step.intermediates.q_target, target_forward.q,
            "q_target mismatch"
        );

        let action = step.transition.action;
        assert!(action < online_forward.q.len(), "action out of range");
        let q_online_action = online_forward.q[action];
        let next_action = argmax_first(&online_next.q);
        let q_target_next = target_forward.q[next_action];
        let done = step.transition.terminated || step.transition.truncated;
        let td_target = if done {
            step.transition.reward
        } else {
            step.transition.reward
                + fixed_point_mul(public.gamma, q_target_next, public.fixed_point_scale)
        };
        let td_error = q_online_action - td_target;
        let loss = smooth_l1_loss_fp(td_error, public.fixed_point_scale);
        assert_eq!(
            step.intermediates.q_online_action, q_online_action,
            "q_online_action mismatch"
        );
        assert_eq!(
            step.intermediates.q_target_next, q_target_next,
            "q_target_next mismatch"
        );
        assert_eq!(
            step.intermediates.td_target, td_target,
            "td_target mismatch"
        );
        assert_eq!(step.intermediates.td_error, td_error, "td_error mismatch");
        assert_eq!(step.intermediates.loss, loss, "loss mismatch");

        let (gradients, deltas, expected_post) = compute_gradients_and_update(
            &step.online_model_before,
            &step.transition,
            td_error,
            public.learning_rate,
            public.fixed_point_scale,
        );
        assert_eq!(
            step.intermediates.gradients, gradients,
            "gradient tensor mismatch"
        );
        assert_eq!(step.intermediates.deltas, deltas, "delta tensor mismatch");
        assert_model_eq(
            &step.online_model_after,
            &expected_post,
            "online_model_after",
        );
        let checkpoint_hash_after =
            model_commitment(&step.online_model_after, public.fixed_point_scale);
        assert_eq!(
            checkpoint_hash_after, step.checkpoint_hash_after,
            "checkpoint_hash_after mismatch"
        );
        let gradient_hash = gradient_commitment(&gradients);
        assert_eq!(
            gradient_hash, step.intermediates.gradient_hash,
            "gradient hash mismatch"
        );
        let update_hash = update_commitment(
            &checkpoint_hash_before,
            &checkpoint_hash_after,
            &gradient_hash,
            public.learning_rate,
        );
        assert_eq!(
            update_hash, step.intermediates.update_hash,
            "update hash mismatch"
        );

        let sync_applied = target_sync_applies(public, idx as u64);
        assert_eq!(
            step.intermediates.target_sync_applied, sync_applied,
            "target_sync_applied mismatch"
        );
        if sync_applied {
            assert_model_eq(
                &step.target_model_after,
                &step.online_model_after,
                "target_model_after",
            );
            target_sync_events += 1;
        } else {
            assert_model_eq(
                &step.target_model_after,
                &step.target_model_before,
                "target_model_after",
            );
        }
        let target_checkpoint_hash_after =
            model_commitment(&step.target_model_after, public.fixed_point_scale);
        assert_eq!(
            target_checkpoint_hash_after, step.target_checkpoint_hash_after,
            "target_checkpoint_hash_after mismatch"
        );

        summaries.push(StepSummary {
            checkpoint_hash_before: checkpoint_hash_before.clone(),
            checkpoint_hash_after: checkpoint_hash_after.clone(),
            target_checkpoint_hash_before: target_checkpoint_hash_before.clone(),
            target_checkpoint_hash_after: target_checkpoint_hash_after.clone(),
            target_sync_applied: sync_applied,
            sample_index: expected_sample,
            q_online_action,
            q_target_next,
            td_target,
            td_error,
            loss,
            gradient_hash,
            update_hash,
        });
        expected_checkpoint_hash = checkpoint_hash_after;
        expected_target_hash = target_checkpoint_hash_after;
    }

    assert_eq!(
        expected_checkpoint_hash, public.final_checkpoint_hash,
        "final_checkpoint_hash mismatch"
    );
    assert_eq!(
        expected_target_hash, public.final_target_checkpoint_hash,
        "final_target_checkpoint_hash mismatch"
    );
    let checkpoint_chain_hash = checkpoint_chain_hash(&summaries);
    let minibatch_indices_hash = minibatch_indices_hash(&summaries);
    let loss_trace_hash = loss_trace_hash(&summaries);
    let gradient_trace_hash = gradient_trace_hash(&summaries);
    let update_trace_hash = update_trace_hash(&summaries);
    let trace_hash = fragment_trace_hash(
        &checkpoint_chain_hash,
        &minibatch_indices_hash,
        &loss_trace_hash,
        &gradient_trace_hash,
        &update_trace_hash,
    );
    assert_eq!(
        checkpoint_chain_hash, public.checkpoint_chain_hash,
        "checkpoint_chain_hash mismatch"
    );
    assert_eq!(
        minibatch_indices_hash, public.minibatch_indices_hash,
        "minibatch_indices_hash mismatch"
    );
    assert_eq!(
        loss_trace_hash, public.loss_trace_hash,
        "loss_trace_hash mismatch"
    );
    assert_eq!(
        gradient_trace_hash, public.gradient_trace_hash,
        "gradient_trace_hash mismatch"
    );
    assert_eq!(
        update_trace_hash, public.update_trace_hash,
        "update_trace_hash mismatch"
    );
    assert_eq!(trace_hash, public.trace_hash, "trace_hash mismatch");

    TrainingFragmentOutput {
        schema_version: "sp1_training_fragment_public_v1".to_owned(),
        relation: public.relation.clone(),
        case_id: public.case_id.clone(),
        dataset_id_hash: public.dataset_id_hash.clone(),
        dataset_type: public.dataset_type.clone(),
        dataset_root: public.dataset_root.clone(),
        manifest_hash: public.manifest_hash.clone(),
        audit_report_hash: public.audit_report_hash.clone(),
        collection_log_final_hash: public.collection_log_final_hash.clone(),
        raw_trajectory_hash: public.raw_trajectory_hash.clone(),
        start_checkpoint_hash: public.start_checkpoint_hash.clone(),
        final_checkpoint_hash: public.final_checkpoint_hash.clone(),
        start_target_checkpoint_hash: public.start_target_checkpoint_hash.clone(),
        final_target_checkpoint_hash: public.final_target_checkpoint_hash.clone(),
        num_steps: public.num_steps,
        batch_size: public.batch_size,
        fixed_point_scale: public.fixed_point_scale,
        gamma: public.gamma,
        learning_rate: public.learning_rate,
        sampler_seed: public.sampler_seed,
        sampler_type: public.sampler_type.clone(),
        dataset_size: public.dataset_size,
        target_sync_interval: public.target_sync_interval,
        target_sync_mode: public.target_sync_mode.clone(),
        trace_hash,
        checkpoint_chain_hash,
        minibatch_indices_hash,
        loss_trace_hash,
        gradient_trace_hash,
        update_trace_hash,
        target_sync_events,
    }
}

fn assert_provenance_matches(
    public: &TrainingFragmentPublicInputs,
    provenance: &ProvenanceWitness,
) {
    assert_eq!(
        public.dataset_id_hash, provenance.dataset_id_hash,
        "dataset_id_hash witness mismatch"
    );
    assert_eq!(
        public.dataset_type, provenance.dataset_type,
        "dataset_type witness mismatch"
    );
    assert_eq!(
        public.manifest_hash, provenance.manifest_hash,
        "manifest_hash witness mismatch"
    );
    assert_eq!(
        public.audit_report_hash, provenance.audit_report_hash,
        "audit_report_hash witness mismatch"
    );
    assert_eq!(
        public.collection_log_final_hash, provenance.collection_log_final_hash,
        "collection_log_final_hash witness mismatch"
    );
    assert_eq!(
        public.raw_trajectory_hash, provenance.raw_trajectory_hash,
        "raw_trajectory_hash witness mismatch"
    );
}

fn lcg_sample_index(seed: u64, step_id: u64, dataset_size: u64) -> u64 {
    assert!(dataset_size > 0, "dataset_size must be positive");
    let mut state = seed % LCG_M;
    for _ in 0..=step_id {
        state = (LCG_A.wrapping_mul(state).wrapping_add(LCG_C)) % LCG_M;
    }
    state % dataset_size
}

fn target_sync_applies(public: &TrainingFragmentPublicInputs, step_id: u64) -> bool {
    (public.global_step_start + step_id + 1) % public.target_sync_interval == 0
}

fn assert_valid_tiny_model(model: &QuantizedMlp, fp_scale: i64) {
    assert_eq!(model.format, "quantized_mlp_v1", "unexpected model format");
    assert_eq!(model.fp_scale, fp_scale, "model fp_scale mismatch");
    assert_eq!(
        model.layer_sizes.len(),
        3,
        "training_fragment expects one hidden layer"
    );
    assert_eq!(
        model.layers.len(),
        2,
        "training_fragment expects two linear layers"
    );
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
    assert_eq!(
        input_fp.len(),
        model.layer_sizes[0],
        "input dimension mismatch"
    );
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
    let h1 = z1
        .iter()
        .map(|value| if *value > 0 { *value } else { 0 })
        .collect::<Vec<_>>();
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
        let grad_z = if forward.z1[hidden_idx] > 0 {
            grad_hidden
        } else {
            0
        };
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
                let delta =
                    -fixed_point_mul(learning_rate, grad_layer.weight[row_idx][col_idx], fp_scale);
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
        post_model.layers.push(QuantizedLayer {
            weight: post_weight,
            bias: post_bias,
        });
    }
    (post_model, deltas)
}

fn serialize_transition_leaf(
    transition: &Transition,
    obs_dim: usize,
    action_dim: usize,
) -> Vec<i64> {
    assert_eq!(transition.state.len(), obs_dim, "state dimension mismatch");
    assert_eq!(
        transition.next_state.len(),
        obs_dim,
        "next_state dimension mismatch"
    );
    assert!(transition.action < action_dim, "action out of range");
    let mut leaf = Vec::with_capacity(2 * obs_dim + 3);
    leaf.extend_from_slice(&transition.state);
    leaf.push(transition.action as i64);
    leaf.push(transition.reward);
    leaf.extend_from_slice(&transition.next_state);
    leaf.push(if transition.terminated || transition.truncated {
        1
    } else {
        0
    });
    leaf
}

fn hash_leaf(leaf: &[i64]) -> String {
    hex::encode(Sha256::digest(encode_leaf_for_hash(leaf).as_bytes()))
}

fn encode_leaf_for_hash(leaf: &[i64]) -> String {
    leaf.iter()
        .map(|value| value.to_string())
        .collect::<Vec<_>>()
        .join(",")
}

fn assert_path_metadata(path: &[MerklePathStep], leaf_index: u64) {
    if path.is_empty() {
        assert_eq!(
            leaf_index, 0,
            "single-leaf Merkle path requires leaf_index 0"
        );
        return;
    }
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
                "left sibling_index mismatch"
            );
        } else {
            assert_eq!(expected_current % 2, 1, "right path step has even index");
            assert_eq!(
                step.sibling_index,
                expected_current - 1,
                "right sibling_index mismatch"
            );
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

fn checkpoint_chain_hash(summaries: &[StepSummary]) -> String {
    let values = summaries
        .iter()
        .map(|item| {
            format!(
                "{{\"checkpoint_hash_after\":\"{}\",\"checkpoint_hash_before\":\"{}\",\"target_checkpoint_hash_after\":\"{}\",\"target_checkpoint_hash_before\":\"{}\",\"target_sync_applied\":{}}}",
                item.checkpoint_hash_after,
                item.checkpoint_hash_before,
                item.target_checkpoint_hash_after,
                item.target_checkpoint_hash_before,
                bool_json(item.target_sync_applied)
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    trace_commitment(
        "training_fragment_checkpoint_chain_v1",
        &format!("[{}]", values),
    )
}

fn minibatch_indices_hash(summaries: &[StepSummary]) -> String {
    let values = summaries
        .iter()
        .map(|item| item.sample_index.to_string())
        .collect::<Vec<_>>()
        .join(",");
    trace_commitment(
        "training_fragment_minibatch_indices_v1",
        &format!("[{}]", values),
    )
}

fn loss_trace_hash(summaries: &[StepSummary]) -> String {
    let values = summaries
        .iter()
        .map(|item| {
            format!(
                "{{\"loss\":{},\"q_online_action\":{},\"q_target_next\":{},\"td_error\":{},\"td_target\":{}}}",
                item.loss, item.q_online_action, item.q_target_next, item.td_error, item.td_target
            )
        })
        .collect::<Vec<_>>()
        .join(",");
    trace_commitment("training_fragment_loss_trace_v1", &format!("[{}]", values))
}

fn gradient_trace_hash(summaries: &[StepSummary]) -> String {
    let values = summaries
        .iter()
        .map(|item| format!("\"{}\"", item.gradient_hash))
        .collect::<Vec<_>>()
        .join(",");
    trace_commitment(
        "training_fragment_gradient_trace_v1",
        &format!("[{}]", values),
    )
}

fn update_trace_hash(summaries: &[StepSummary]) -> String {
    let values = summaries
        .iter()
        .map(|item| format!("\"{}\"", item.update_hash))
        .collect::<Vec<_>>()
        .join(",");
    trace_commitment(
        "training_fragment_update_trace_v1",
        &format!("[{}]", values),
    )
}

fn trace_commitment(format_name: &str, values_json: &str) -> String {
    let payload = format!(
        "{{\"format\":\"{}\",\"values\":{}}}",
        format_name, values_json
    );
    hex::encode(Sha256::digest(payload.as_bytes()))
}

fn fragment_trace_hash(
    checkpoint_chain_hash: &str,
    minibatch_indices_hash: &str,
    loss_trace_hash: &str,
    gradient_trace_hash: &str,
    update_trace_hash: &str,
) -> String {
    let payload = format!(
        "{{\"checkpoint_chain_hash\":\"{}\",\"format\":\"training_fragment_trace_v1\",\"gradient_trace_hash\":\"{}\",\"loss_trace_hash\":\"{}\",\"minibatch_indices_hash\":\"{}\",\"update_trace_hash\":\"{}\"}}",
        checkpoint_chain_hash,
        gradient_trace_hash,
        loss_trace_hash,
        minibatch_indices_hash,
        update_trace_hash
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

fn bool_json(value: bool) -> &'static str {
    if value {
        "true"
    } else {
        "false"
    }
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
    assert_eq!(
        actual.layer_sizes, expected.layer_sizes,
        "{label} layer_sizes mismatch"
    );
    assert_eq!(
        actual.fp_scale, expected.fp_scale,
        "{label} fp_scale mismatch"
    );
    assert_eq!(
        actual.layers.len(),
        expected.layers.len(),
        "{label} layer count mismatch"
    );
    for idx in 0..actual.layers.len() {
        assert_eq!(
            actual.layers[idx].weight, expected.layers[idx].weight,
            "{label} weight mismatch"
        );
        assert_eq!(
            actual.layers[idx].bias, expected.layers[idx].bias,
            "{label} bias mismatch"
        );
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
