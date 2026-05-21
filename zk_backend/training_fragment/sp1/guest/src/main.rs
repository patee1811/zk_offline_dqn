#![no_main]

sp1_zkvm::entrypoint!(main);

use training_fragment_shared::{verify_training_fragment, TrainingFragmentInput};

pub fn main() {
    let input = sp1_zkvm::io::read::<TrainingFragmentInput>();
    let output = verify_training_fragment(&input);
    sp1_zkvm::io::commit(&output);
}
