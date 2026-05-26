#![no_main]

sp1_zkvm::entrypoint!(main);

use one_step_sgd_tiny_shared::verify_one_step_sgd_tiny;
use td_mvp_shared::TdMvpInput;

pub fn main() {
    let input = sp1_zkvm::io::read::<TdMvpInput>();
    let output = verify_one_step_sgd_tiny(&input);
    sp1_zkvm::io::commit(&output);
}

