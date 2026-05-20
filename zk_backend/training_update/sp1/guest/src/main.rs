#![no_main]

sp1_zkvm::entrypoint!(main);

use training_update_shared::{verify_training_update, TrainingUpdateInput};

pub fn main() {
    let input = sp1_zkvm::io::read::<TrainingUpdateInput>();
    let output = verify_training_update(&input);
    sp1_zkvm::io::commit(&output);
}
