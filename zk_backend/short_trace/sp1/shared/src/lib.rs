use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ShortTraceInput {
    pub schema_version: String,
    pub public_inputs: ShortTracePublicInputs,
    pub private_witness: ShortTraceWitness,
    pub config: ShortTraceConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ShortTracePublicInputs {
    pub relation: String,
    pub case_id: String,
    pub start_checkpoint_hash: String,
    pub final_checkpoint_hash: String,
    pub num_steps: usize,
    pub trace_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ShortTraceConfig {
    pub fixed_point_scale: i64,
    pub learning_rate_fp: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ShortTraceWitness {
    pub steps: Vec<ShortTraceStep>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ShortTraceStep {
    pub old_weights: Vec<i64>,
    pub gradients: Vec<i64>,
    pub new_weights: Vec<i64>,
    pub old_checkpoint_hash: String,
    pub new_checkpoint_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ShortTraceOutput {
    pub schema_version: String,
    pub relation: String,
    pub case_id: String,
    pub start_checkpoint_hash: String,
    pub final_checkpoint_hash: String,
    pub num_steps: usize,
    pub trace_hash: String,
}

pub fn verify_short_trace(input: &ShortTraceInput) -> ShortTraceOutput {
    assert_eq!(input.schema_version, "sp1_short_trace_case_v1");
    assert_eq!(input.public_inputs.relation, "short_trace");
    assert!(input.config.fixed_point_scale > 0);
    assert!(input.config.learning_rate_fp > 0);
    assert_eq!(
        input.private_witness.steps.len(),
        input.public_inputs.num_steps,
        "num_steps mismatch"
    );
    assert!(input.public_inputs.num_steps > 0);

    let mut previous_new_hash: Option<String> = None;
    for (idx, step) in input.private_witness.steps.iter().enumerate() {
        assert_eq!(step.old_weights.len(), step.gradients.len());
        assert_eq!(step.old_weights.len(), step.new_weights.len());
        let old_hash = checkpoint_hash(&step.old_weights);
        let new_hash = checkpoint_hash(&step.new_weights);
        assert_eq!(old_hash, step.old_checkpoint_hash, "old checkpoint hash mismatch");
        assert_eq!(new_hash, step.new_checkpoint_hash, "new checkpoint hash mismatch");
        if idx == 0 {
            assert_eq!(
                step.old_checkpoint_hash, input.public_inputs.start_checkpoint_hash,
                "start checkpoint mismatch"
            );
        } else {
            assert_eq!(
                Some(step.old_checkpoint_hash.clone()),
                previous_new_hash,
                "checkpoint chain mismatch"
            );
        }
        for ((old, grad), new) in step
            .old_weights
            .iter()
            .zip(step.gradients.iter())
            .zip(step.new_weights.iter())
        {
            let delta = -fixed_point_mul(input.config.learning_rate_fp, *grad, input.config.fixed_point_scale);
            assert_eq!(*new, *old + delta, "SGD update mismatch");
        }
        previous_new_hash = Some(step.new_checkpoint_hash.clone());
    }
    assert_eq!(
        previous_new_hash,
        Some(input.public_inputs.final_checkpoint_hash.clone()),
        "final checkpoint mismatch"
    );
    let trace_hash = compute_trace_hash(
        &input.private_witness.steps,
        input.config.learning_rate_fp,
        input.config.fixed_point_scale,
    );
    assert_eq!(trace_hash, input.public_inputs.trace_hash, "trace hash mismatch");

    ShortTraceOutput {
        schema_version: "sp1_short_trace_public_v1".to_owned(),
        relation: input.public_inputs.relation.clone(),
        case_id: input.public_inputs.case_id.clone(),
        start_checkpoint_hash: input.public_inputs.start_checkpoint_hash.clone(),
        final_checkpoint_hash: input.public_inputs.final_checkpoint_hash.clone(),
        num_steps: input.public_inputs.num_steps,
        trace_hash: input.public_inputs.trace_hash.clone(),
    }
}

pub fn checkpoint_hash(weights: &[i64]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(b"checkpoint_v1");
    for value in weights {
        hasher.update(value.to_le_bytes());
    }
    hex::encode(hasher.finalize())
}

pub fn compute_trace_hash(steps: &[ShortTraceStep], learning_rate_fp: i64, fp_scale: i64) -> String {
    let mut hasher = Sha256::new();
    hasher.update(b"short_trace_v1");
    hasher.update(learning_rate_fp.to_le_bytes());
    hasher.update(fp_scale.to_le_bytes());
    for step in steps {
        for values in [&step.old_weights, &step.gradients, &step.new_weights] {
            for value in values {
                hasher.update(value.to_le_bytes());
            }
        }
        hasher.update(hex::decode(&step.old_checkpoint_hash).expect("old hash hex"));
        hasher.update(hex::decode(&step.new_checkpoint_hash).expect("new hash hex"));
    }
    hex::encode(hasher.finalize())
}

fn fixed_point_mul(a_fp: i64, b_fp: i64, fp_scale: i64) -> i64 {
    div_trunc_zero(a_fp * b_fp, fp_scale)
}

fn div_trunc_zero(numerator: i64, denominator: i64) -> i64 {
    let sign = if numerator < 0 { -1 } else { 1 };
    sign * (numerator.abs() / denominator)
}

