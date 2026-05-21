#![no_main]

sp1_zkvm::entrypoint!(main);

use training_aggregation_shared::{verify_training_aggregation, TrainingAggregationInput};

pub fn main() {
    let input = sp1_zkvm::io::read::<TrainingAggregationInput>();
    let output = verify_training_aggregation(&input);
    sp1_zkvm::io::commit(&output);
}
