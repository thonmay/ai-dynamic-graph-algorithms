# Private exam-topic coverage map (8, 19, 17)

Registered order: **8 Object oriented modelling (first choice), 19 Concurrent programming, 17 Operating systems**.
Subtopic text is verbatim from the official list (`finalexam_new_260515.pdf`). Status: C = explained in the thesis and real in the code; P = present but thin; N = no genuine relationship (left honest, not forced). Thesis locations are printed sections/pages of the 150-page build at commit 11efeea or later; code locations were re-read on 2026-10-31.

## 8. Object oriented modelling

| Subtopic | St | Thesis | Code / test |
|---|---|---|---|
| Static model: class diagram | C | 4.2.1, Fig. 4.3 (p. 43) | `orchestrator.py:84-122` (composition root: verifiers, population, provider, event log, control channel), `population.py`, `candidate.py`, `agents/base.py` |
| Static model: object diagram | C | 4.2.1, Fig. 4.2 (p. 42) | `runs/eval1_orchestrator_dynamic_bfs_s1/generation_0008.json`, `config.yaml` |
| Static model: package diagram | C | 5.2, Fig. 5.1 (p. 58) | import statements: `llm_provider.py:25-26`, `agents/examples.py:23-26`, `cli.py:636-717` |
| Static model: component diagram | C | 4.1, Fig. 4.1 (p. 41) | `server.py`, `events.py`, `sandbox.py`, `agents/base.py` |
| Dynamic model: state diagram | C | 4.2.2, Fig. 4.4 (p. 44) | `candidate.py` `_TRANSITIONS`, `Candidate.transition`; `test_population.py` |
| Dynamic model: sequence diagram | C | 4.4, Fig. 4.5 (p. 48) | `orchestrator.py:494-707` (`step_generation`), `reflector.py` |
| Dynamic model: use case diagram | C | 3.2, Fig. 3.1 (p. 33); narratives App. B.9 | `cli.py` commands, `server.py` routes |

Also in the thesis: design patterns table (4.2.4), runtime/deployment-style process figure (Fig. 4.6). Seven UML diagram types in total (supervisor minimum is 4).

## 19. Concurrent programming

| Subtopic | St | Thesis | Code / test |
|---|---|---|---|
| Multithreaded programs | C | 4.5.3, 5.5 (Lst. run-capped), 5.8 | `sandbox.py:289-313` feed/drain threads; `test_stderr_flood_is_truncated` |
| Scheduling, context switch | C | 5.8 (layered scheduling, GIL 5 ms vs `await`, `_THREAD_ENV`) | `verifier.py:51-54,465-490`; `sandbox.py` `_THREAD_ENV` |
| Race condition | C | 4.5.4 races designed out; 4.5.2 | `server.py` (config before reply), `events.py` ack set, `api.ts` resume from seq |
| Synchronization, explicit locks | C | 4.5.2, 5.8 (`flock` x2), Table 5.3 | `workspace.py:244-259`, `agents/api.py:119-149` |
| Reader-writer synchronization | C | 4.5.2 (events.jsonl single writer; control.jsonl several O_APPEND writers) | `events.py:53-118` |
| Blocking operations | C | 4.5, 5.8 (pause loop, `wait FIRST_COMPLETED`) | `orchestrator.py:257-274`; `test_pause_blocks_until_resume` |
| Use of memory (stack and heap) in threads | C | 5.8 (buffers on thread stacks, shared heap `proc/out/err`, join visibility) | `sandbox.py:248-314` |
| Language support for threads, monitor | C | 4.5.2 (polling vs monitor, Hoare), 5.8 (Future condition variable) | `threading`, `concurrent.futures`, `asyncio` |
| Data types for synchronization/communication | C | 5.8 (`Future`, `Task`) | `verifier.py:459`, `server.py:319` |
| Executors | C | 4.3.3, 5.4, 5.8, ADR-04 | `verifier.py:448-490` `ProcessPoolExecutor`; `test_parallel_workers_match_serial_n4` |
| Producer-consumer problem and implementation | C | 4.5.3, 5.5 | `sandbox.py` pipes, `server.py` `_tail`/`_commands` |
| Deadlock | C | 4.5.2 (Coffman, starvation vs deadlock), 4.5.3 (pipe deadlock, circular wait) | `sandbox.py:300-313`; `test_stderr_flood_is_truncated` |

Thin spots to be ready for orally: no contention stress test (two parallel `check` calls); exceptions in threads (feed swallows `BrokenPipeError`, `fut.result()` re-raises worker errors).

## 17. Operating systems

| Subtopic | St | Thesis | Code / test |
|---|---|---|---|
| Classification of OS, role of the CPU | N | - | no genuine relationship |
| Implementation of processes | C | 4.5.1, 4.6.1, 4.6.3, 5.5 | `sandbox.py:81-122,196-199,277-284` |
| Scheduling algorithms | P/C | 5.8 (FCFS dispatch, kernel time-sharing, per-chunk timeout bound) | `verifier.py:465-490` |
| Avoidance of starvation | C | 4.5.2 (strict in-order submission) | `verifier.py:465-472` |
| Concurrency, threads vs processes | C | 4.5.1, 5.8, ADR-04 | `verifier.py`, `sandbox.py` |
| Inter-process communication | C | 4.5.2 (message passing, three channels), Fig. 4.6 | pipes, pool pickling, JSONL files |
| Critical sections, mutual exclusion | C | 4.5.2, 5.8 | `workspace.py` `flock`, `agents/api.py` |
| Peterson's algorithm | N | - | no genuine relationship |
| Semaphores | C (analogy) | 5.8 (sliding window as counting semaphore) | `verifier.py:467,483` |
| Shared memory | C | 4.6.3 (SysV segments, IPC namespace) | `sandbox.py:55-57,198`; `test_shared_memory_does_not_outlive_the_candidate` |
| Message passing | C | 4.5.2 | as IPC |
| Producer-consumer | C | 4.5.3 | as above |
| I/O device scheduling | N | - | no genuine relationship |
| Deadlocks; starvation vs deadlock | C | 4.5.2, 4.5.3 | as above |
| Memory management, virtual memory | C | 4.6.2 (RLIMIT_AS vs resident set) | `sandbox.py:221-245`; `campaign/chunk_memory.log` |
| Paging | C | 4.6.2 (demand paging, limits after NumPy import) | `sandbox.py:339-341` |
| Segmentation, multi-level page tables, TLB, page replacement/LRU | N | - | no genuine relationship (do not cite `lru_cache`) |
| Storage, file systems, services | C | 4.6.1, 4.7, 5.9 (fsync gap) | `checkpoint.py:89-98`, `events.py:75-78` |
| Redundancy | N | - | no genuine relationship |
| (Supervisor rule) OS error codes, resource release | C | 4.6.3 | `sandbox.py:283,292`; `test_sandbox_jail.py:116-126`; `test_sandbox_leaves_no_temp_files` |

N items are textbook topics to prepare for the oral exam independently of the thesis.
