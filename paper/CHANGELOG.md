# Paper Restructuring Walkthrough

## Current Documentation Sync - 2026-05-02

The manuscript has been synchronized with the current repository state:

- short verified traces are now described as implemented for 2-step, 4-step, and 8-step settings;
- the locked 8-step short-trace benchmark numbers match `docs/current_benchmark_snapshot.md`;
- deterministic contiguous sampling-rule enforcement is described as implemented and tested;
- the negative sampling-rule tamper check is described as a current verifier rejection test;
- the B3 short-trace artifact cleanup is documented: operational Merkle/checkpoint paths are supplied by the runtime/benchmark rather than stored in persistent `notes`;
- export/verify timings are explicitly framed as Python pre-ZK artifact/verifier timings, not cryptographic proving times.

The older notes below are historical restructuring notes. They are not the canonical source for the current technical milestone; use `paper/README.md`, `docs/current_benchmark_snapshot.md`, and `docs/artifact_schema.md` for current status.

## Summary of Changes

The paper `main.tex` and all section files were restructured and enhanced to conform to academic journal standards for computer science / engineering venues.

## Structural Changes

### New Section Ordering (Journal Standard)
1. **Abstract** — added Keywords line
2. **Introduction** — added citations throughout  
3. **Related Work** — **NEW** section with 5 paragraphs
4. **Problem Setup** — added citations, formal Huber loss definition
5. **System Design and Methodology** — **RENAMED** from "Toward ZK...", completely restructured
6. **Experimental Setup** — cleaned, numbered subsections
7. **Results** — cleaned, extracted Discussion
8. **Discussion** — **NEW** section with 3 subsections
9. **Conclusion and Future Work** — expanded with structured future work
10. **References** — **ACTIVATED** (was commented out)
11. **Appendix** — added Fixed-Point Specification and Artifact Schema sections

## Files Modified

| File | Change |
|------|--------|
| `main.tex` | Added packages (natbib, tikz, algorithm), author affiliation/email, new section ordering, activated bibliography |
| `refs.bib` | Added 6 new references (Merkle, Gym, Groth16, PLONK, Q-learning, Huber); fixed Proof-of-Learning entry |
| `abstract.tex` | Added one-step SGD mention, added Keywords line |
| `related_work.tex` | **NEW** — 5 paragraphs covering Deep RL, Offline RL, Verifiable ML, ZK Proofs, Cryptographic Commitments |
| `introduction.tex` | Added ~10 citations, updated contributions list |
| `problem_setup.tex` | Added citations, formal Huber loss formula |
| `zk_direction.tex` | **COMPLETE REWRITE** as System Design section with TikZ figures |
| `experimental_setup.tex` | Removed 3 contentReference artifacts, numbered subsections, added citations |
| `results.tex` | Removed 2 contentReference artifacts, numbered subsections, extracted Discussion |
| `discussion.tex` | **NEW** — Dataset-method analysis, verifiable RL implications, limitations |
| `conclusion.tex` | Added Future Work paragraph with structured list |
| `appendix.tex` | Added Fixed-Point Specification table and Artifact JSON Schema section |

## New Figures Added

1. **Figure 1: System Architecture** (TikZ) — end-to-end pipeline from CartPole through commitment and training to verification
2. **Figure 2: Verification Pipeline** (TikZ) — 7-step one-step update verification flowchart

## Issues Fixed

- ❌ `:contentReference[oaicite:N]{index=N}` artifacts (5 occurrences) — **REMOVED**
- ❌ Duplicate `\section{}` declaration in zk_direction.tex — **FIXED**
- ❌ `\subsection*{}` unnumbered subsections — **CONVERTED** to numbered
- ❌ Commented-out bibliography — **ACTIVATED**
- ❌ Missing citations — **ADDED** 13 `\cite{}` references
- ❌ Missing Related Work section — **CREATED**
- ❌ Missing Discussion section — **CREATED**
- ❌ No keywords — **ADDED**
- ❌ No author affiliation — **ADDED**: Faculty of IT, UET, duypt114@gmail.com

## Compilation

- **0 errors**, **0 warnings**, **0 undefined references**
- Output: 19 pages, 530KB PDF
- Build command: `pdflatex → bibtex → pdflatex → pdflatex`

## References (13 total in refs.bib)

| Key | Paper |
|-----|-------|
| mnih2015dqn | Human-level control through deep RL (Nature 2015) |
| hasselt2016double | Double DQN (AAAI 2016) |
| watkins1992qlearning | Q-Learning (ML 1992) |
| levine2020offline | Offline RL Tutorial (arXiv 2020) |
| fujimoto2019offpolicy | Off-Policy Deep RL without Exploration (ICML 2019) |
| kumar2020cql | Conservative Q-Learning (NeurIPS 2020) |
| jia2021proofoflearning | Proof-of-Learning (IEEE S&P 2021) |
| thalerbook | Proofs, Arguments, and Zero-Knowledge (2022) |
| groth2016zksnark | Pairing-Based Non-interactive Arguments (EUROCRYPT 2016) |
| gabizon2019plonk | PLONK (ePrint 2019) |
| merkle1987 | Digital Signatures via Conventional Encryption (CRYPTO 1987) |
| brockman2016gym | OpenAI Gym (arXiv 2016) |
| huber1964robust | Robust Location Estimation (Ann. Math. Stat. 1964) |
