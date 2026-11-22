# Execution record

Revision `4a22f9dba135b40c725cf4f6d59b4c7189e7e485`, recorded 2026-11-22. Platform: Linux x86_64, user
namespaces available, sandbox jail on (`EVOALGO_SANDBOX` unset). Environment
and the exact transitive dependency set: `01_environment.txt`.

Steps 30 to 55 use the offline scripted `mock` provider: a simulation of the
agent calls that exercises the real engine, verifier, sandbox, checkpoints,
control channel and UI server. It does not show autonomous discovery; the
model-driven research evidence is the committed campaign under `campaign/`.

| Step | Command | Exit | Expected | Result |
|---|---|---|---|---|
| 00_install | `pip install -e .[api,ui,dev] ` | 0 | 0 | OK |
| 10_pytest_full | `$WORK/venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=$WORK/pt ` | 0 | 0 | OK |
| 20_selftest_bfs | `$WORK/venv/bin/evoalgo verify --problem dynamic_bfs --n-max 5 ` | 0 | 0 | OK |
| 21_selftest_dfs | `$WORK/venv/bin/evoalgo verify --problem dynamic_dfs --n-max 5 ` | 0 | 0 | OK |
| 22_selftest_lbfs | `$WORK/venv/bin/evoalgo verify --problem dynamic_lbfs --n-max 5 ` | 0 | 0 | OK |
| 23_ui_install | `bash -c cd ui && npm ci --no-audit --no-fund --silent ` | 0 | 0 | OK |
| 24_ui_vitest | `bash -c cd ui && npx vitest run ` | 0 | 0 | OK |
| 25_ui_typecheck | `bash -c cd ui && npx tsc --noEmit -p . ` | 0 | 0 | OK |
| 26_ui_rebuild_identical | `bash -c cd ui && npm run build --silent && cd ..         && git status --porcelain --untra` | 0 | 0 | OK |
| 30_invalid_config | `$WORK/venv/bin/evoalgo start $WORK/invalid.yaml --run-id invalid ` | 1 | 1 | OK |
| 31_missing_credentials | `bash -c env -u EXECREC_MISSING_KEY '$WORK/venv/bin/evoalgo' start '$WORK/nokey.yaml' --run` | 0 | 0 | OK |
| 32_run_bad_reflect_repair | `$WORK/venv/bin/evoalgo start $WORK/repair.yaml --run-id repair ` | 0 | 0 | OK |
| 33_status | `$WORK/venv/bin/evoalgo status $WORK/runs/repair ` | 0 | 0 | OK |
| 34_status_json | `$WORK/venv/bin/evoalgo status --json $WORK/runs/repair ` | 0 | 0 | OK |
| 35_events | `evsel repair candidate_generated candidate_verified candidate_reflected final_graded run_e` | 0 | 0 | OK |
| 36_final_grade_pass | `$WORK/venv/bin/python -c import json, sys; sys.exit(0 if any(e['type'] == 'final_graded' a` | 0 | 0 | OK |
| 37_export | `$WORK/venv/bin/evoalgo export $WORK/runs/repair ` | 0 | 0 | OK |
| 38_candidate_timeout | `$WORK/venv/bin/evoalgo start $WORK/timeout.yaml --run-id timeout ` | 0 | 0 | OK |
| 39_timeout_is_fail | `bash -c '$WORK/venv/bin/python' -c " import json, sys v = [json.loads(l) for l in open('$W` | 0 | 0 | OK |
| 40_pause | `$WORK/venv/bin/evoalgo control $WORK/runs/stopresume pause ` | 0 | 0 | OK |
| 41_stop | `$WORK/venv/bin/evoalgo control $WORK/runs/stopresume stop ` | 0 | 0 | OK |
| 42_stopped_run | `evoalgo start stop.yaml (background, stopped by step 41) ` | 0 | 0 | OK |
| 43_stop_acknowledged | `grep -q user_stop $WORK/runs/stopresume/events.jsonl ` | 0 | 0 | OK |
| 44_status_after_stop | `$WORK/venv/bin/evoalgo status $WORK/runs/stopresume ` | 0 | 0 | OK |
| 45_resume | `$WORK/venv/bin/evoalgo resume $WORK/runs/stopresume ` | 0 | 0 | OK |
| 46_lifecycle_events | `evsel stopresume run_start control_ack paused gen_committed run_end ` | 0 | 0 | OK |
| 50_ui_refuses_without_token | `bash -c test "$(curl -s -o /dev/stderr -w '%{http_code}' 'http://127.0.0.1:37042/api/runs'` | 0 | 0 | OK |
| 51_ui_run_list | `bash -c test "$(curl -s -o /dev/stderr -w '%{http_code}' -H 'Authorization: Bearer <token>` | 0 | 0 | OK |
| 52_ui_run_detail | `bash -c test "$(curl -s -o /dev/stderr -w '%{http_code}' -H 'Authorization: Bearer <token>` | 0 | 0 | OK |
| 53_ui_candidate | `bash -c test "$(curl -s -o /dev/stderr -w '%{http_code}' -H 'Authorization: Bearer <token>` | 0 | 0 | OK |
| 54_ui_stream_and_ended_control | `$WORK/venv/bin/python $WORK/ws.py 37042 <token> ` | 0 | 0 | OK |

Failed steps: 0. Redaction scan: clean.
