# PhoneLLM Mini α2 on τ²-bench: evidence

Raw results, prompts and patches behind our write-up on evaluating `pipecat-ai/phonellm-mini-alpha-2`
on [τ²-bench](https://github.com/sierra-research/tau2-bench) (telecom, retail, airline; 4 trials per task, seed 300).
Served with vLLM in BF16, tool parser `qwen3_coder`, thinking off, temperature 0. On telecom the model kept calling
the *customer's* phone functions (listed in the agent's tech-support manual for reference) as if they were its own tools
and got "Tool not found". A load-time rewrite of the manual (model, tools, tasks and scoring untouched) cut the invalid
share of tool calls from 46.2% to 4.4% and lifted telecom pass^1 from 32.9 to 54.8, measured with a MiniMax customer.
Everything is here to inspect or rerun: per-run `results.json.gz`, the exact agent prompts, the patches, and `scripts/metrics.py`.

**Important:** the telecom patch was only run with the MiniMax strict customer. There is no gpt-5.2-customer run of the patched manual.

## Results

### Standard customer (gpt-5.2), comparable to the leaderboard setup
Unpatched prompts, standard τ²-bench customer (gpt-5.2, reasoning effort low). Qwen3.5-9B ran under the same customer.

| Model | Domain | pass^1 | pass^4 | Invalid tool-call share |
|---|---|---|---|---|
| PhoneLLM Mini α2 BF16 | telecom (114 tasks) | 10.7 | 0.0 | 53.6% |
| PhoneLLM Mini α2 BF16 | retail (114) | 59.0 | 31.6 | 2.7% |
| PhoneLLM Mini α2 BF16 | airline (50) | 29.0 | 10.0 | 2.3% |
| Qwen3.5-9B | telecom | 97.4 | 89.5 | 1.4% |
| Qwen3.5-9B | retail | 77.2 | 55.3 | 2.3% |
| Qwen3.5-9B | airline | 76.0 | 62.0 | 1.2% |

### MiniMax strict customer (not leaderboard-comparable)
Customer = MiniMax m3.1 flash with an added "strict" rule (see `prompts/`). PhoneLLM only.

| Domain | Agent prompt | pass^1 | pass^4 | Invalid tool-call share |
|---|---|---|---|---|
| telecom | original manual | 32.9 | 9.6 | 46.2% |
| telecom | step 1: action list labelled as the customer's | 46.5 | 16.7 | 32.4% |
| telecom | step 2: manual names no customer function | 54.8 | 20.2 | 4.4% |
| retail | original | 59.0 | 34.2 | 5.0% |
| airline | original | 25.5 | 10.0 | 3.6% |

`python3 scripts/metrics.py` recomputes every number above from the gzipped results.

## What the patch does
The tech-support manual embeds a section listing phone actions as function names, and the guides say things like
"guide the user to use `toggle_airplane_mode()`". PhoneLLM read those as its own tools. The patch is applied in memory when
the manual is loaded; nothing on disk in tau2-bench is edited.

- **Step 1** (`patches/telecom_step1_label.py`): rewrites the heading to say these are the customer's functions, not the agent's tools, and tags every listed action `[CUSTOMER'S PHONE ONLY, not your tool]`.
- **Step 2** (`patches/telecom_step2_plain_requests.py`): additionally rewrites every guide line that names a function into a plain request, and turns snake_case action names into words.

Before (original):
> If it is ON, guide the user to use `toggle_airplane_mode()` to turn it OFF.
>
> 2. **toggle_airplane_mode** - Turns Airplane Mode ON or OFF. ...

