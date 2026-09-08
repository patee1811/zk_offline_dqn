fn main() {
    // The guest ELF hash is the identity Table 2 cites for every proved row, so
    // it must not depend on where the repository happens to sit. The same
    // source built at ~/repo8 and ~/repo11 produced different hashes, because a
    // path dependency reaching outside the workspace enters the binary as an
    // absolute path; only the two guests with such a dependency drifted.
    //
    // Remapping the repository root makes the hash a property of the source.
    // The root is discovered at build time rather than written down, since it
    // differs on every machine -- host -> sp1 -> <relation> -> zk_backend.
    let manifest = std::path::PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let repo_root = manifest
        .ancestors()
        .nth(4)
        .expect("host crate sits four levels below the repository root");

    // Cargo separates encoded flags with US (0x1f). Building the separator
    // rather than escaping it keeps the byte out of this file, where an editor
    // would render it invisibly.
    let separator = char::from(31u8);
    let mut flags: Vec<String> = std::env::var("CARGO_ENCODED_RUSTFLAGS")
        .ok()
        .filter(|encoded| !encoded.is_empty())
        .map(|encoded| encoded.split(separator).map(str::to_owned).collect())
        .unwrap_or_default();
    flags.push(format!(
        "--remap-path-prefix={}=/zk_offline_dqn",
        repo_root.display()
    ));

    // sp1_build spawns cargo, which prefers the encoded form; setting only
    // RUSTFLAGS would be ignored whenever cargo has already encoded its own.
    std::env::set_var(
        "CARGO_ENCODED_RUSTFLAGS",
        flags.join(&separator.to_string()),
    );
    std::env::remove_var("RUSTFLAGS");

    sp1_build::build_program("../guest");
}
