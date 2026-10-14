# 03 — The token ratio and the threshold are calibrated and recorded

**Goal**: [x]
> **Done:** The ratio is calibrated against Opus 5.5, bytes × 3 / 7 as `Read` returns a file; the default threshold is 2000, from R2's goal files; and R1's baseline is recorded, ≈28.4k for its largest plan. `calibrate.py` repeats the measurement.
> **Note:** Neither the `ant` CLI nor the Python `anthropic` SDK is installed here, and the sessions run on a Claude Code login, so `count_tokens` would need a new install and an API credential.
> **Q:** How are the real token counts taken: headless `claude -p --max-turns 1` runs, differencing the input tokens of a prompt with and without each file's text, on the user's login, for well under $1 (A), or the `count_tokens` API, after installing the SDK or `ant` and logging in with an API credential (B)?
> **A:** A: no new install or credential, it measures the model the commands run on, and like `dev/grant-lifetime/` it is a headless harness anyone can repeat after a tokenizer change. The user runs it.
> **Q:** Run `c1` of `dev/memory-check/calibrate.py` (2026-10-14, 20 sessions on `claude-opus-5-5`, the baseline 29,803 tokens both times) found a token is 2.52 bytes raw and 2.34 as `Read` returns a file, over nine plan files, k from 2.06 to 2.74, so bytes / 4 is 42% low. Should the script switch to the as-read ratio, ≈ tokens = bytes × 3 / 7, with the suite's oracle, its boundary fixture and mutant `mc01` following and the threshold set in these tokens (A), or keep bytes / 4 for comparability with `measure-context.sh` and record the factor (B)?
> **A:** A: the threshold is meant to say when a file costs too much context, and an estimate 42% low would pass files nearly twice the intended size. §4.8 asked for the ratio to be calibrated when it is built; `measure-context.sh` is better fixed later than kept wrong in both.
> **Q:** In calibrated tokens, R2's 17 merged goal files run ≈219–1,906, median ≈963, and R1's 8 single-file plans ≈3,579–28,437. Should the default threshold be 2000, about twice R2's median and above every goal that shipped (A), 1500, flagging `feat-master-plan-checks` goals 02–04 (B), or the placeholder 4000 (C)?
> **A:** A: 2000 is §4.8's "well above the median goal file", falls between R2's largest goal file and R1's smallest plan, and fires on no goal that shipped, so a warning means something.

- [x] The bytes / 4 ratio is calibrated once against a real token count, and the result is recorded
  > **Note:** Run `c1` of `dev/memory-check/calibrate.py`: 2.34 bytes a token as `Read` returns a file (2.52 raw), so bytes / 4 was 42% low. The script now estimates bytes × 3 / 7; its header, the suite's oracle and `mc01-bytes-by-4` carry the ratio, and the suite's README records the run. `dev/measure-context.sh` still divides by 4, so its reports are low by the same factor.
- [x] The threshold's default comes from the first R2 goal files, and how it was chosen is recorded with it
  > **Note:** 2000, per the fourth Q&A: about twice the median (≈963) of R2's 17 merged goal files, above the largest (≈1,906) and below every R1 plan (≈3,579 and up). Recorded in the script's usage and the suite's README.
- [x] R1's legacy plans are measured as the first baseline, the largest being `feat-plan-locator` at ≈ 16.6k tokens
  > **Note:** In calibrated tokens `feat-plan-locator` is ≈28,437; ≈16.6k was its bytes / 4. R1's eight plans total ≈76k read whole, and a `/hitl-step` on R2 reads ≈2.2k at most, an index and one goal file. Recorded in the suite's README.
