#![no_main]

sp1_zkvm::entrypoint!(main);

use td_mvp_shared::{verify_td_mvp, TdMvpInput};

pub fn main() {
    let input = sp1_zkvm::io::read::<TdMvpInput>();
    let output = verify_td_mvp(&input);
    sp1_zkvm::io::commit(&output);
}
