# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Peak memory and time of one final-grade verifier chunk in the sandbox.

Runs the known-good reference of a problem on the last ``chunk_size`` base
graphs of the final-grade universe (n <= 5) in one jailed sandbox call with
all resource limits active, and prints the peak resident set size of the
child processes and the wall time.

Run: .venv/bin/python scripts/chunk_memory.py dynamic_dfs dynamic_bfs
"""
import resource
import sys
import tempfile
import time
from pathlib import Path

from evoalgo.config import RunConfig
from evoalgo.selftest.references import reference_code
from evoalgo.workspace import _verifier


def measure(problem: str, tmp: Path) -> str:
    v = _verifier(problem, RunConfig(), "final", "mixed")
    cases = [{"graph": g.tolist(),
              "sequences": [[{"type": t, "edge": list(e)} for t, e in s] for s in v.get_sequences(n, g)]}
             for n, g in v.test_graphs[-v.chunk_size:]]
    cand = tmp / f"{problem}.py"
    cand.write_text(reference_code(problem))
    before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    t = time.time()
    r = v.sandbox.execute_batch(cand, cases, offline_src=v._offline_src(),
                                root=0 if v.problem.needs_root else None, repeat=20)
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return (f"{problem}: {len(cases)} base graphs at n=5, repeat 20, status {r.status}, "
            f"wall {time.time() - t:.1f} s, peak child RSS {max(peak, before) >> 10} MB")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        for p in sys.argv[1:] or ["dynamic_dfs", "dynamic_bfs"]:
            print(measure(p, Path(d)), flush=True)
