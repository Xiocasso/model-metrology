#!/usr/bin/env bash
# Experiment 03 launcher: finish remaining pilots, then run all 7 models'
# full sweeps IN PARALLEL (one process per model, separate output files —
# concurrent appends to a shared file are unsafe; analysis merges by glob).
# Resumable: re-running skips completed trials.
set -u
cd "$(dirname "$0")/../../.."          # repo root
set -a; . ./.env; set +a
cd instruments/permission_bench

DATA="../../experiments/03-permission-compliance/data"
MODELS="deepseek-v4-flash deepseek-v4-pro glm-47-flash glm-47 qwen-plus minimax-m27 claude-haiku-45"

# 1. remaining pilots (quick smoke; resumable no-ops for already-piloted models)
for m in qwen-plus minimax-m27 claude-haiku-45 glm-47; do
  python -m permission_bench.runner --model "$m" --profiles customer_support \
    --arms C1 C2 C3 C4 --max-tasks 4 --replicates 1 \
    --out "$DATA/pilot_$m.jsonl" > "$DATA/pilot_$m.log" 2>&1
  echo "pilot done: $m"
done

# 2. full sweeps, one process per model, in parallel
pids=""
for m in $MODELS; do
  python -m permission_bench.runner --model "$m" --replicates 3 \
    --out "$DATA/trials_$m.jsonl" > "$DATA/full_$m.log" 2>&1 &
  pids="$pids $!"
  echo "launched full: $m (pid $!)"
done

rc=0
for p in $pids; do
  wait "$p" || rc=1
done
echo "all full runs finished (rc=$rc)"
exit $rc
