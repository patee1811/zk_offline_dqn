fn main() {
    // The guest ELF hash is the identity Table 2 cites for every proved row, so
    // it must not depend on where the repository happens to sit, nor on whose
    // machine built it. Docker mode is what makes the second half true.
    //
    // Measured at two paths of different length on one machine:
    //
    //   plain   3fc8ee12...  340168 bytes   9 strings under /home/<user>
    //   docker  5ef93342...  340144 bytes   0 strings under /home/<user>
    //
    // The hashes already agreed without Docker, so the repository path is not
    // what varies -- an earlier note in this file claimed a single absolute
    // path reaches the binary, and on the current toolchain none does. What
    // remains are nine cargo registry paths, identical between builds on one
    // machine and different on the next. Docker replaces them with
    // /root/.sp1/... inside the container, which is the same everywhere.
    //
    // Cost: the first build pulls the image, about seven minutes; later builds
    // add sixteen seconds. Docker runs as root, so target/elf-compilation ends
    // up root-owned and a later non-Docker build cannot write there.
    //
    // The flags go through BuildArgs rather than the environment. sp1_build
    // assembles its own flag list and sets CARGO_ENCODED_RUSTFLAGS for the
    // guest, so a flag exported here is overwritten and silently lost -- the
    // same shape of trap as a [profile.release] in a workspace member.
    let manifest = std::path::PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let repo_root = manifest
        .ancestors()
        .nth(4)
        .expect("host crate sits four levels below the repository root");
    // Docker mounts one directory, and three relations reach outside their own
    // workspace for a shared crate: forward_td_mlp and one_step_sgd_tiny depend
    // on td_mvp's, and training_aggregation's shared crate depends on
    // training_fragment's. Mounting the workspace root alone makes cargo fail to
    // read those manifests. zk_backend is the nearest ancestor that covers them.
    let backend_root = manifest
        .ancestors()
        .nth(3)
        .expect("host crate sits three levels below zk_backend");

    sp1_build::build_program_with_args(
        "../guest",
        sp1_build::BuildArgs {
            rustflags: vec![format!(
                "--remap-path-prefix={}=/zk_offline_dqn",
                repo_root.display()
            )],
            docker: true,
            // Pins the compiler. sp1-build defaults this to its own
            // crate version, so relying on the default would let a
            // dependency bump change the guest silently; spelled out,
            // the change is a line in the diff. Matches the `=6.1.0`
            // pin on sp1-build, sp1-sdk and sp1-zkvm.
            tag: "v6.1.0".to_string(),
            workspace_directory: Some(backend_root.display().to_string()),
            ..Default::default()
        },
    );
}
