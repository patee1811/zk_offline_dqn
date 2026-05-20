use serde::{Deserialize, Serialize};
use td_mvp_shared::{TdItemOutput, TdMvpInput};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OneStepSgdTinyOutput {
    pub schema_version: String,
    pub relation: String,
    pub dataset_root: String,
    pub fp_scale: i64,
    pub gamma_fp: i64,
    pub learning_rate_fp: i64,
    pub leaf_index: i64,
    pub network_spec_hash: String,
    pub pre_model_commitment: String,
    pub post_model_commitment: String,
    pub target_model_commitment: String,
    pub claimed_batch_loss_fp: i64,
    pub item: TdItemOutput,
}

pub fn verify_one_step_sgd_tiny(input: &TdMvpInput) -> OneStepSgdTinyOutput {
    assert_eq!(
        input.schema_version, "one_step_sgd_tiny_v1",
        "unexpected schema_version"
    );
    let output = td_mvp_shared::verify_td_mvp(input);
    assert_eq!(output.items.len(), 1, "expected one item output");
    OneStepSgdTinyOutput {
        schema_version: "sp1_one_step_sgd_tiny_public_v1".to_owned(),
        relation: "one_step_sgd_tiny".to_owned(),
        dataset_root: input.public.dataset_root.clone(),
        fp_scale: input.public.fp_scale,
        gamma_fp: input.public.gamma_fp,
        learning_rate_fp: input
            .public
            .learning_rate_fp
            .expect("missing learning_rate_fp"),
        leaf_index: input.public.leaf_indices.clone().expect("missing leaf_indices")[0],
        network_spec_hash: input
            .public
            .network_spec_hash
            .clone()
            .expect("missing network_spec_hash"),
        pre_model_commitment: input
            .public
            .pre_model_commitment
            .clone()
            .expect("missing pre_model_commitment"),
        post_model_commitment: input
            .public
            .post_model_commitment
            .clone()
            .expect("missing post_model_commitment"),
        target_model_commitment: input
            .public
            .target_model_commitment
            .clone()
            .expect("missing target_model_commitment"),
        claimed_batch_loss_fp: input
            .public
            .claimed_batch_loss_fp
            .expect("missing claimed_batch_loss_fp"),
        item: output.items[0].clone(),
    }
}
