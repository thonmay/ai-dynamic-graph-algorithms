# Final-exam topic routing

Use this reference only when final-exam topics are part of the audit. Obtain the official registered or proposed topic names and their listed subtopics. The table below is a routing synopsis of Gregory Morse's BSc guidance, verified 10 September 2026; consult the live homepage for the full current wording when online.

## Common rules

- Choose exactly three topics whose natural subject matter genuinely overlaps the project.
- Map every listed subtopic privately to a substantive thesis passage and technical evidence.
- Do not require headings such as Exam Topic 1 or parenthetical checklist labels in the thesis. Coverage should read as normal technical documentation.
- General concepts and rationale belong in Design; concrete language/tool realization belongs in Implementation; empirical validation belongs in Testing.
- If a topic appears in two chapters, each occurrence must add distinct value rather than repeat textbook prose.
- At checkpoint 3, implementation-heavy topics may have a forward coverage plan rather than finished implementation prose. At checkpoint 4, require current code/documentation evidence. At checkpoint 5, require complete coverage of every registered subtopic.

## Topic synopsis

| No. | Topic | Primary location | Thesis-specific evidence expected |
| ---: | --- | --- | --- |
| 1 | Limits and Continuity of Functions | Design, Implementation | Continuous model, formal convergence/stopping criteria, justified tolerances, and matching checks in code. |
| 2 | Differential and Integral Calculus | Design, Implementation | Optimization objective, gradient/Jacobian/Hessian or integration basis, derivation or autodiff rationale, and corresponding implementation. |
| 3 | Numerical Methods | Design, Implementation, Testing | Chosen method and alternatives, error/tolerance budget, convergence logic, analytic/reference validation, and ill-conditioned edge cases. |
| 4 | Number Theory and Graphs | Design, Implementation | Precise graph vertex/edge semantics and justified representation/algorithms, or the actual modular/number-theoretic structure and correctness basis. |
| 5 | Basics of Probability and Statistics | Implementation, Testing | Probabilistic/statistical model, meaningful metrics, distributions or tests, baselines, confidence/significance, and documented computations. |
| 6 | Artificial Intelligence | Design, Implementation | Formal state/search or ML pipeline, algorithm choice, heuristic/model rationale, evaluation method, and clean state/inference implementation. |
| 7 | Algorithmic Patterns | Implementation, Testing | Named collection-processing patterns, visible implementation structure, and edge-case unit tests. |
| 8 | Object-Oriented Modelling | Design, Implementation | At least four relevant UML types: class, sequence, use case, and one of state/activity/component/deployment; diagrams correspond to actual code and flows. |
| 9 | Object-Oriented Design | Design, Implementation | Architecture/pattern rationale and real structural evidence for claimed patterns; aim for at least two patterns from each GoF category when this topic is chosen. |
| 10 | Fundamentals of Programming Languages | Implementation | Compilation/interpretation model, scope/visibility, type system, parameter passing, exceptions, and conscious language idioms used by the project. |
| 11 | Object-Oriented Programming Languages | Implementation | Encapsulation, inheritance versus composition, subtype polymorphism, memory management, and meaningful generics/templates in the primary language. |
| 12 | Formal Languages | Implementation | Actual lexer/parser, grammar, automaton, or regex language; explicit states/rules and mapping from grammar to code. |
| 13 | Theory of Computation | Implementation | Complexity of major algorithms, worst cases, and, where relevant, NP-hardness, approximation/heuristic rationale, reductions, or computability claims. |
| 14 | Basic Algorithms | Implementation, Testing | Algorithm choice, time/space complexity, invariants where implemented, library algorithm identification, benchmarks, and boundary/worst-case tests. |
| 15 | Data Structures and Data Types | Design, Implementation, Testing | Justified structure choice and tradeoffs, documented invariants for custom structures, and invariant/edge-case tests. |
| 16 | Advanced Algorithms | Design, Implementation, Testing | Explicit graph/problem model, justified algorithm and representation, integrated implementation, complexity, and verified edge-case graphs. |
| 17 | Operating Systems | Design, Implementation, Testing | Process/service/deployment model, OS resources and permissions, I/O or scheduling/synchronization use, cleanup, and constrained-resource tests. |
| 18 | Computer Networks | Design, Implementation, Testing | Network architecture, protocols/API formats/authentication, failure handling, and valid/invalid/timeout/authentication tests. |
| 19 | Concurrent Programming | Implementation, Testing | Threads/tasks, shared state and synchronization, lifecycle/deadlock policy, contention/stress tests, and resource release on failure. |
| 20 | Databases - Design and Query | Design, Implementation | Complete ERD and schema/NoSQL equivalent, keys/constraints/normalization rationale, mapping to code, queries/indexes, and ORM or DDL evidence. |
| 21 | Databases - Optimization and Concurrency Control | Implementation, Testing | Isolation/transaction boundaries, indexes and query plans, rollback/recovery/cache policy, performance comparison, and concurrent-write tests. |
| 22 | Functional Programming | Implementation | Meaningful higher-order operations, immutability, composition/pattern matching/laziness where applicable, types, and an explicit imperative-functional boundary. |

## Reject superficial coverage

Fail or warn, according to the current checkpoint, when evidence consists only of:

- definitions copied from a textbook or course notes;
- a library name with no explanation of the underlying concept actually used;
- diagrams that do not match source or workflows;
- pattern/algorithm labels without structural or execution evidence;
- generic paragraphs that could be pasted into an unrelated thesis;
- coverage of the broad topic while registered subtopics remain unmapped.

