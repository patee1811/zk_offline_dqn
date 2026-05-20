#![no_main]

sp1_zkvm::entrypoint!(main);

use forward_td_mlp_shared::verify_forward_td_mlp;
use td_mvp_shared::TdMvpInput;

pub fn main() {
    let input = sp1_zkvm::io::read::<TdMvpInput>();
    let output = verify_forward_td_mlp(&input);
    sp1_zkvm::io::commit(&output);
}

