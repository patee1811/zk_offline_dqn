// Mirrors .claude/hooks/validate_commit_msg.py (source of truth).
// Optional: npx commitlint --edit. Pre-commit uses the Python checker.

module.exports = {
  extends: ["@commitlint/config-conventional"],
  // Mirrors GIT_GENERATED in validate_commit_msg.py.
  ignores: [(message) => /^(Merge|Revert) /.test(message)],
  rules: {
    "type-enum": [
      2,
      "always",
      [
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "build",
        "ci",
        "chore",
        "revert",
      ],
    ],
    "scope-enum": [
      2,
      "always",
      [
        "relations",
        "verifiers",
        "artifacts",
        "backends",
        "data",
        "cli",
        "experiments",
        "paper",
        "tests",
        "docs",
        "ci",
        "harness",
        "scripts",
        "rl",
        "proof",
        "tamper",
      ],
    ],
    "header-max-length": [2, "always", 72],
    "subject-case": [2, "never", ["pascal-case", "upper-case"]],
    "subject-full-stop": [2, "never", "."],
    "subject-empty": [2, "never"],
    "type-empty": [2, "never"],
  },
};
