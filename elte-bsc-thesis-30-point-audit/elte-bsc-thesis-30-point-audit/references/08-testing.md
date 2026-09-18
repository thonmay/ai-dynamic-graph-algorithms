# Testing

Supervisor guidance checked 2026-09-10 sets a minimum 10-page testing chapter and recommends balanced coverage across UI, core/unit-functional, integration/data/API/end-to-end, and advanced reliability testing. It expects unit, integration, scenario, and regression coverage; explicit datasets and edge/failure cases; and quantitative metrics, baselines, and error analysis for AI topics.

## C6.1 Test plan and cases

Require an explicit strategy, levels/types, environment, tools, scope, priorities, coverage goals, and traceability to requirements, complex features, risks, and exam-topic-relevant algorithms. Every reported test case needs identity, preconditions/data, steps or executable reference, expected result, and oracle.

Inspect the repository to confirm tests exist, are discovered, and target the claimed code. Generated test counts or trivial assertions do not establish meaningful coverage.

## C6.2 Functional, integration, and end-to-end results

Require observed results, dates/revisions/environments, pass/fail status, and evidence for major functions and component boundaries. Cover positive, negative, edge, role/authentication, data/API, and end-to-end scenarios where relevant. Map all proposal commitments and complex features to results.

Re-run safe deterministic tests when feasible. Record skipped/flaky tests, external dependencies, failures, and divergence between reported and reproduced results. Do not silently replace the student's reported test evidence with the auditor's environment.

## C6.3 Non-functional testing and scalability

Require project-relevant evidence for realistic/high-volume behavior, performance/efficiency, scalability, and applicable security/usability/reliability concerns. Define workload, hardware/software environment, dataset, warm-up/repetitions, metrics, baseline, thresholds, variance, and limitations.

Examples include latency/throughput/resource profiling, stress/soak/load, concurrency, large files/data, fuzz/property testing, security validation, accessibility/usability studies, model accuracy and error analysis, or device/network degradation. A screenshot of one fast run is insufficient.

## C6.4 Lessons, changes, and correctness

Require concrete defects or discoveries, their reproduction, root cause, resulting design/implementation change, regression protection, and current status. Analyze output correctness using an appropriate oracle: known answers, invariants, reference implementation, mathematical proof/metric, baseline, human annotation, or domain validation.

“All tests passed” without lessons, correctness reasoning, or limitations does not satisfy this point. The official guide explicitly treats testing-driven changes as positive evidence, not a weakness.

## Evidence integrity

Cross-check narrative counts/tables/screenshots with test files, CI logs, result artifacts, and the fixed code revision. Look for stale screenshots, impossible timestamps, copied framework examples, missing datasets, changed assertions, tests that never execute, and coverage that excludes contribution paths.

Do not fabricate test execution when required accounts, devices, services, datasets, or permissions are unavailable. Mark the evidence unverified and turn the exact gap into a manual reproduction or demo request.

## Evidence output

For each C6 point, cite thesis pages/tables plus test file/case/log/command. Provide a requirement-to-test gap list and prioritize gaps that affect promised complex features, safety, correctness, or realistic scale.
