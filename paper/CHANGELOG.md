# Paper Changelog

## Relation-Stack Rewrite

The manuscript has been updated around the achieved artifact results.

- Reframed the paper as a layered relation stack for committed replay
  membership, distinct minibatch TD, model-grounded forward-TD MLP, and tiny
  one-step SGD.
- Added explicit threat model, formal statements, SP1 backend, security
  analysis, limitations, and artifact appendix sections.
- Updated proof metrics from `artifacts/benchmarks/final_ndss/summary.json`:
  TD-1/2/4/8, CartPole forward-TD, MountainCar forward-TD, and CartPole
  one-step SGD tiny.
- Added an automated paper-number consistency check against the benchmark
  aggregate.
- Clarified that the contribution is relation-level proof evidence, not full
  proof-of-training.
