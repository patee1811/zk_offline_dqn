python scripts/experiments/benchmark_short_trace_update.py `
  --data data/cartpole_dqn_eps010_transitions.pkl `
  --merkle artifacts/cartpole_dqn_eps010_merkle.json `
  --checkpoint models/offline_dqn_with_target_seed42_best.pt `
  --lr 0.001 `
  --target-sync-every 2


python -c "import json; s=json.load(open('artifacts/benchmarks/short_trace_update/summary.json',encoding='utf-8')); p=s[0]['artifact_path']; d=json.load(open(p,encoding='utf-8')); print(list(d['steps'][0].keys()))"