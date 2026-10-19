#!/usr/bin/env python3
"""Recompute the README tables from the gzipped tau2 results files.

Usage: python3 scripts/metrics.py [results_dir]   (default: results/)

pass^k  = mean over tasks of C(c,k)/C(n,k), c = trials with reward 1, n = trials (4).
invalid = tool messages with error=True / agent tool calls (the definition used in the post;
          it also counts the rare error on a customer-side tool, 1 of ~2000 in the step-1 run).
"""
import glob, gzip, json, os, sys
from math import comb

def load(path):
    with gzip.open(path, "rt") as f:
        return json.load(f)

def metrics(d):
    per = {}
    calls = errs = 0
    for s in d["simulations"]:
        ok = s["reward_info"] is not None and s["reward_info"]["reward"] >= 1 - 1e-6
        per.setdefault(s["task_id"], []).append(ok)
        for m in s["messages"]:
            if m["role"] == "assistant" and m.get("tool_calls"):
                calls += len(m["tool_calls"])
            elif m["role"] == "tool" and m.get("error"):
                errs += 1
    n = d["info"]["num_trials"]
    out = {"tasks": len(per), "trials": n}
    for k in range(1, n + 1):
        out[f"pass^{k}"] = 100 * sum(comb(sum(v), k) / comb(len(v), k) for v in per.values()) / len(per)
    out["invalid"] = 100 * errs / calls if calls else float("nan")
    out["calls"] = calls
    return out

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results")
    for group in sorted(glob.glob(os.path.join(root, "*"))):
        print(f"\n## {os.path.basename(group)}")
        print(f"{'run':34s} {'domain':8s} {'tasks':>5s} {'pass^1':>7s} {'pass^4':>7s} {'invalid%':>9s} {'tool calls':>10s}")
        for p in sorted(glob.glob(os.path.join(group, "*", "results.json.gz"))):
            d = load(p)
            m = metrics(d)
            print(f"{os.path.basename(os.path.dirname(p)):34s} {d['info']['environment_info']['domain_name']:8s} "
                  f"{m['tasks']:5d} {m['pass^1']:7.1f} {m['pass^4']:7.1f} {m['invalid']:9.1f} {m['calls']:10d}")

if __name__ == "__main__":
    main()
