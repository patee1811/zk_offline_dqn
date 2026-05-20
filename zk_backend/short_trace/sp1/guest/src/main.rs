#![no_main]

sp1_zkvm::entrypoint!(main);

use short_trace_shared::{verify_short_trace, ShortTraceInput};

pub fn main() {
    let input = sp1_zkvm::io::read::<ShortTraceInput>();
    let output = verify_short_trace(&input);
    sp1_zkvm::io::commit(&output);
}

