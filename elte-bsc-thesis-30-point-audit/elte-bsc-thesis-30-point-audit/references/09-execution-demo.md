# Program execution and manual demo

Criterion 7 is normally resolved by the supervisor's execution demo. Static artifacts can establish a zero but should not establish a positive point unless the supervisor explicitly accepts comparably direct evidence.

## Pre-demo deductions

Set an execution item to `Lost (0)` before running only when the evidence is conclusive. Examples:

- a promised feature has no implementation path, route, command, build target, or required dependency;
- the proposal promises mobile/device/account/service behavior absent from the submitted code;
- the only implementation is a hard-coded mock while the promise requires real behavior;
- tests and thesis explicitly state the required workflow is unimplemented;
- the submitted build cannot contain the claimed component.

Do not turn a local environment/setup failure into a conclusive zero when the code may run in the student's documented environment. Record it as a demo question.

## C7.1 Accuracy

Demonstrate every approved promise, complex feature, major workflow, and material design claim. Include evidence that the demonstrated build is the submitted source revision. A missing promised item loses C7.1 even if the remaining program runs well.

## C7.2 Robustness

Use ethical invalid inputs and failure conditions selected from the threat/risk model: malformed data, wrong roles, expired/missing credentials, unavailable dependencies, duplicate actions, network interruption, invalid files, boundary values, or concurrent actions. Pass requires controlled behavior, useful feedback, and no crash or corruption. The official guide states a crash under ethical testing is unacceptable.

## C7.3 Realistic or large volumes

Use a justified dataset/workload representative of actual use or the documented upper bound. Observe completion, responsiveness, resource behavior, and correctness. Synthetic scale is acceptable when explained and faithful. Tiny toy data cannot prove this point.

## C7.4 User-friendly interface and domain fit

Observe first-use clarity, workflow efficiency, flexibility, aesthetics, feedback, accessibility-relevant behavior, and fit to the intended professional/user context. For CLI/API/headless systems, judge the equivalent developer/operator interface.

## C7.5 Conventions, labels, and help

Inspect labels, wording, spelling, tooltips, navigation/command/API conventions, validation messages, and context-sensitive help where needed. “No GUI” is not an exemption; assess interface conventions appropriate to the product.

## C7.6 Interruptibility, safety, and user traditions

Attempt safe cancellation/interruption of long or consequential work. Verify rollback/atomicity, idempotence or recovery, data protection, progress feedback, and familiar platform/domain conventions. If interruption is genuinely irrelevant, require a reasoned equivalent safety/lifecycle demonstration rather than awarding automatically.

## Tailored demo sheet

Produce one row per action; multiple rows may support one point:

| ID | Setup/data | Supervisor action | Expected result | Evidence to observe | Pass condition | Observation/result |
|---|---|---|---|---|---|---|

Order the sheet to minimize setup switching:

1. identify build, commit, configuration, accounts/devices, and clean start;
2. run a thin happy path;
3. demonstrate all proposal promises and three complex features;
4. probe integration and data boundaries;
5. use realistic/large data;
6. apply ethical failure and invalid-input cases;
7. inspect usability, conventions, messages, and help;
8. interrupt/recover a long or consequential operation;
9. inspect relevant logs/data/API/device state;
10. record limitations and stop conditions.

Include fallback evidence for external outages, but do not let a recording conceal that submitted code differs. State which points remain unresolved if a required service/device is unavailable.

## Finalization from observations

For each C7 item, record observer, date, environment, code revision, exact action, observed result, and decision. Reconcile observations with the thesis and code. A demo can prove behavior; it cannot retroactively supply missing documentation required by C2-C6.
