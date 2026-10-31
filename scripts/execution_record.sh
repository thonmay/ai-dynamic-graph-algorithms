#!/usr/bin/env bash
# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
#
# Same-revision execution record on the supported platform (Linux with
# unprivileged user namespaces; the sandbox jail stays on).
#
# Clones the given revision into a fresh directory, builds a clean virtual
# environment from the pinned manifest, records the environment, and runs:
#   1. the full pytest suite (fast + slow);
#   2. the verifier self-tests for BFS, DFS and LBFS at n <= 5;
#   3. the UI unit tests, type check and a rebuild of the committed bundle;
#   4. a run lifecycle with the offline scripted "mock" provider (clearly
#      labelled simulation; no model is called): invalid configuration,
#      missing model credentials, a bad-then-good run through generation,
#      reflection, repair, verification and the final grade, a candidate
#      timeout, pause/stop/resume, and the UI server (token refusal, run
#      list, run detail, candidate, event stream, control on an ended run).
#
# Output: one log per step plus summary.md under OUT (must be new or empty).
# Host and domain names, the user name, and the absolute paths of the clone,
# OUT and the home directory are replaced by placeholders; a final scan
# fails the record if any of them is still present.
#
# Usage: scripts/execution_record.sh REPO_URL_OR_PATH REVISION OUT PYTHON
# Optional: REDACT_PREFIX / REDACT_TOOLS replace a site-specific path prefix
# (workspace root, tool installation root) with a placeholder in the logs.
set -uo pipefail

REPO=${1:?repo}; REV=${2:?revision}; OUT=${3:?output dir}; PY=${4:-python3}
mkdir -p "$OUT"
[[ -z "$(ls -A "$OUT")" ]] || { echo "OUT must be empty: $OUT"; exit 1; }
OUT=$(cd "$OUT" && pwd)
WORK=$(mktemp -d "${TMPDIR:-$OUT}/execrec.XXXXXX") && [[ -d "$WORK" ]] || { echo "mktemp failed"; exit 1; }
SRC="$WORK/src"
export TMPDIR="$WORK/tmp"; mkdir -p "$TMPDIR"
unset EVOALGO_SANDBOX            # never inherit a disabled jail
HOST=$(hostname -s); DOMAIN=$(hostname -d 2>/dev/null); ME=$(whoami)
TOKEN=; UPID=; PID=
trap 'kill $UPID $PID 2>/dev/null; rm -rf "$WORK"' EXIT

redact() {  # stdin -> stdout with environment-specific strings replaced (longest first)
    sed -e "s#$SRC#\$REPO#g" -e "s#$WORK#\$WORK#g" -e "s#$OUT#\$OUT#g" \
        ${REDACT_PREFIX:+-e "s#$REDACT_PREFIX#\$PREFIX#g"} \
        ${REDACT_TOOLS:+-e "s#$REDACT_TOOLS#\$TOOLS#g"} \
        -e "s#/afs/[^/ ]*#\$AFS#g" -e "s#$HOME#\$HOME#g" \
        ${DOMAIN:+-e "s#$DOMAIN#\$DOMAIN#g"} -e "s#$HOST#\$HOST#g" -e "s#$ME#\$USER#g" \
        ${TOKEN:+-e "s#$TOKEN#<token>#g"}
}

declare -a STEPS
row() { STEPS+=("| $1 | \`$(echo "$2" | tr '\n' ' ' | redact | sed 's/|/\\|/g' | cut -c1-90)\` | $3 | $4 | $5 |"); }
step() {  # step NAME EXPECTED_RC CMD... ; records command, output and exit code
    local name=$1 want=$2; shift 2
    local log="$OUT/$name.log"
    { echo "\$ $*"; echo; } | redact > "$log"
    ( cd "$SRC" && "$@" ) 2>&1 | redact >> "$log"
    local rc=${PIPESTATUS[0]}
    echo -e "\n[exit code $rc, expected $want]" >> "$log"
    local ok=FAIL; [[ "$rc" == "$want" ]] && ok=OK
    row "$name" "$*" "$rc" "$want" "$ok"
    echo "$name: rc=$rc (expected $want) $ok"
}

