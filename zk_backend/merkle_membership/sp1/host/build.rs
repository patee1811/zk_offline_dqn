fn main() {
    // The guest ELF hash is the identity Table 2 cites for every proved row, so
    // it must not depend on where the repository happens to sit. The same
    // source built at ~/repo8 and ~/repo11 hashed differently, and the 4992-step
    // proof came back on a guest its ten siblings did not share -- with no
    // source change between the builds.
    //
    // Exactly one absolute path reaches the binary: `strings` on the ELF finds
    // the repository root once and nothing else that varies. Remapping it is
    // enough; the cargo registry paths are identical across builds.
    //
    // The flag goes through BuildArgs rather than the environment. sp1_build
    // assembles its own flag list and sets CARGO_ENCODED_RUSTFLAGS for the
    // guest, so a flag exported here is overwritten and silently lost -- the
    // same shape of trap as a [profile.release] in a workspace member.
    let manifest = std::path::PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let repo_root = manifest
        .ancestors()
        .nth(4)
        .expect("host crate sits four levels below the repository root");

    sp1_build::build_program_with_args(
        "../guest",
        sp1_build::BuildArgs {
            rustflags: vec![format!(
                "--remap-path-prefix={}=/zk_offline_dqn",
                repo_root.display()
            )],
            ..Default::default()
        },
    );
}
