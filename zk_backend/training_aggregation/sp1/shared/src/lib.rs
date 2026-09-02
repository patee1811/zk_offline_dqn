use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use sp1_verifier::{Groth16Verifier, PlonkVerifier, GROTH16_VK_BYTES, PLONK_VK_BYTES};
use training_fragment_shared::TrainingFragmentOutput;

const NATIVE_CHILD_PROOF_MODE: &str = "native_sp1";
const GROTH16_CHILD_PROOF_MODE: &str = "groth16_bn254";
const PLONK_CHILD_PROOF_MODE: &str = "plonk_bn254";
const LEAF_CHILD_RELATION_ID: &str = "training_fragment_k8";
const BINARY_NODE_RELATION_ID: &str = "training_aggregation_binary_node";
const BINARY_TOPOLOGY: &str = "binary_tree";

const MANIFEST_CHUNK_FIELDS: [&str; 19] = [
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
    #[serde(default)]
    pub chunk_vkey_root: Option<String>,
    #[serde(default)]
    pub child_proof_mode: Option<String>,
    #[serde(default)]
    pub expected_child_vkey_hash: Option<String>,
    #[serde(default)]
    pub expected_child_vkey_digest_words: Option<Vec<u32>>,
    #[serde(default)]
    pub aggregation_topology: Option<String>,
    #[serde(default)]
    pub node_id: Option<String>,
    #[serde(default)]
    pub node_depth: Option<u64>,
    #[serde(default)]
    pub node_range_start: Option<u64>,
    #[serde(default)]
    pub node_range_end: Option<u64>,
    #[serde(default)]
    pub leaf_chunk_count: Option<usize>,
    #[serde(default)]
    pub child_count: Option<usize>,
    #[serde(default)]
    pub left_child_public_values_hash: Option<String>,
    #[serde(default)]
    pub right_child_public_values_hash: Option<String>,
    #[serde(default)]
    pub left_child_proof_hash: Option<String>,
    #[serde(default)]
    pub right_child_proof_hash: Option<String>,
    #[serde(default)]
    pub left_child_vkey_hash: Option<String>,
    #[serde(default)]
    pub right_child_vkey_hash: Option<String>,
    #[serde(default)]
    pub tree_root_hash: Option<String>,
    pub claim_scope: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrainingAggregationWitness {
    pub chunks: Vec<ChunkRecord>,
    #[serde(default)]
    pub child_proofs: Vec<RecursiveChildProof>,
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
    #[serde(default)]
    pub child_public_inputs_hash: Option<String>,
    #[serde(default)]
    pub child_vkey_hash: Option<String>,
    #[serde(default)]
    pub child_proof_hash: Option<String>,
    #[serde(default)]
    pub child_proof_mode: Option<String>,
    #[serde(default)]
    pub child_verify_report_hash: Option<String>,
    #[serde(default)]
    pub child_tamper_report_hash: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RecursiveChildProof {
    pub chunk_id: usize,
    pub proof_mode: String,
    pub proof_bytes: String,
    pub public_values_bytes: String,
    pub vkey_hash: String,
    #[serde(default)]
    pub vkey_digest_words: Vec<u32>,
    #[serde(default)]
    pub vkey_bytes: String,
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
    #[serde(default)]
    pub chunk_vkey_root: Option<String>,
    #[serde(default)]
    pub child_proof_mode: Option<String>,
    #[serde(default)]
    pub expected_child_vkey_hash: Option<String>,
    #[serde(default)]
    pub expected_child_vkey_digest_words: Option<Vec<u32>>,
    #[serde(default)]
    pub aggregation_topology: Option<String>,
    #[serde(default)]
    pub node_id: Option<String>,
    #[serde(default)]
    pub node_depth: Option<u64>,
    #[serde(default)]
    pub node_range_start: Option<u64>,
    #[serde(default)]
    pub node_range_end: Option<u64>,
    #[serde(default)]
    pub leaf_chunk_count: Option<usize>,
    #[serde(default)]
    pub child_count: Option<usize>,
    #[serde(default)]
    pub left_child_public_values_hash: Option<String>,
    #[serde(default)]
    pub right_child_public_values_hash: Option<String>,
    #[serde(default)]
    pub left_child_proof_hash: Option<String>,
    #[serde(default)]
    pub right_child_proof_hash: Option<String>,
    #[serde(default)]
    pub left_child_vkey_hash: Option<String>,
    #[serde(default)]
    pub right_child_vkey_hash: Option<String>,
    #[serde(default)]
    pub tree_root_hash: Option<String>,
    pub claim_scope: String,
    pub child_proof_verification_inside_guest: bool,
}

#[derive(Debug, Clone)]
struct Roots {
    aggregate_root: String,
    chunk_public_inputs_root: String,
    chunk_proof_root: String,
    chunk_verify_report_root: String,
    chunk_vkey_root: Option<String>,
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
    let binary = public.aggregation_topology.as_deref() == Some(BINARY_TOPOLOGY);
    let first_relation = witness
        .chunks
        .first()
        .map(|chunk| chunk.relation_id.as_str())
        .unwrap_or(LEAF_CHILD_RELATION_ID);
    assert_eq!(
        public.chunk_relation_id,
        if binary {
            first_relation
        } else {
            LEAF_CHILD_RELATION_ID
        },
        "chunk relation mismatch"
    );
    assert_eq!(public.chunk_size, 8, "chunk_size mismatch");
    assert_eq!(
        public.chunk_count,
        witness.chunks.len(),
        "chunk_count mismatch"
    );
    assert!(!witness.chunks.is_empty(), "at least one chunk is required");
    let expected_span = if binary {
        public.leaf_chunk_count.expect("missing leaf_chunk_count") as u64 * public.chunk_size
    } else {
        public.chunk_size * witness.chunks.len() as u64
    };
    assert_eq!(
        public.step_end - public.step_start,
        expected_span,
        "aggregate step span mismatch"
    );
    assert_public_hashes(public);
    if binary {
        verify_binary_public(public, &witness.chunks);
    }
    verify_chunk_chain(public, &witness.chunks, binary);

    let recursive = match public.aggregation_mode.as_str() {
        "proof_manifest_chain" => {
            assert_eq!(
                public.claim_scope,
                "chunk-chain aggregation over externally verified proof manifests",
                "claim_scope mismatch"
            );
            assert!(
                witness.child_proofs.is_empty(),
                "manifest-chain mode must not claim child proof bytes"
            );
            assert!(
                public.chunk_vkey_root.is_none(),
                "unexpected chunk_vkey_root"
            );
            assert!(
                public.child_proof_mode.is_none(),
                "unexpected child_proof_mode"
            );
            assert!(
                public.expected_child_vkey_hash.is_none(),
                "unexpected expected_child_vkey_hash"
            );
            assert!(
                public.expected_child_vkey_digest_words.is_none(),
                "unexpected expected_child_vkey_digest_words"
            );
            false
        }
        "recursive_sp1" => {
            assert_eq!(
                public.claim_scope,
                if binary {
                    "true recursive binary-tree native SP1 aggregation"
                } else {
                    "true recursive SP1 aggregation over child training-fragment proofs"
                },
                "claim_scope mismatch"
            );
            assert_child_proof_mode(
                public
                    .child_proof_mode
                    .as_deref()
                    .expect("missing child_proof_mode"),
            );
            assert_eq!(
                public.chunk_count,
                witness.child_proofs.len(),
                "child proof count mismatch"
            );
            let expected_vkey = public
                .expected_child_vkey_hash
                .as_deref()
                .expect("missing expected child vkey hash");
            assert_vkey_hash(expected_vkey, "expected_child_vkey_hash");
            if public.child_proof_mode.as_deref() == Some(NATIVE_CHILD_PROOF_MODE) {
                let expected_vkey_digest = public
                    .expected_child_vkey_digest_words
                    .as_deref()
                    .expect("missing expected child vkey digest");
                assert_vkey_digest_words(expected_vkey_digest, "expected_child_vkey_digest_words");
            } else {
                assert!(
                    public.expected_child_vkey_digest_words.is_none(),
                    "unexpected expected child vkey digest"
                );
            }
            assert_nonzero_hex_32(
                public
                    .chunk_vkey_root
                    .as_deref()
                    .expect("missing chunk_vkey_root"),
                "chunk_vkey_root",
            );
            verify_recursive_children(public, witness);
            true
        }
        _ => panic!("unsupported aggregation_mode"),
    };

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

    let roots = recompute_roots(&witness.chunks, recursive);
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
    assert_eq!(
        public.chunk_vkey_root, roots.chunk_vkey_root,
        "chunk_vkey_root mismatch"
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
        chunk_vkey_root: roots.chunk_vkey_root,
        child_proof_mode: public.child_proof_mode.clone(),
        expected_child_vkey_hash: public.expected_child_vkey_hash.clone(),
        expected_child_vkey_digest_words: public.expected_child_vkey_digest_words.clone(),
        aggregation_topology: public.aggregation_topology.clone(),
        node_id: public.node_id.clone(),
        node_depth: public.node_depth,
        node_range_start: public.node_range_start,
        node_range_end: public.node_range_end,
        leaf_chunk_count: public.leaf_chunk_count,
        child_count: public.child_count,
        left_child_public_values_hash: public.left_child_public_values_hash.clone(),
        right_child_public_values_hash: public.right_child_public_values_hash.clone(),
        left_child_proof_hash: public.left_child_proof_hash.clone(),
        right_child_proof_hash: public.right_child_proof_hash.clone(),
        left_child_vkey_hash: public.left_child_vkey_hash.clone(),
        right_child_vkey_hash: public.right_child_vkey_hash.clone(),
        tree_root_hash: public.tree_root_hash.clone(),
        claim_scope: public.claim_scope.clone(),
        child_proof_verification_inside_guest: recursive,
    }
}

fn assert_public_hashes(public: &TrainingAggregationPublicInputs) {
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
}

fn verify_binary_public(public: &TrainingAggregationPublicInputs, chunks: &[ChunkRecord]) {
    assert_eq!(
        public.aggregation_mode, "recursive_sp1",
        "binary tree aggregation must be recursive"
    );
    assert_eq!(
        public.child_proof_mode.as_deref(),
        Some(NATIVE_CHILD_PROOF_MODE),
        "binary tree aggregation must use native_sp1"
    );
    assert_eq!(chunks.len(), 2, "binary tree fan-in mismatch");
    assert_eq!(public.chunk_count, 2, "binary chunk_count mismatch");
    assert_eq!(public.child_count, Some(2), "binary child_count mismatch");
    // A node covers every leaf beneath it, so this doubles per level: 2 at depth 1,
    // 4 at depth 2, 16 at depth 4. The old Some(2) | Some(4) match capped the tree
    // at depth 2, which caps a provable training run at 32 steps.
    let leaf_chunk_count = public.leaf_chunk_count.expect("missing leaf_chunk_count");
    assert!(
        leaf_chunk_count >= 2 && leaf_chunk_count & (leaf_chunk_count - 1) == 0,
        "binary leaf_chunk_count must be a power of two >= 2"
    );
    assert!(
        public.node_depth.unwrap_or_default() >= 1,
        "binary node_depth mismatch"
    );
    assert_eq!(
        public.node_range_start,
        Some(public.step_start),
        "binary node_range_start mismatch"
    );
    assert_eq!(
        public.node_range_end,
        Some(public.step_end),
        "binary node_range_end mismatch"
    );
    assert!(
        public
            .node_id
            .as_deref()
            .is_some_and(|node_id| !node_id.is_empty()),
        "binary node_id mismatch"
    );
    let left = &chunks[0];
    let right = &chunks[1];
    for (actual, expected, label) in [
        (
            public.left_child_public_values_hash.as_ref(),
            left.child_public_inputs_hash.as_ref(),
            "left_child_public_values_hash",
        ),
        (
            public.right_child_public_values_hash.as_ref(),
            right.child_public_inputs_hash.as_ref(),
            "right_child_public_values_hash",
        ),
        (
            public.left_child_proof_hash.as_ref(),
            left.child_proof_hash.as_ref(),
            "left_child_proof_hash",
        ),
        (
            public.right_child_proof_hash.as_ref(),
            right.child_proof_hash.as_ref(),
            "right_child_proof_hash",
        ),
        (
            public.left_child_vkey_hash.as_ref(),
            left.child_vkey_hash.as_ref(),
            "left_child_vkey_hash",
        ),
        (
            public.right_child_vkey_hash.as_ref(),
            right.child_vkey_hash.as_ref(),
            "right_child_vkey_hash",
        ),
    ] {
        assert_eq!(actual, expected, "{label} mismatch");
    }
    let tree_root_hash = binary_tree_root(chunks);
    assert_eq!(
        public.tree_root_hash.as_deref(),
        Some(tree_root_hash.as_str()),
        "tree_root_hash mismatch"
    );
}

fn verify_chunk_chain(
    public: &TrainingAggregationPublicInputs,
    chunks: &[ChunkRecord],
    binary: bool,
) {
    for (idx, chunk) in chunks.iter().enumerate() {
        assert_eq!(chunk.chunk_id, idx, "chunk order mismatch");
        let span = chunk.step_end - chunk.step_start;
        if binary {
            assert!(
                span > 0 && span % public.chunk_size == 0,
                "chunk step span mismatch"
            );
            assert_eq!(
                chunk.relation_id, public.chunk_relation_id,
                "chunk relation_id mismatch"
            );
            assert!(
                matches!(
                    chunk.relation_id.as_str(),
                    LEAF_CHILD_RELATION_ID | BINARY_NODE_RELATION_ID
                ),
                "binary child relation_id mismatch"
            );
            if chunk.relation_id == LEAF_CHILD_RELATION_ID {
                assert_eq!(span, public.chunk_size, "leaf chunk step span mismatch");
            }
        } else {
            assert_eq!(span, public.chunk_size, "chunk step span mismatch");
            assert_eq!(
                chunk.relation_id, LEAF_CHILD_RELATION_ID,
                "chunk relation_id mismatch"
            );
        }
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
        if idx + 1 < chunks.len() {
            let next = &chunks[idx + 1];
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
}

fn verify_recursive_children(
    public: &TrainingAggregationPublicInputs,
    witness: &TrainingAggregationWitness,
) {
    let expected_vkey = public.expected_child_vkey_hash.as_ref().unwrap();
    let proof_mode = public.child_proof_mode.as_deref().unwrap();
    for (idx, (chunk, child)) in witness
        .chunks
        .iter()
        .zip(witness.child_proofs.iter())
        .enumerate()
    {
        assert_eq!(child.chunk_id, idx, "child proof order mismatch");
        assert_eq!(
            child.proof_mode, proof_mode,
            "child proof material mode mismatch"
        );
        assert_eq!(
            chunk.child_proof_mode.as_deref(),
            Some(proof_mode),
            "chunk child proof mode mismatch"
        );
        assert_eq!(
            chunk.child_vkey_hash.as_ref(),
            Some(&child.vkey_hash),
            "chunk child vkey hash mismatch"
        );
        assert_eq!(
            &child.vkey_hash, expected_vkey,
            "unexpected child verification key"
        );
        assert_vkey_hash(&child.vkey_hash, "child_vkey_hash");
        if proof_mode == NATIVE_CHILD_PROOF_MODE {
            assert_eq!(
                public.expected_child_vkey_digest_words.as_ref().unwrap(),
                &child.vkey_digest_words,
                "unexpected child verification key digest"
            );
            assert_vkey_digest_words(&child.vkey_digest_words, "child_vkey_digest_words");
            assert!(!child.vkey_bytes.is_empty(), "missing child vkey bytes");
        } else {
            assert!(
                child.vkey_digest_words.is_empty(),
                "unexpected child vkey digest words"
            );
            assert!(child.vkey_bytes.is_empty(), "unexpected child vkey bytes");
        }
        let proof_bytes = decode_hex(&child.proof_bytes, "child proof bytes");
        let public_values = decode_hex(&child.public_values_bytes, "child public values");
        assert_eq!(
            chunk.child_proof_hash.as_deref(),
            Some(sha256_hex(&proof_bytes).as_str()),
            "child proof hash mismatch"
        );
        assert_eq!(
            chunk.child_public_inputs_hash.as_deref(),
            Some(sha256_hex(&public_values).as_str()),
            "child public values hash mismatch"
        );
        assert_eq!(
            chunk.proof_hash,
            chunk.child_proof_hash.as_ref().unwrap().as_str(),
            "recursive proof_hash alias mismatch"
        );
        assert_eq!(
            chunk.public_inputs_hash,
            chunk.child_public_inputs_hash.as_ref().unwrap().as_str(),
            "recursive public_inputs_hash alias mismatch"
        );
        assert_eq!(
            chunk.verify_report_hash,
            chunk.child_verify_report_hash.as_ref().unwrap().as_str(),
            "recursive verify_report_hash alias mismatch"
        );
        assert_eq!(
            chunk.tamper_report_hash,
            chunk.child_tamper_report_hash.as_ref().unwrap().as_str(),
            "recursive tamper_report_hash alias mismatch"
        );
        for (value, label) in [
            (
                chunk.child_public_inputs_hash.as_ref().unwrap(),
                "child_public_inputs_hash",
            ),
            (chunk.child_proof_hash.as_ref().unwrap(), "child_proof_hash"),
            (
                chunk.child_verify_report_hash.as_ref().unwrap(),
                "child_verify_report_hash",
            ),
            (
                chunk.child_tamper_report_hash.as_ref().unwrap(),
                "child_tamper_report_hash",
            ),
        ] {
            assert_nonzero_hex_32(value, label);
        }
        match proof_mode {
            NATIVE_CHILD_PROOF_MODE => verify_native_child_proof(child, &public_values),
            GROTH16_CHILD_PROOF_MODE => Groth16Verifier::verify(
                &proof_bytes,
                &public_values,
                &child.vkey_hash,
                &GROTH16_VK_BYTES,
            )
            .expect("child Groth16 proof verification failed"),
            PLONK_CHILD_PROOF_MODE => PlonkVerifier::verify(
                &proof_bytes,
                &public_values,
                &child.vkey_hash,
                &PLONK_VK_BYTES,
            )
            .expect("child Plonk proof verification failed"),
            _ => panic!("unsupported child proof mode"),
        }
        match chunk.relation_id.as_str() {
            LEAF_CHILD_RELATION_ID => {
                let child_output: TrainingFragmentOutput = bincode::deserialize(&public_values)
                    .expect("child public values decode failed");
                assert_fragment_child_output(public, chunk, &child_output);
            }
            BINARY_NODE_RELATION_ID => {
                let child_output: TrainingAggregationOutput = bincode::deserialize(&public_values)
                    .expect("child public values decode failed");
                assert_aggregation_child_output(public, chunk, &child_output);
            }
            _ => panic!("unsupported recursive child relation"),
        }
    }
}

fn verify_native_child_proof(child: &RecursiveChildProof, public_values: &[u8]) {
    #[cfg(target_os = "zkvm")]
    {
        let digest: [u8; 32] = Sha256::digest(public_values).into();
        let vkey_digest: [u32; 8] = child
            .vkey_digest_words
            .clone()
            .try_into()
            .expect("child vkey digest length mismatch");
        sp1_lib::verify::verify_sp1_proof(&vkey_digest, &digest);
    }

    #[cfg(not(target_os = "zkvm"))]
    {
        let _ = (child, public_values);
    }
}

fn assert_fragment_child_output(
    public: &TrainingAggregationPublicInputs,
    chunk: &ChunkRecord,
    child: &TrainingFragmentOutput,
) {
    assert_eq!(
        child.relation, "training_fragment",
        "child relation mismatch"
    );
    assert_eq!(
        child.num_steps as u64, public.chunk_size,
        "child chunk size mismatch"
    );
    assert_eq!(
        child.global_step_start, chunk.step_start,
        "child step_start mismatch"
    );
    assert_eq!(
        child.global_step_start + child.num_steps as u64,
        chunk.step_end,
        "child step_end mismatch"
    );
    assert_eq!(
        child.start_checkpoint_hash, chunk.input_checkpoint_hash,
        "child input checkpoint mismatch"
    );
    assert_eq!(
        child.final_checkpoint_hash, chunk.output_checkpoint_hash,
        "child output checkpoint mismatch"
    );
    assert_eq!(
        child.start_target_checkpoint_hash, chunk.input_target_checkpoint_hash,
        "child input target checkpoint mismatch"
    );
    assert_eq!(
        child.final_target_checkpoint_hash, chunk.output_target_checkpoint_hash,
        "child output target checkpoint mismatch"
    );
    assert_eq!(
        child.dataset_root, public.dataset_root,
        "child dataset_root mismatch"
    );
    assert_eq!(
        child.manifest_hash, public.manifest_hash,
        "child manifest_hash mismatch"
    );
    assert_eq!(
        child.audit_report_hash, public.audit_report_hash,
        "child audit_report_hash mismatch"
    );
    assert_eq!(
        child.collection_log_final_hash, public.collection_log_final_hash,
        "child collection_log_final_hash mismatch"
    );
    assert_eq!(
        child.raw_trajectory_hash, public.raw_trajectory_hash,
        "child raw_trajectory_hash mismatch"
    );
    assert_eq!(
        child_config_hash(child),
        public.config_hash,
        "child config hash mismatch"
    );
}

fn assert_aggregation_child_output(
    public: &TrainingAggregationPublicInputs,
    chunk: &ChunkRecord,
    child: &TrainingAggregationOutput,
) {
    assert_eq!(
        child.relation, "training_aggregation",
        "child relation mismatch"
    );
    assert_eq!(
        child.aggregation_mode, "recursive_sp1",
        "child aggregation mode mismatch"
    );
    assert_eq!(
        child.aggregation_topology.as_deref(),
        Some(BINARY_TOPOLOGY),
        "child aggregation topology mismatch"
    );
    assert_eq!(
        child.child_proof_mode.as_deref(),
        Some(NATIVE_CHILD_PROOF_MODE),
        "child proof mode mismatch"
    );
    assert!(
        child.child_proof_verification_inside_guest,
        "child aggregation must verify proofs inside guest"
    );
    assert_eq!(
        child.chunk_size, public.chunk_size,
        "child chunk size mismatch"
    );
    assert_eq!(
        child.step_start, chunk.step_start,
        "child step_start mismatch"
    );
    assert_eq!(child.step_end, chunk.step_end, "child step_end mismatch");
    assert_eq!(
        child.input_checkpoint_hash, chunk.input_checkpoint_hash,
        "child input checkpoint mismatch"
    );
    assert_eq!(
        child.output_checkpoint_hash, chunk.output_checkpoint_hash,
        "child output checkpoint mismatch"
    );
    assert_eq!(
        child.input_target_checkpoint_hash, chunk.input_target_checkpoint_hash,
        "child input target checkpoint mismatch"
    );
    assert_eq!(
        child.output_target_checkpoint_hash, chunk.output_target_checkpoint_hash,
        "child output target checkpoint mismatch"
    );
    assert_eq!(
        child.dataset_root, public.dataset_root,
        "child dataset_root mismatch"
    );
    assert_eq!(
        child.manifest_hash, public.manifest_hash,
        "child manifest_hash mismatch"
    );
    assert_eq!(
        child.audit_report_hash, public.audit_report_hash,
        "child audit_report_hash mismatch"
    );
    assert_eq!(
        child.collection_log_final_hash, public.collection_log_final_hash,
        "child collection_log_final_hash mismatch"
    );
    assert_eq!(
        child.raw_trajectory_hash, public.raw_trajectory_hash,
        "child raw_trajectory_hash mismatch"
    );
    assert_eq!(
        child.config_hash, public.config_hash,
        "child config hash mismatch"
    );
}

fn recompute_roots(chunks: &[ChunkRecord], recursive: bool) -> Roots {
    if recursive {
        Roots {
            aggregate_root: hash_rows(
                "training_aggregation_recursive_chunk_records_v1",
                chunks.iter().map(recursive_chunk_record_row).collect(),
            ),
            chunk_public_inputs_root: hash_rows(
                "training_aggregation_recursive_public_inputs_root_v1",
                chunks
                    .iter()
                    .map(|chunk| chunk.child_public_inputs_hash.clone().unwrap())
                    .collect(),
            ),
            chunk_proof_root: hash_rows(
                "training_aggregation_recursive_proof_root_v1",
                chunks
                    .iter()
                    .map(|chunk| chunk.child_proof_hash.clone().unwrap())
                    .collect(),
            ),
            chunk_verify_report_root: hash_rows(
                "training_aggregation_recursive_verify_report_root_v1",
                chunks
                    .iter()
                    .map(|chunk| chunk.child_verify_report_hash.clone().unwrap())
                    .collect(),
            ),
            chunk_vkey_root: Some(hash_rows(
                "training_aggregation_recursive_vkey_root_v1",
                chunks
                    .iter()
                    .map(|chunk| chunk.child_vkey_hash.clone().unwrap())
                    .collect(),
            )),
        }
    } else {
        Roots {
            aggregate_root: hash_rows(
                "training_aggregation_chunk_records_v1",
                chunks.iter().map(manifest_chunk_record_row).collect(),
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
            chunk_vkey_root: None,
        }
    }
}

fn manifest_chunk_record_row(chunk: &ChunkRecord) -> String {
    let values = base_chunk_values(chunk);
    assert_eq!(
        values.len(),
        MANIFEST_CHUNK_FIELDS.len(),
        "chunk field count mismatch"
    );
    values.join("|")
}

fn recursive_chunk_record_row(chunk: &ChunkRecord) -> String {
    let mut values = base_chunk_values(chunk);
    values.extend([
        chunk.child_public_inputs_hash.clone().unwrap(),
        chunk.child_vkey_hash.clone().unwrap(),
        chunk.child_proof_hash.clone().unwrap(),
        chunk.child_proof_mode.clone().unwrap(),
        chunk.child_verify_report_hash.clone().unwrap(),
        chunk.child_tamper_report_hash.clone().unwrap(),
    ]);
    values.join("|")
}

fn base_chunk_values(chunk: &ChunkRecord) -> Vec<String> {
    vec![
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
    ]
}

fn child_config_hash(child: &TrainingFragmentOutput) -> String {
    let payload = format!(
        "{{\"batch_size\":{},\"chunk_relation_id\":\"training_fragment_k8\",\"dataset_size\":{},\"fixed_point_scale\":{},\"format\":\"training_aggregation_chunk_config_v1\",\"gamma\":{},\"learning_rate\":{},\"sampler_seed\":{},\"sampler_type\":\"{}\",\"target_sync_interval\":{},\"target_sync_mode\":\"{}\"}}",
        child.batch_size,
        child.dataset_size,
        child.fixed_point_scale,
        child.gamma,
        child.learning_rate,
        child.sampler_seed,
        child.sampler_type,
        child.target_sync_interval,
        child.target_sync_mode,
    );
    sha256_hex(payload.as_bytes())
}

fn hash_rows(format_name: &str, rows: Vec<String>) -> String {
    let payload = format!("{}\n{}", format_name, rows.join("\n"));
    sha256_hex(payload.as_bytes())
}

fn binary_tree_root(chunks: &[ChunkRecord]) -> String {
    assert_eq!(chunks.len(), 2, "binary tree root requires two children");
    hash_rows(
        "training_aggregation_binary_tree_node_v1",
        ["left", "right"]
            .iter()
            .zip(chunks.iter())
            .map(|(side, chunk)| {
                [
                    side.to_string(),
                    chunk.relation_id.clone(),
                    chunk.step_start.to_string(),
                    chunk.step_end.to_string(),
                    chunk.child_public_inputs_hash.clone().unwrap(),
                    chunk.child_proof_hash.clone().unwrap(),
                    chunk.child_vkey_hash.clone().unwrap(),
                    chunk.input_checkpoint_hash.clone(),
                    chunk.output_checkpoint_hash.clone(),
                    chunk.input_target_checkpoint_hash.clone(),
                    chunk.output_target_checkpoint_hash.clone(),
                ]
                .join("|")
            })
            .collect(),
    )
}

fn sha256_hex(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn decode_hex(value: &str, label: &str) -> Vec<u8> {
    hex::decode(value).unwrap_or_else(|_| panic!("{label} must be hex"))
}

fn assert_nonzero_hex_32(value: &str, label: &str) {
    let bytes = decode_hex(value, label);
    assert_eq!(bytes.len(), 32, "{} must be a 32-byte hex string", label);
    assert!(
        bytes.iter().any(|item| *item != 0),
        "{} must be nonzero",
        label
    );
}

fn assert_vkey_hash(value: &str, label: &str) {
    assert!(value.starts_with("0x"), "{label} must be 0x-prefixed");
    let bytes = decode_hex(&value[2..], label);
    assert_eq!(bytes.len(), 32, "{label} must be 32 bytes");
    assert!(
        bytes.iter().any(|item| *item != 0),
        "{label} must be nonzero"
    );
}

fn assert_vkey_digest_words(words: &[u32], label: &str) {
    assert_eq!(words.len(), 8, "{label} must have eight words");
    assert!(
        words.iter().any(|item| *item != 0),
        "{label} must be nonzero"
    );
}

fn assert_child_proof_mode(mode: &str) {
    assert!(
        matches!(
            mode,
            NATIVE_CHILD_PROOF_MODE | GROTH16_CHILD_PROOF_MODE | PLONK_CHILD_PROOF_MODE
        ),
        "unsupported child proof mode"
    );
}
