use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

const CHUNK_FIELDS: [&str; 19] = [
    "chunk_id",
    "step_start",
    "step_end",
    "input_checkpoint_hash",
    "output_checkpoint_hash",
    "input_target_checkpoint_hash",
    "output_target_checkpoint_hash",
    "dataset_root",
    "manifest_hash",
    "audit_report_hash",
    "collection_log_final_hash",
    "raw_trajectory_hash",
    "config_hash",
    "relation_id",
    "public_inputs_hash",
    "proof_hash",
    "metrics_hash",
    "verify_report_hash",
    "tamper_report_hash",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingAggregationInput {
    pub schema_version: String,
    pub public_inputs: TrainingAggregationPublicInputs,
    pub private_witness: TrainingAggregationWitness,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingAggregationPublicInputs {
    pub relation: String,
    pub case_id: String,
    pub aggregation_mode: String,
    pub chunk_relation_id: String,
    pub chunk_size: u64,
    pub chunk_count: usize,
    pub step_start: u64,
    pub step_end: u64,
    pub input_checkpoint_hash: String,
    pub output_checkpoint_hash: String,
    pub input_target_checkpoint_hash: String,
    pub output_target_checkpoint_hash: String,
    pub dataset_root: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: String,
    pub raw_trajectory_hash: String,
    pub config_hash: String,
    pub aggregate_root: String,
    pub chunk_public_inputs_root: String,
    pub chunk_proof_root: String,
    pub chunk_verify_report_root: String,
    pub claim_scope: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingAggregationWitness {
    pub chunks: Vec<ChunkRecord>,
    pub child_proofs: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChunkRecord {
    pub chunk_id: usize,
    pub step_start: u64,
    pub step_end: u64,
    pub input_checkpoint_hash: String,
    pub output_checkpoint_hash: String,
    pub input_target_checkpoint_hash: String,
    pub output_target_checkpoint_hash: String,
    pub dataset_root: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: String,
    pub raw_trajectory_hash: String,
    pub config_hash: String,
    pub relation_id: String,
    pub public_inputs_hash: String,
    pub proof_hash: String,
    pub metrics_hash: String,
    pub verify_report_hash: String,
    pub tamper_report_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TrainingAggregationOutput {
    pub schema_version: String,
    pub relation: String,
    pub case_id: String,
    pub aggregation_mode: String,
    pub chunk_relation_id: String,
    pub chunk_size: u64,
    pub chunk_count: usize,
    pub step_start: u64,
    pub step_end: u64,
    pub input_checkpoint_hash: String,
    pub output_checkpoint_hash: String,
    pub input_target_checkpoint_hash: String,
    pub output_target_checkpoint_hash: String,
    pub dataset_root: String,
    pub manifest_hash: String,
    pub audit_report_hash: String,
    pub collection_log_final_hash: String,
    pub raw_trajectory_hash: String,
    pub config_hash: String,
    pub aggregate_root: String,
    pub chunk_public_inputs_root: String,
    pub chunk_proof_root: String,
    pub chunk_verify_report_root: String,
    pub claim_scope: String,
    pub child_proof_verification_inside_guest: bool,
}

#[derive(Debug, Clone)]
struct Roots {
    aggregate_root: String,
    chunk_public_inputs_root: String,
    chunk_proof_root: String,
    chunk_verify_report_root: String,
}

pub fn verify_training_aggregation(input: &TrainingAggregationInput) -> TrainingAggregationOutput {
    let public = &input.public_inputs;
    let witness = &input.private_witness;
    assert_eq!(
        input.schema_version, "sp1_training_aggregation_case_v1",
        "unexpected schema_version"
    );
    assert_eq!(
        public.relation, "training_aggregation",
        "unexpected relation"
    );
    assert_eq!(
        public.aggregation_mode, "proof_manifest_chain",
        "recursive child proof verification is not implemented"
    );
    assert_eq!(
        public.claim_scope, "chunk-chain aggregation over externally verified proof manifests",
        "claim_scope mismatch"
    );
    assert_eq!(
        public.chunk_relation_id, "training_fragment_k8",
        "chunk relation mismatch"
    );
    assert_eq!(public.chunk_size, 8, "chunk_size mismatch");
    assert_eq!(
        public.chunk_count,
        witness.chunks.len(),
        "chunk_count mismatch"
    );
    assert!(!witness.chunks.is_empty(), "at least one chunk is required");
    assert!(
        witness.child_proofs.is_empty(),
        "manifest-chain mode must not claim child proof bytes"
    );
    assert_eq!(
        public.step_end - public.step_start,
        public.chunk_size * witness.chunks.len() as u64,
        "aggregate step span mismatch"
    );
    for (value, label) in [
        (&public.input_checkpoint_hash, "input_checkpoint_hash"),
        (&public.output_checkpoint_hash, "output_checkpoint_hash"),
        (
            &public.input_target_checkpoint_hash,
            "input_target_checkpoint_hash",
        ),
        (
            &public.output_target_checkpoint_hash,
            "output_target_checkpoint_hash",
        ),
        (&public.dataset_root, "dataset_root"),
        (&public.manifest_hash, "manifest_hash"),
        (&public.audit_report_hash, "audit_report_hash"),
        (
            &public.collection_log_final_hash,
            "collection_log_final_hash",
        ),
        (&public.raw_trajectory_hash, "raw_trajectory_hash"),
        (&public.config_hash, "config_hash"),
        (&public.aggregate_root, "aggregate_root"),
        (&public.chunk_public_inputs_root, "chunk_public_inputs_root"),
        (&public.chunk_proof_root, "chunk_proof_root"),
        (&public.chunk_verify_report_root, "chunk_verify_report_root"),
    ] {
        assert_nonzero_hex_32(value, label);
    }

    for (idx, chunk) in witness.chunks.iter().enumerate() {
        assert_eq!(chunk.chunk_id, idx, "chunk order mismatch");
        assert_eq!(
            chunk.step_end - chunk.step_start,
            public.chunk_size,
            "chunk step span mismatch"
        );
        assert_eq!(
            chunk.relation_id, "training_fragment_k8",
            "chunk relation_id mismatch"
        );
        assert_eq!(
            chunk.dataset_root, public.dataset_root,
            "dataset_root mismatch"
        );
        assert_eq!(
            chunk.manifest_hash, public.manifest_hash,
            "manifest_hash mismatch"
        );
        assert_eq!(
            chunk.audit_report_hash, public.audit_report_hash,
            "audit_report_hash mismatch"
        );
        assert_eq!(
            chunk.collection_log_final_hash, public.collection_log_final_hash,
            "collection_log_final_hash mismatch"
        );
        assert_eq!(
            chunk.raw_trajectory_hash, public.raw_trajectory_hash,
            "raw_trajectory_hash mismatch"
        );
        assert_eq!(
            chunk.config_hash, public.config_hash,
            "config_hash mismatch"
        );
        for (value, label) in [
            (&chunk.input_checkpoint_hash, "input_checkpoint_hash"),
            (&chunk.output_checkpoint_hash, "output_checkpoint_hash"),
            (
                &chunk.input_target_checkpoint_hash,
                "input_target_checkpoint_hash",
            ),
            (
                &chunk.output_target_checkpoint_hash,
                "output_target_checkpoint_hash",
            ),
            (&chunk.public_inputs_hash, "public_inputs_hash"),
            (&chunk.proof_hash, "proof_hash"),
            (&chunk.metrics_hash, "metrics_hash"),
            (&chunk.verify_report_hash, "verify_report_hash"),
            (&chunk.tamper_report_hash, "tamper_report_hash"),
        ] {
            assert_nonzero_hex_32(value, label);
        }
        if idx + 1 < witness.chunks.len() {
            let next = &witness.chunks[idx + 1];
            assert_eq!(chunk.step_end, next.step_start, "chunk step link mismatch");
            assert_eq!(
                chunk.output_checkpoint_hash, next.input_checkpoint_hash,
                "checkpoint link mismatch"
            );
            assert_eq!(
                chunk.output_target_checkpoint_hash, next.input_target_checkpoint_hash,
                "target checkpoint link mismatch"
            );
        }
    }

    let first = witness.chunks.first().unwrap();
    let last = witness.chunks.last().unwrap();
    assert_eq!(public.step_start, first.step_start, "step_start mismatch");
    assert_eq!(public.step_end, last.step_end, "step_end mismatch");
    assert_eq!(
        public.input_checkpoint_hash, first.input_checkpoint_hash,
        "input_checkpoint_hash mismatch"
    );
    assert_eq!(
        public.output_checkpoint_hash, last.output_checkpoint_hash,
        "output_checkpoint_hash mismatch"
    );
    assert_eq!(
        public.input_target_checkpoint_hash, first.input_target_checkpoint_hash,
        "input_target_checkpoint_hash mismatch"
    );
    assert_eq!(
        public.output_target_checkpoint_hash, last.output_target_checkpoint_hash,
        "output_target_checkpoint_hash mismatch"
    );

    let roots = recompute_roots(&witness.chunks);
    assert_eq!(
        public.aggregate_root, roots.aggregate_root,
        "aggregate_root mismatch"
    );
    assert_eq!(
        public.chunk_public_inputs_root, roots.chunk_public_inputs_root,
        "chunk_public_inputs_root mismatch"
    );
    assert_eq!(
        public.chunk_proof_root, roots.chunk_proof_root,
        "chunk_proof_root mismatch"
    );
    assert_eq!(
        public.chunk_verify_report_root, roots.chunk_verify_report_root,
        "chunk_verify_report_root mismatch"
    );
    TrainingAggregationOutput {
        schema_version: "sp1_training_aggregation_public_v1".to_owned(),
        relation: public.relation.clone(),
        case_id: public.case_id.clone(),
        aggregation_mode: public.aggregation_mode.clone(),
        chunk_relation_id: public.chunk_relation_id.clone(),
        chunk_size: public.chunk_size,
        chunk_count: public.chunk_count,
        step_start: public.step_start,
        step_end: public.step_end,
        input_checkpoint_hash: public.input_checkpoint_hash.clone(),
        output_checkpoint_hash: public.output_checkpoint_hash.clone(),
        input_target_checkpoint_hash: public.input_target_checkpoint_hash.clone(),
        output_target_checkpoint_hash: public.output_target_checkpoint_hash.clone(),
        dataset_root: public.dataset_root.clone(),
        manifest_hash: public.manifest_hash.clone(),
        audit_report_hash: public.audit_report_hash.clone(),
        collection_log_final_hash: public.collection_log_final_hash.clone(),
        raw_trajectory_hash: public.raw_trajectory_hash.clone(),
        config_hash: public.config_hash.clone(),
        aggregate_root: roots.aggregate_root,
        chunk_public_inputs_root: roots.chunk_public_inputs_root,
        chunk_proof_root: roots.chunk_proof_root,
        chunk_verify_report_root: roots.chunk_verify_report_root,
        claim_scope: public.claim_scope.clone(),
        child_proof_verification_inside_guest: false,
    }
}

fn recompute_roots(chunks: &[ChunkRecord]) -> Roots {
    Roots {
        aggregate_root: hash_rows(
            "training_aggregation_chunk_records_v1",
            chunks.iter().map(chunk_record_row).collect(),
        ),
        chunk_public_inputs_root: hash_rows(
            "training_aggregation_public_inputs_root_v1",
            chunks
                .iter()
                .map(|chunk| chunk.public_inputs_hash.clone())
                .collect(),
        ),
        chunk_proof_root: hash_rows(
            "training_aggregation_proof_root_v1",
            chunks
                .iter()
                .map(|chunk| chunk.proof_hash.clone())
                .collect(),
        ),
        chunk_verify_report_root: hash_rows(
            "training_aggregation_verify_report_root_v1",
            chunks
                .iter()
                .map(|chunk| chunk.verify_report_hash.clone())
                .collect(),
        ),
    }
}

fn chunk_record_row(chunk: &ChunkRecord) -> String {
    let values = [
        chunk.chunk_id.to_string(),
        chunk.step_start.to_string(),
        chunk.step_end.to_string(),
        chunk.input_checkpoint_hash.clone(),
        chunk.output_checkpoint_hash.clone(),
        chunk.input_target_checkpoint_hash.clone(),
        chunk.output_target_checkpoint_hash.clone(),
        chunk.dataset_root.clone(),
        chunk.manifest_hash.clone(),
        chunk.audit_report_hash.clone(),
        chunk.collection_log_final_hash.clone(),
        chunk.raw_trajectory_hash.clone(),
        chunk.config_hash.clone(),
        chunk.relation_id.clone(),
        chunk.public_inputs_hash.clone(),
        chunk.proof_hash.clone(),
        chunk.metrics_hash.clone(),
        chunk.verify_report_hash.clone(),
        chunk.tamper_report_hash.clone(),
    ];
    assert_eq!(
        values.len(),
        CHUNK_FIELDS.len(),
        "chunk field count mismatch"
    );
    values.join("|")
}

fn hash_rows(format_name: &str, rows: Vec<String>) -> String {
    let payload = format!("{}\n{}", format_name, rows.join("\n"));
    hex::encode(Sha256::digest(payload.as_bytes()))
}

fn assert_nonzero_hex_32(value: &str, label: &str) {
    let bytes = hex::decode(value).unwrap_or_else(|_| panic!("{} must be hex", label));
    assert_eq!(bytes.len(), 32, "{} must be a 32-byte hex string", label);
    assert!(
        bytes.iter().any(|item| *item != 0),
        "{} must be nonzero",
        label
    );
}
