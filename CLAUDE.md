# zk_offline_dqn

Repo nghiên cứu: kiểm chứng **quan hệ (relation)** Offline-DQN trên artifact đã commit, kèm chứng minh SP1 cho vector canonical. Không phải proof toàn bộ quá trình train DQN. Sai claim trên paper/README thì artifact không còn reviewable.

Người dùng: reviewer paper, contributor Python/Rust SP1. Hỏng: số liệu paper lệch provenance, schema gãy, hoặc claim vượt coverage.

## Câu lệnh

Chạy từ root, `PYTHONPATH=.`. Make target dùng Unix (`mkdir -p`); trên Windows dùng Git Bash/WSL.

| Việc | Lệnh | Thời gian |
| --- | --- | --- |
| Cài | `pip install -r requirements.lock \|\| pip install -r requirements.txt` rồi `pip install -e .` | TODO(human): đo thật |
| Smoke | `python -m compileall zk_offline_dqn scripts tests` (`make smoke`) | ~0.1s (3.10.5) |
| Test | `python -m unittest discover tests` (`make check` còn paper-claims) | ~38s, 237 tests, 21 skipped |
| Test đơn | `python -m unittest tests.unit.test_core_helpers.CoreHelperTests.test_fixed_point_td_helpers_are_deterministic` | ~0.1s |
| Unit/golden/negative/CLI | `make unit` / `make golden` / `make negative` / `make cli-smoke` | TODO(human): đo từng target |
| Regression 15 check | `python scripts/experiments/run_full_regression.py` — cần fixture CI | TODO(human): đo trên máy có fixture |
| Lint/format | **không có sẵn trong repo.** Harness: `ruff` trên file vừa sửa (`ruff.toml`). Không typecheck. | n/a |
| CLI | `python -m zk_offline_dqn.cli.main --help` | ~1.4s |
| Paper | `python scripts/experiments/check_paper_claims.py` | ~0.1s |
| Reviewer nhỏ | `make reproduce-small` (nặng: `RUN_HEAVY_SP1=1` v.v.) | TODO(human): đo thật |

SP1 prove **không** nằm trong regression Python. `RUN_SP1_PROVE=1 cargo run --release -p <host> -- --prove`. CI: Python 3.11, `ubuntu-latest`, `.github/workflows/regression.yml`.

## Bản đồ

| Đường dẫn | Trách nhiệm |
| --- | --- |
| `zk_offline_dqn/relations/` | Oracle thuần: membership, TD, SGD, fragment. **Cấm CLI/IO.** |
| `zk_offline_dqn/verifiers/` | Load JSON + schema, gọi relation |
| `zk_offline_dqn/artifacts/` | Schema version, IO, field roles |
| `zk_offline_dqn/cli/` | `verify` / `benchmark` / `report` |
| `zk_offline_dqn/backends/sp1/` | Fixture/lệnh/metric Python; **không** prove khi import |
| `zk_offline_dqn/core/` | Wrapper merkle/TD — phải khớp module gốc |
| `zk_offline_dqn/{merkle,zk_specs,io_utils}.py` | Logic gốc; đừng nhân bản |
| `zk_backend/<relation>/sp1/` | Workspace Rust host/guest/shared, SP1 6.1.0 |
| `zk_backend/test_vectors/` | Vector canonical đã khóa |
| `scripts/experiments/` | Regression, benchmark, Kaggle, paper reports |
| `scripts/artifacts_export/` | Legacy; giữ vì regression còn gọi |
| `scripts/data/` | Collect → audit → commit → verify |
| `tests/{unit,golden,negative,regression}/` | `unittest` (không phải pytest) |
| `paper/`, `docs/` | Paper vs docs implementation |
| `artifacts/reports/final_ndss/` | Số liệu paper đã commit |
| `artifacts/reports/provenance/sp1/` | Provenance SP1 (không commit `proof.bin`) |
| `artifacts/kaggle*` | **Không commit** (gitignore) |
| `data/`, `artifacts/datasets/` | Generated; gitignore |

Đừng đặt semantics mới vào CLI/scripts; đừng sửa `paper/` để nới claim.

## Bất biến

1. `FP_SCALE=1000`, `GAMMA_FP=990`; nhân cố định `(a * b) // fp_scale` — không `round`.
2. SmoothL1 beta = 1.0 (`SMOOTH_L1_BETA_FP=1000`), khớp `torch.nn.SmoothL1Loss()`.
3. Leaf: `",".join(str(int(x)))` rồi SHA256 hex; node trong: `SHA256(bytes.fromhex(L)+bytes.fromhex(R))`; lá lẻ **duplicate** (kiểu Bitcoin).
4. Chuỗi `schema_version` tương thích ngược trừ khi được duyệt migration.
5. `relations/` không phụ thuộc đường dẫn file hay argparse.
6. Cấm claim: full DQN training, Adam, honest public collection, true recursive aggregation, mọi relation đều có SP1. Theorem 7 = proof-manifest chain, không verify child proof trong SP1. Scanner: `scripts/experiments/check_paper_claims.py`.
7. Report (`generate_paper_reports.py`) **không** chạy lại prove/benchmark nặng.
8. Wrapper `core.merkle` / `core.td_arithmetic` re-export — đổi một bên phải khớp bên kia (`test_active_import_surface`).
9. Fixture regression (pkl, merkle JSON, `.pt`) phải có trước khi `run_full_regression.py`.
10. `Dict[str, Any]` cho JSON artifact là style repo, không phải mùi cần “làm chặt kiểu”.

## Mục lục quy ước

- [00 nguyên tắc](.claude/rules/00-nguyen-tac-coi-loi.md)
- [10 phong cách](.claude/rules/10-phong-cach-code.md)
- [20 comment](.claude/rules/20-comment-va-tai-lieu.md)
- [30 kiểm thử](.claude/rules/30-kiem-thu.md)
- [40 git](.claude/rules/40-git-va-commit.md)
- [50 bảo mật](.claude/rules/50-bao-mat-va-secret.md)
- [60 harness](.claude/rules/60-bao-tri-harness.md)
- Vùng: [relations](.claude/rules/90-domain/relations.md), [verifiers](.claude/rules/90-domain/verifiers.md), [sp1](.claude/rules/90-domain/sp1-backend.md), [data](.claude/rules/90-domain/data-pipeline.md), [paper](.claude/rules/90-domain/paper-claims.md), [schema](.claude/rules/90-domain/artifacts-schema.md), [experiments](.claude/rules/90-domain/experiments.md)

## Hoàn thành

- [ ] Đúng lớp (relation vs verifier vs script)
- [ ] `unittest` liên quan xanh; đụng paper thì `check_paper_claims.py` xanh
- [ ] Không nới claim; không đổi schema/`FP_*` lén
- [ ] Không commit secret, `.env`, `proof.bin`, kaggle outputs, lockfile thừa
- [ ] Conventional Commit; không push `master` trừ khi được yêu cầu tường minh

## Phải hỏi người

Sửa `paper/`, `docs/claim_matrix.md`, schema version, `zk_backend/test_vectors/`, `artifacts/reports/final_ndss/`, hằng `zk_specs.py`, thêm dependency, relation SP1 mới, `RUN_HEAVY_*`, force-push, xóa fixture CI, đổi field public/private.
