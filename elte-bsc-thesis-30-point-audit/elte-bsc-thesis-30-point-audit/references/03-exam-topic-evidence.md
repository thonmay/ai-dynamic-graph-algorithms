# Exam-topic evidence map

This is a compact operational map of Gregory Morse's published guidance checked on 2026-09-10. Search for and read only the three registered topic headings. Verify the exact topic/subtopic wording against the student's current official final-exam form; the public list can change.

For every topic, require project-specific depth, traceable code or design, and coverage of each registered subtopic. Generic textbook prose is not evidence. Do not tell the student to label thesis sections as exam topics.

## 1 Limits and Continuity of Functions

- Fit: ML, numerical simulation, optimization, scientific computing.
- Design/implementation: formal continuous model, convergence criterion, tolerances, iterative or gradient-based method, and theoretical justification.
- Code/evidence: explicit convergence checks and mathematically explained floating-point tolerances; cite the convergence result used.

## 2 Differential and Integral Calculus

- Fit: gradient methods, backpropagation, physics/signal simulation, optimization.
- Design/implementation: objective, analytical or automatic differentiation approach, formulas, and key update derivation; Jacobian/Hessian where genuinely applicable.
- Code/evidence: map optimization code to the mathematics and explain chain-rule use when relying on autodiff.

## 3 Numerical Methods

- Design: choose and justify the numerical method, accuracy target, and tolerance budget.
- Implementation: solver/interpolation/integration logic with convergence, step size, and error analysis.
- Tests/code: known analytic solutions, convergence rate, ill-conditioned or near-singular cases, and annotated numerical parameters.

## 4 Number Theory and Graphs

- Graph fit: routing, dependencies, knowledge/workflow/game/network graphs. Number-theory fit: cryptography, modular arithmetic, hashes/checksums.
- Design: precise vertex/edge semantics or mathematical structure.
- Implementation/code: appropriate representation and algorithms, justified against alternatives; cite mathematical properties relied upon.

## 5 Basics of Probability and Statistics

- Design: probabilistic/statistical model and mathematically defined metrics.
- Implementation: distributions, parameters, likelihoods, statistical tests, or probabilistic models with rationale.
- Tests/code: baselines, quantified confidence/significance where suitable, and explicit expected-value or sampling logic.

## 6 Artificial Intelligence

- Design: state space, operators, initial/goal state, heuristic, and algorithm choice; for ML, define the training/inference pipeline.
- Implementation: chosen search/planning/game/ML method with a clear student contribution.
- Code/evidence: clean state representation, separated branching/evaluation, and a reasoned heuristic quality or admissibility claim.

## 7 Algorithmic Patterns

- Design: identify the data-processing pipeline and relevant patterns.
- Implementation/code: make summation, counting, maximum search, selection, searching, or enumeration patterns visible and explain their formal analogue.
- Tests: empty, singleton, all-equal, and predicate edge cases for each relevant pattern.

## 8 Object-Oriented Modelling

- Require at least four distinct UML diagram types directly matching the real system. The recommended set is class, sequence, use case, and one of state/activity/component/deployment.
- Cross-check classes, method flows, actors, and relations against code and actual workflows.
- Document and justify implementation deviations; generic/generated diagrams without semantic review do not suffice.

## 9 Object-Oriented Design

- Design: dedicated architecture rationale and claimed GoF patterns with code locations and reasons. The published aspiration is at least two patterns from each creational, structural, and behavioral category; judge relevance and substance, not pattern counting alone.
- Implementation/code: every claimed pattern must be structurally real, not merely named; show interfaces, collaborators, and evolution where relevant.

## 10 Fundamentals of Programming Languages

- Explain the primary language's compilation/interpretation model, scope/visibility, type system, parameter passing, and exception strategy as they affect this project.
- Code/evidence: conscious type use, language idioms, exception hierarchy/handling, and comments for non-obvious semantics.

## 11 Object-Oriented Programming Languages

