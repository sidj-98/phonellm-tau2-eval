#!/bin/bash
# Run PhoneLLM against tau2-bench with one of the patch wrappers in ../patches.
#   usage: scripts/run_phonellm.sh <patch.py> <domain> <save-name> [extra tau2 args]
# Run from the root of a tau2-bench checkout at commit 96a3ef92 (path to this repo in $EVAL_REPO).
# Env (names only, set them yourself):
#   OPENROUTER_API_KEY   for the MiniMax customer (openrouter/minimax/minimax-m3.1-flash:free)
#   HOSTED_VLLM_API_BASE e.g. http://localhost:8000/v1 (the vLLM server below); HOSTED_VLLM_API_KEY=EMPTY
#   NL_JUDGE             (retail/airline MiniMax runs) set to the MiniMax model id so the NL-assertion judge is not OpenAI
set -euo pipefail
PATCH=$1; DOM=$2; SAVE=$3; shift 3
: "${EVAL_REPO:?path to this repo}"; : "${HOSTED_VLLM_API_BASE:?}"; export HOSTED_VLLM_API_KEY=${HOSTED_VLLM_API_KEY:-EMPTY}
uv run python "$EVAL_REPO/patches/$PATCH" run --domain "$DOM" \
  --agent-llm hosted_vllm/phonellm-mini-alpha-2 --agent-llm-args '{"temperature":0.0}' \
  --user-llm "openrouter/minimax/minimax-m3.1-flash:free" --user-llm-args '{"temperature":0.0}' \
  --num-trials 4 --seed 300 --max-concurrency 40 --save-to "$SAVE" --auto-resume --log-level ERROR "$@"