After (step 2):
> If it is ON, ask the customer to switch Airplane Mode OFF on their phone.
>
> 2. Toggle airplane mode (customer's phone only) - Turns Airplane Mode ON or OFF. ...

The full agent system prompts actually sent (taken from each run's `policy` field) are in `prompts/telecom_manual_{original,step1,step2}.md`;
`diff` them directly. Customer additions: `prompts/customer_addition_telecom_strict.md` (telecom) and
`prompts/customer_addition_retail_airline_strict.md` (retail, airline).

## Layout
- `results/gpt-5.2-customer/<run>/results.json.gz`: gpt-5.2 customer runs (PhoneLLM `phonellm_bf16_modal_telecom`, `phonellm_bf16_retail`, `phonellm_bf16_airline`; Qwen `full52_qwen_*`).
- `results/minimax-strict-customer/<run>/results.json.gz`: MiniMax strict customer runs (PhoneLLM only).
- `patches/`, `prompts/`, `scripts/` as described here.

| Run | Patch wrapper |
|---|---|
| `phonellm_bf16_orig_newcust` | `telecom_baseline_strict_customer.py` |
| `phonellm_bf16_fix_newcust` (step 1) | `telecom_step1_label.py` |
| `phonellm_bf16_words_newcust` (step 2) | `telecom_step2_plain_requests.py` |
| `phonellm_bf16_ret_orig_strict`, `phonellm_bf16_air_orig_strict` | `strict_customer_retail_airline.py` (`NL_JUDGE` set, `AIR_PATCH` unset) |
| gpt-5.2 runs (PhoneLLM, Qwen) | none: stock `tau2 run` |

I checked that applying each telecom wrapper to the original manual reproduces the `policy` string stored in the matching run.
(The step 2 wrapper here is the one used, minus an unrelated airline option that was off in that run.)

## Reproducing
1. tau2-bench at commit `96a3ef92329baf908ffe9dfe188cea34e8701d2a` (version 1.0.1). Our checkout carried one uncommitted change in `llm_utils.py` that adds OpenAI prompt-cache routing hints for the gpt-5.2 customer/judge calls (no effect on outputs); it is not needed to reproduce.
2. Serve the model: `scripts/serve_phonellm.sh` (vLLM 0.27.1, single RTX PRO 6000). The Qwen3.5-9B serve flags were not recorded in the result files (served as `openai/qwen3.5-9b` behind an OpenAI-compatible endpoint).
3. Set env vars (names only): `OPENROUTER_API_KEY` (MiniMax customer), `OPENAI_API_KEY` (gpt-5.2 customer and judge), `HOSTED_VLLM_API_BASE`, `HOSTED_VLLM_API_KEY=EMPTY`, `NL_JUDGE` (MiniMax retail/airline runs).
4. Run, from the tau2-bench checkout, e.g. step 2 telecom:
   `EVAL_REPO=/path/to/this/repo scripts/run_phonellm.sh telecom_step2_plain_requests.py telecom phonellm_bf16_words_newcust`
   Baseline: `telecom_baseline_strict_customer.py`; step 1: `telecom_step1_label.py`; retail/airline: `strict_customer_retail_airline.py` with `NL_JUDGE=openrouter/minimax/minimax-m3.1-flash:free`.
   gpt-5.2 PhoneLLM runs: stock `tau2 run --domain <d> --agent-llm hosted_vllm/phonellm-mini-alpha-2 --agent-llm-args '{"temperature":0.0}' --user-llm gpt-5.2 --user-llm-args '{"temperature":0.0,"reasoning_effort":"low"}' --num-trials 4 --seed 300`.

## Metrics
- **pass^k** = mean over tasks of C(c,k)/C(4,k), where c is the number of the task's 4 trials with reward 1. pass^1 is the mean pass rate; pass^4 requires all four trials to pass.
- **Invalid share** = tool messages with `error` set / agent tool calls. Almost all are "Tool 'x' not found".

## Caveats
- MiniMax-customer scores are not comparable to the public τ²-bench leaderboard, which uses a different customer simulator. The strict rule also changes customer behaviour. Use the gpt-5.2 table for comparisons.
- The telecom patch has no gpt-5.2-customer run, and the Qwen3.5-9B rows used the standard customer and unpatched prompts.
- One run per configuration, no confidence intervals; with 114 tasks (50 for airline) differences of a few points are within noise.
- The patch edits the agent's prompt only for telecom; retail and airline were not patched.

## License
Our code and docs are MIT (see `LICENSE`). τ²-bench is a separate project by Sierra Research with its own license; the result files contain its task data and are included for inspection.
