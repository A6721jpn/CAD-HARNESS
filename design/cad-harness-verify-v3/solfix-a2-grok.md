AGREE

Root cause confirmed on the archived F4-r1 driver. Status is `ok` / `completed`. Fault flags and `injected_sha256` `118f1c94…` match the raw `candidate.py` bytes (9948 bytes, ends `\r\n`). Attempt-1 `source_sha256` is `4b43ad8b…`, and `input-a1.py` is those same bytes (9947). The only extra fixture byte is the final CR. `source_from_final` does `strip()` then adds `\n`, which is what the driver runs after `fault.inject` (`cad_verify_v3_agent.py` 443–446). `sha(source_from_final(fixture))` equals `4b43ad8b…` and the input file. The old checker hashed the raw injection, so `check_fault` raised `fault_source_binding` after a normal driver. Suite row: `stop_reason=harness:report_binding`, error `fault_source_binding`. F5-r1 through F6-r2 were not started.

The diff is that checker only. `fault_source_sha` is `sha(cad_agent.source_from_final(injected).encode("utf-8"))`, the same function and encoding as `agent.digest`. Spec/F6 still uses `compile_spec`. No scoring, gold, threshold, order, rubric, driver, or fixture edit. The test locks the CRLF re-extract and the LF identity.

Call charge matches the archived suite: `inherited_calls` 54, `real_calls` 17, `total_real_calls` 71, row `sol_calls` sum 17 (the prose “real_calls 71” is this total). Prior aborted resume remains 4. Spent 54+4+17=75. Sequences 47–60 `max_calls` sum to 48, so 75+48=123≤163. `resume` still inherits 54.

Re-run plan matches `resume()`: the attempt-#3 `-resume1` dirs are already renamed with `-aborted-fault-binding-20261013T1930` and nothing is deleted, so `entries[46:]` can run again. Those passes stay unscored. Manifest version stays `verify-v3-reviewed-r1-solfix`, with the previous manifest archived as `SHA256.solfix-a1.json`.