- Explain class hierarchy, encapsulation, inheritance versus composition, subtype polymorphism, memory management, and generics/templates in the project's actual language.
- Code/evidence: meaningful hierarchy and dynamic dispatch, interfaces/abstract classes, real generic reuse, and justified mixins/multiple inheritance where applicable.

## 12 Formal Languages and Automata

- Design: define the grammar/automaton formally and specify the language; include Chomsky class where relevant.
- Implementation/code: lexer/parser, explicit states/transitions, documented regex language, or parser-generator grammar mapped to code.

## 13 Theory of Computation

- Analyze time and space complexity of major algorithms.
- For NP-hardness, approximations, reductions, decidability, or completeness claims, give formal reasoning and citations.
- Code/evidence: annotate worst cases and show how operational limits are handled.

## 14 Basic Algorithms

- Justify sorting, searching, string-processing, or compression choices and document complexity/invariants.
- Do not treat library algorithms as black boxes when their behavior matters.
- Tests/code: edge and worst-case inputs, comparative benchmarks where claimed, loop invariants/termination for student implementations.

## 15 Data Structures and Data Types

- Design: justify structure choices using access patterns and performance trade-offs.
- Implementation: document non-trivial structures; for custom structures, state invariants.
- Tests/code: verify invariants, collision/balance/order/traversal behavior, or explain library-structure guarantees relied upon.

## 16 Advanced Algorithms

- Fit: graph routing, traversal, dependency, closure, or spanning-tree problems.
- Design: explicit graph model and justified algorithm/representation.
- Implementation/tests: appropriate BFS/DFS/shortest-path/MST/all-pairs method, known-answer graphs, disconnected/cyclic/weight edge cases, and complexity annotations.

## 17 Operating Systems

- Design: processes/services, IPC, memory/storage, permissions, files, ports, and deployment constraints.
- Implementation/code: explicit OS facilities, scheduling or background work, and correct resource acquisition/release.
- Tests: missing/denied/large file cases, cleanup/leaks, and low-resource behavior where feasible.

## 18 Computer Networks

- Design: network architecture, protocols, API contracts, authentication, and session model.
- Implementation/code: communication, status/error handling, timeouts/retries, protocol versions, and security configuration.
- Tests: valid/invalid endpoints, authentication states, and controlled network failures.

## 19 Concurrent Programming

- Document every thread/task, lifecycle, shared state, synchronization primitive, and deadlock-avoidance strategy.
- Code: make ownership and synchronization explicit and avoid unsafe locking conventions.
- Tests: contention/stress, blocking behavior, thread-safe operations, termination, and resource release after exceptions.

## 20 Databases Design and Query Design

- Require a complete ERD and derived relational schema with keys, constraints, cardinalities, and normalization/intentional denormalization; use an equivalent explicit model for NoSQL.
- Implementation/code: DDL or matching ORM entities, non-trivial queries, joins/aggregation, indexes, stored procedures or mapping layer.
- Cross-check every diagram and constraint against the actual schema/migrations.

## 21 Databases Optimization and Concurrency Control

- Design: DBMS choice, isolation level, and transaction model.
- Implementation: indexes, query plans, N+1 avoidance, transaction boundaries, rollback/recovery, and cache invalidation where used.
- Tests/code: before/after performance, concurrent writes, rollback/recovery, and proof that critical indexes/plans are used.

## 22 Functional Programming

- Document higher-order functions, composition, immutability, pattern matching, lazy evaluation, currying, or type classes where genuinely used.
- Code/evidence: a meaningful map/filter/reduce-style pipeline, immutable transformation, and function composition; explain imperative/functional boundaries.

## Placement and coverage rules

- Design-oriented treatment belongs in the design chapter; language-, implementation-, concurrency-, and optimization-centered treatment often belongs primarily in implementation.
- A topic may span design and implementation only when each occurrence adds distinct value.
- Check every registered subtopic privately in the promise matrix. The thesis should read as coherent technical work rather than an exam checklist.
