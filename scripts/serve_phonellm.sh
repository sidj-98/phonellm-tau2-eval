#!/bin/bash
# vLLM 0.27.1, one RTX PRO 6000 (sm_120). VLLM_USE_FLASHINFER_SAMPLER=0 and --moe-backend triton are needed on that card.
export VLLM_USE_FLASHINFER_SAMPLER=0
exec vllm serve pipecat-ai/phonellm-mini-alpha-2 --served-model-name phonellm-mini-alpha-2 --trust-remote-code \
  --dtype bfloat16 --max-model-len 32768 --gpu-memory-utilization 0.90 --max-num-seqs 128 --enable-prefix-caching \
  --mamba-cache-mode align --moe-backend triton --enable-auto-tool-choice --tool-call-parser qwen3_coder \
  --default-chat-template-kwargs '{"enable_thinking": false}' --override-generation-config '{"temperature":0}' \
  --host 127.0.0.1 --port 8000