git clone -q "$REPO" "$SRC" && git -C "$SRC" checkout -q "$REV" || { echo "clone failed"; exit 1; }
FULL=$(git -C "$SRC" rev-parse HEAD)
"$PY" -m venv "$WORK/venv" || { echo "venv failed"; exit 1; }
VPY="$WORK/venv/bin/python"; EVO="$WORK/venv/bin/evoalgo"
"$VPY" -m pip install --disable-pip-version-check -e "$SRC[api,ui,dev]" 2>&1 | redact > "$OUT/00_install.log"
rc=${PIPESTATUS[0]}; echo "[exit code $rc]" >> "$OUT/00_install.log"
((rc == 0)) || { echo "install failed"; exit 1; }
row 00_install "pip install -e .[api,ui,dev]" "$rc" 0 OK

if unshare --user --map-root-user true 2>/dev/null; then USERNS=available; else USERNS=UNAVAILABLE; fi
{
    echo "revision: $FULL"
    echo "date_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "kernel: $(uname -srm)"
    echo "os: $(. /etc/os-release 2>/dev/null; echo "$PRETTY_NAME")"
    echo "cpu_count: $(nproc)"
    echo "mem_total: $(awk '/MemTotal/{print $2" kB"}' /proc/meminfo)"
    echo "python: $("$VPY" -V 2>&1)"
    echo "node: $(node -v 2>&1)"
    echo "npm: $(npm -v 2>&1)"
    echo "unshare: $(unshare --version 2>&1 | head -1)"
    echo "user_namespaces: $USERNS"
    echo "max_user_namespaces: $(cat /proc/sys/user/max_user_namespaces 2>/dev/null)"
    echo "EVOALGO_SANDBOX: ${EVOALGO_SANDBOX:-unset (jail on)}"
    echo; echo "pip freeze (transitive, exact):"
    "$VPY" -m pip freeze --exclude-editable --disable-pip-version-check
} 2>&1 | redact > "$OUT/01_environment.txt"

# 1. Full test suite and 2. verifier self-tests.
step 10_pytest_full 0 "$VPY" -m pytest -q -p no:cacheprovider --basetemp="$WORK/pt"
step 20_selftest_bfs 0 "$EVO" verify --problem dynamic_bfs --n-max 5
step 21_selftest_dfs 0 "$EVO" verify --problem dynamic_dfs --n-max 5
step 22_selftest_lbfs 0 "$EVO" verify --problem dynamic_lbfs --n-max 5

# 3. UI unit tests and a rebuild of the committed bundle (identity check).
if command -v npm > /dev/null; then
    step 23_ui_install 0 bash -c "cd ui && npm ci --no-audit --no-fund --silent"
    step 24_ui_vitest 0 bash -c "cd ui && npx vitest run"
    step 25_ui_typecheck 0 bash -c "cd ui && npx tsc --noEmit -p ."
    step 26_ui_rebuild_identical 0 bash -c "cd ui && npm run build --silent && cd .. \
        && git status --porcelain --untracked-files=all src/evoalgo/ui_dist \
        && sha256sum src/evoalgo/ui_dist/index.html src/evoalgo/ui_dist/assets/* \
        && test -z \"\$(git status --porcelain --untracked-files=all src/evoalgo/ui_dist)\""
else
    row 23-26_ui "npm not on PATH" - 0 FAIL
fi

