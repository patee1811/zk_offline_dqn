#![no_main]

sp1_zkvm::entrypoint!(main);

use merkle_membership_shared::{verify_merkle_membership, MerkleMembershipInput};

pub fn main() {
    let input = sp1_zkvm::io::read::<MerkleMembershipInput>();
    let output = verify_merkle_membership(&input);
    sp1_zkvm::io::commit(&output);
}