# 4. Run lifecycle with the scripted provider (simulation, not discovery).
R="$WORK/runs"; mkdir -p "$R"
cfg() {  # cfg FILE KEY=VALUE... -> YAML config for the mock provider, one value per key
    local f=$1; shift
    declare -A c=([problem]=dynamic_bfs [provider]=mock [workdir]="$R" [population_size]=2
                  [elitism_k]=1 [selection_seed]=1 [timeout_seconds]=5 [final_timeout_seconds]=120)
    local kv; for kv in "$@"; do c[${kv%%=*}]=${kv#*=}; done
    local k; for k in "${!c[@]}"; do echo "$k: ${c[$k]}"; done | sort > "$f"
}
evsel() {  # evsel RUN TYPES... -> one line per matching event
    "$VPY" - "$R/$1/events.jsonl" "${@:2}" <<'PYEOF'
import json, sys
keep = ("id", "gen", "state", "fitness", "timeout", "cmd", "reason", "stop_reason", "generation")
for line in open(sys.argv[1]):
    e = json.loads(line)
    if e["type"] in sys.argv[2:]:
        print(e["type"], {k: e[k] for k in keep if e.get(k) not in (None, "")},
              (e.get("failing_case") or {}).get("operation", ""))
PYEOF
}
cfg "$WORK/invalid.yaml" population_size=0 max_generations=5000
step 30_invalid_config 1 "$EVO" start "$WORK/invalid.yaml" --run-id invalid
cfg "$WORK/nokey.yaml" provider=api model=example-model api_base_url=openai api_key_env=EXECREC_MISSING_KEY max_generations=1
step 31_missing_credentials 0 bash -c "env -u EXECREC_MISSING_KEY '$EVO' start '$WORK/nokey.yaml' --run-id nokey 2>&1 \
    | tee /dev/stderr | grep -q 'API key not found: export EXECREC_MISSING_KEY'"
# bad -> reflection -> repair (good): FAIL then PASS, then the final grade.
cfg "$WORK/repair.yaml" max_generations=4 'mock_script=["bad", "bad", "good", "good"]'
step 32_run_bad_reflect_repair 0 "$EVO" start "$WORK/repair.yaml" --run-id repair
step 33_status 0 "$EVO" status "$R/repair"
step 34_status_json 0 "$EVO" status --json "$R/repair"
step 35_events 0 evsel repair candidate_generated candidate_verified candidate_reflected final_graded run_end
step 36_final_grade_pass 0 "$VPY" -c "import json, sys; sys.exit(0 if any(e['type'] == 'final_graded' and e['state'] == 'PASS' for e in map(json.loads, open('$R/repair/events.jsonl'))) else 1)"
step 37_export 0 "$EVO" export "$R/repair"
# A candidate that never returns: the sandbox timeout maps it to FAIL.
HANG='code:import time\ndef init(graph):\n    time.sleep(60)\n    return {}\ndef insert_edge(graph, edge, state):\n    return state\ndef delete_edge(graph, edge, state):\n    return state\n'
cfg "$WORK/timeout.yaml" max_generations=1 timeout_seconds=2 final_grade=false "mock_script=[\"$HANG\", \"$HANG\"]"
step 38_candidate_timeout 0 "$EVO" start "$WORK/timeout.yaml" --run-id timeout
step 39_timeout_is_fail 0 bash -c "'$VPY' -c \"
import json, sys
v = [json.loads(l) for l in open('$R/timeout/events.jsonl')]
v = [e for e in v if e['type'] == 'candidate_verified']
for e in v: print(e['id'], e['state'], 'timeout=%s' % e['timeout'], e['failing_case'].get('operation'))
sys.exit(0 if v and all(e['state'] == 'FAIL' and e['timeout'] for e in v) else 1)\""
# Pause, stop mid-run, then resume from the last committed generation.
cfg "$WORK/stop.yaml" max_generations=6 early_stop_on_success=false final_grade=false
( cd "$SRC" && exec "$EVO" start "$WORK/stop.yaml" --run-id stopresume > "$WORK/stop.out" 2>&1 ) &
PID=$!
for _ in $(seq 120); do [[ -f "$R/stopresume/COMMITTED" ]] && break; sleep 1; done
step 40_pause 0 "$EVO" control "$R/stopresume" pause
sleep 3
step 41_stop 0 "$EVO" control "$R/stopresume" stop
timeout 300 tail --pid=$PID -f /dev/null; wait $PID; SRC_RC=$?; PID=
redact < "$WORK/stop.out" > "$OUT/42_stopped_run.log"; echo "[exit code $SRC_RC]" >> "$OUT/42_stopped_run.log"
row 42_stopped_run "evoalgo start stop.yaml (background, stopped by step 41)" "$SRC_RC" 0 "$([[ $SRC_RC == 0 ]] && echo OK || echo FAIL)"
step 43_stop_acknowledged 0 grep -q user_stop "$R/stopresume/events.jsonl"
step 44_status_after_stop 0 "$EVO" status "$R/stopresume"
step 45_resume 0 "$EVO" resume "$R/stopresume"
step 46_lifecycle_events 0 evsel stopresume run_start control_ack paused gen_committed run_end
# UI server: token-protected HTTP API and WebSocket stream over the recorded runs.
PORT=$(( 20000 + RANDOM % 20000 )); rm -f "$R/.ui-link"
( cd "$SRC" && exec "$EVO" ui --runs "$R" --port "$PORT" > "$WORK/ui.out" 2>&1 ) &
UPID=$!
for _ in $(seq 40); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && [[ -s "$R/.ui-link" ]] && break; sleep 1; done
TOKEN=$(grep -o "token=[A-Za-z0-9_-]*" "$R/.ui-link" | head -1 | cut -d= -f2)
B="http://127.0.0.1:$PORT/api/runs"
step 50_ui_refuses_without_token 0 bash -c "test \"\$(curl -s -o /dev/stderr -w '%{http_code}' '$B')\" = 401"
step 51_ui_run_list 0 bash -c "test \"\$(curl -s -o /dev/stderr -w '%{http_code}' -H 'Authorization: Bearer $TOKEN' '$B')\" = 200"
step 52_ui_run_detail 0 bash -c "test \"\$(curl -s -o /dev/stderr -w '%{http_code}' -H 'Authorization: Bearer $TOKEN' '$B/repair')\" = 200"
step 53_ui_candidate 0 bash -c "test \"\$(curl -s -o /dev/stderr -w '%{http_code}' -H 'Authorization: Bearer $TOKEN' '$B/repair/candidates/gen001_c01')\" = 200"
cat > "$WORK/ws.py" <<'PYEOF'
import asyncio, json, sys, websockets
async def main(port, tok):
    url = f"ws://127.0.0.1:{port}/api/runs/repair/ws?from=0"
    async with websockets.connect(url, additional_headers={"Authorization": f"Bearer {tok}"}) as ws:
        types = []
        try:
            while True:
                types.append(json.loads(await asyncio.wait_for(ws.recv(), 3)).get("type"))
        except asyncio.TimeoutError:
            pass
        print("replayed events:", len(types), "first:", types[:2], "last:", types[-2:])
        await ws.send(json.dumps({"cmd": "pause"}))
        reply = json.loads(await asyncio.wait_for(ws.recv(), 5))
        print("reply to pause on the ended run:", reply)
    refused = False
    try:
        async with websockets.connect(url) as ws:
            await ws.recv()
    except Exception as e:
        refused = True
        print("stream without token:", type(e).__name__, str(e)[:70])
    ok = "run_end" in types and reply.get("type") == "error" and refused
    sys.exit(0 if ok else 1)
asyncio.run(main(sys.argv[1], sys.argv[2]))
PYEOF
step 54_ui_stream_and_ended_control 0 "$VPY" "$WORK/ws.py" "$PORT" "$TOKEN"
kill $UPID 2>/dev/null; wait $UPID 2>/dev/null; UPID=
redact < "$WORK/ui.out" > "$OUT/55_ui_server.log"

LEAKS=$(grep -rlniE "ericsson|ericai|enlcode|/proj/|/afs/|/app/|$ME|$HOST" "$OUT" 2>/dev/null)
NFAIL=$(printf '%s\n' "${STEPS[@]}" | grep -c "| FAIL |")
{
    echo "# Execution record"
    echo
    echo "Revision \`$FULL\`, recorded $(date -u +%Y-%m-%d). Platform: $(uname -sm), user"
    echo "namespaces $USERNS, sandbox jail on (\`EVOALGO_SANDBOX\` unset). Environment"
    echo "and the exact transitive dependency set: \`01_environment.txt\`."
    echo
    echo "Steps 30 to 55 use the offline scripted \`mock\` provider: a simulation of the"
    echo "agent calls that exercises the real engine, verifier, sandbox, checkpoints,"
    echo "control channel and UI server. It does not show autonomous discovery; the"
    echo "model-driven research evidence is the committed campaign under \`campaign/\`."
    echo
    echo "| Step | Command | Exit | Expected | Result |"
    echo "|---|---|---|---|---|"
    printf '%s\n' "${STEPS[@]}"
    echo
    echo "Failed steps: $NFAIL. Redaction scan: ${LEAKS:-clean}."
} > "$OUT/summary.md"
echo "done: $OUT/summary.md (failed steps: $NFAIL, redaction: ${LEAKS:-clean})"
[[ -z "$LEAKS" && "$NFAIL" == 0 ]]
